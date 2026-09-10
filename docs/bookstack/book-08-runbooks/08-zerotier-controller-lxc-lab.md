# ZeroTier network controller (Proxmox LXC, lab)

Tillfällig **self-hosted ZeroTier controller** i labbet för att testa overlay-VPN innan eventuell produktionssättning (t.ex. Azure). Konfigurationen ligger **på LXC:en** — inte i home-ops Git.

## Syfte och scope

| Lab (nu) | Produktion (senare) |
|----------|---------------------|
| Privat mesh mellan lab-enheter | Företagsnät / remote access |
| VLAN 20, ingen publik exponering krävs | Azure VM + publik UDP 9993 (eller Moon) |
| Snabb teardown när test klart | Samma Docker-layout, annan host |

ZeroTier controller är **lätt** (~256 MB RAM). Kör den **utanför Kubernetes** så VPN-controllern överlever klusterstrul.

## Arkitektur (lab)

```
Klienter (laptop, telefon, annan VM)
  → UDP 9993 → srv-ztnc01 (LXC, VLAN 20)
  → ZeroTier controller + ztncui (webb-UI)
  → godkända medlemmar får overlay-IP (t.ex. 10.147.0.0/16)
```

Parallellt med befintlig **Cloudflare Tunnel** (HTTP-appar) — ZeroTier är **UDP mesh**, inte samma sak.

---

## 1. Placering

| Val | Rekommendation |
|-----|----------------|
| Proxmox-värd | **px-node03** eller **px-node04** (undvik px-node01/02 om CP-belastad) |
| Nätverk | **VLAN 20** (Servers), samma som Talos/TrueNAS |
| Hostname | `srv-ztnc01.lab.engstrom.live` |
| IP | Statisk i `192.168.20.0/24` — välj ledig adress i OPNsense/DHCP |
| Resurser | 1 vCPU, **512 MB** RAM, **8 GB** disk |

---

## 2. Skapa LXC (Proxmox GUI)

**Create CT** med ungefär:

| Inställning | Värde |
|-------------|-------|
| OS | Ubuntu 24.04 template |
| Type | **Privileged** (enklast för `/dev/net/tun` i lab) |
| Features | `nesting=1`, `keyctl=1` (Docker i LXC) |
| Network | `vmbr0`, VLAN tag **20**, statisk IP + gateway |
| DNS | Er interna DNS (samma som övriga servrar) |

### Alternativ: `pct` (CLI)

```bash
# Kör på vald Proxmox-värd — justera VMID, IP, template, bridge
pct create 120 local:vztmpl/ubuntu-24.04-standard_24.04-2_amd64.tar.zst \
  --hostname srv-ztnc01 \
  --memory 512 \
  --cores 1 \
  --rootfs local-lvm:8 \
  --net0 name=eth0,bridge=vmbr0,tag=20,ip=192.168.20.160/24,gw=192.168.20.1 \
  --nameserver 192.168.20.1 \
  --features nesting=1,keyctl=1 \
  --unprivileged 0 \
  --onboot 1 \
  --start 1
```

> Byt `192.168.20.160` till ledig IP. Verifiera gateway/DNS mot er OPNsense-setup.

---

## 3. Förbered LXC

```bash
pct enter 120   # eller SSH till containern

apt update && apt upgrade -y
apt install -y curl ca-certificates gnupg

# Docker (official repo)
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" \
  > /etc/apt/sources.list.d/docker.list
apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

mkdir -p /opt/ztncui/data/{ztncui,zt1,zt-mkworld-conf}
```

---

## 4. Starta controller (ztncui-aio)

All-in-one: **ZeroTier One + controller + ztncui** (webb-UI).

Skapa `/opt/ztncui/docker-compose.yml`:

```yaml
services:
  ztncui:
    image: ghcr.io/kmahyyg/ztncui-aio:latest
    container_name: ztncui
    restart: unless-stopped
    cap_add:
      - NET_ADMIN
    devices:
      - /dev/net/tun:/dev/net/tun
    ports:
      - "9993:9993/udp"   # ZeroTier peer traffic
      - "3443:3443/tcp"   # ztncui HTTPS (UI)
      - "3180:3180/tcp"   # ztncui HTTP (valfritt, stäng i prod)
    volumes:
      - /opt/ztncui/data/ztncui:/opt/key-networks/ztncui/etc
      - /opt/ztncui/data/zt1:/var/lib/zerotier-one
      - /opt/ztncui/data/zt-mkworld-conf:/etc/zt-mkworld
    environment:
      NODE_ENV: production
      # Sätt admin-lösenord vid första start (ztncui) — se upstream README
      MYADDR: srv-ztnc01.lab.engstrom.live
```

```bash
cd /opt/ztncui
docker compose up -d
docker compose logs -f   # vänta tills containern är uppe
```

### Snabb hälsokontroll

```bash
docker ps
ss -ulnp | grep 9993
curl -k -s -o /dev/null -w "%{http_code}\n" https://127.0.0.1:3443/
```

| Check | OK |
|-------|-----|
| Container `ztncui` | `Up` |
| UDP 9993 | LISTEN |
| HTTPS 3443 | svarar (200/302) |

---

## 5. Första konfiguration (ztncui)

1. Öppna **https://192.168.20.160:3443** (eller er valda IP) från VLAN 20 / VPN.
2. Logga in i ztncui (första gången — följ UI för admin-konto).
3. Skapa ett **nytt nätverk** (Network ID, t.ex. `xxxxxxxxxx`).
4. Notera **Network ID** — det ska in i klienternas join.

### Koppla klient

På laptop/telefon/annan server:

```bash
# Linux/macOS — installera ZeroTier One, sedan:
zerotier-cli join <NETWORK_ID>
```

Godkänn noden i ztncui (**Members** → authorize).

Verifiera:

```bash
zerotier-cli listnetworks
zerotier-cli peers
ping <overlay-ip-på-annan-nod>
```

---

## 6. Brandvägg (OPNsense, lab)

För **rent labb internt** räcker oftast att klienter på VLAN 20 når LXC:ens IP.

| Regel | Lab | Produktion (Azure) |
|-------|-----|---------------------|
| UDP 9993 → controller | Inom VLAN 20 / trusted | Internet → publik IP |
| TCP 3443 (UI) | Endast admin-VLAN / management | Begränsa till admin-IP / VPN |

**Gör inte** UI publikt utan TLS + IP-begränsning.

---

## 7. Backup (viktigt inför Azure)

Controller-identitet och nätverksdefinitioner ligger i volymerna. Säkerhetskopiera **innan** teardown eller migrering:

```bash
# På srv-ztnc01
tar czf /root/ztncui-backup-$(date +%F).tar.gz -C /opt/ztncui/data .
```

Kopiera arkivet off-host (TrueNAS, 1Password vault file, etc.).

**Kritiska filer:**

| Sökväg | Innehåll |
|--------|----------|
| `zt1/identity.secret` | Controller-identitet — **hemlig** |
| `zt1/controller.d/` | Nätverksdefinitioner |
| `ztncui/` | UI-konfiguration |

Utan backup måste klienter joina ett **nytt** nätverk (nytt Network ID).

---

## 8. Teardown (lab)

```bash
pct enter 120
cd /opt/ztncui && docker compose down
# Ta backup först om du kan tänka dig återanvända identiteten
pct stop 120 && pct destroy 120   # på Proxmox-värden
```

Ta bort ev. OPNsense-regler och DNS-post för `srv-ztnc01`.

---

## 9. Azure — steg-för-steg (företag / produktion)

Samma **Docker Compose** som i lab, men på en **Linux VM** med publik IP. Azure erbjuder hundratals tjänster — för ZeroTier controller behöver du bara **sex saker** (plus valfritt DNS/backup).

### 9.1 Vad du behöver — och vad du kan ignorera

| Azure-tjänst | Behövs? | Varför |
|--------------|---------|--------|
| **Virtual Machine (Linux)** | ✅ Ja | ZeroTier kräver `/dev/net/tun`, UDP 9993, persistent disk |
| **Virtual Network (VNet)** | ✅ Ja | Alla VM:er måste ligga i ett nätverk |
| **Subnet** | ✅ Ja | Minst ett (t.ex. `snet-zt`) |
| **Network Security Group (NSG)** | ✅ Ja | Brandvägg: UDP 9993 + begränsad admin-åtkomst |
| **Public IP (Static)** | ✅ Ja | Klienter utanför Azure måste nå controllern |
| **Network Interface (NIC)** | ✅ Ja | Skapas automatiskt med VM |
| **Managed Disk** | ✅ Ja | OS-disk + ev. datadisk (ingår med VM) |
| Azure Kubernetes (AKS) | ❌ Nej | Onödigt; UDP/TUN krångligt |
| Container Apps / ACI | ❌ Nej | Dåligt stöd för ZeroTier controller |
| App Service | ❌ Nej | HTTP-plattform, inte UDP VPN |
| Application Gateway / Front Door | ❌ Nej | HTTP(S)-lastbalansering — hjälper inte UDP 9993 |
| Azure Firewall | ⚠️ Ofta nej | Dyrt; NSG räcker för en controller-VM |
| VPN Gateway | ❌ Nej | Det är *Azure VPN*, inte ZeroTier |
| Load Balancer | ❌ Nej | En controller = en VM räcker |
| Private Endpoint | ❌ Nej | Controller ska vara nåbar från internet (UDP) |
| ZeroTier Central (SaaS) | ⚠️ Alternativ | Om ni **inte** vill self-hosta — då slipper ni VM helt |

**Enkel regel:** tänk **"en liten Ubuntu-server med publik IP"** — inte container-plattform.

### 9.2 Arkitektur (minimal)

```
                    Internet
                        │
                        │ UDP 9993 (ZeroTier peers)
                        │ TCP 443 eller 3443 (admin-UI, begränsat)
                        ▼
              ┌─────────────────────┐
              │  Public IP (Static) │
              │  zt.company.se      │  ← valfritt Azure DNS / extern DNS
              └──────────┬──────────┘
                         │
    ┌────────────────────┴────────────────────┐
    │  Resource group: rg-zerotier-prod       │
    │  Region: Sweden Central / West Europe   │
    │                                         │
    │  VNet: vnet-zt (10.50.0.0/24)           │
    │    └── Subnet: snet-zt (10.50.0.0/26)   │
    │          └── NSG: nsg-zt-vm             │
    │                └── VM: vm-zt-controller │
    │                      Ubuntu 24.04       │
    │                      Docker + ztncui    │
    └─────────────────────────────────────────┘
```

ZeroTier-trafik går **direkt till VM:ns publika IP** — inte via Application Gateway.

### 9.3 Resursgrupp och region

1. **Resource group:** `rg-zerotier-prod` (eller `rg-net-zerotier-test` för pilot)
2. **Region:** `Sweden Central` om tillgängligt för er tenant, annars `West Europe`
3. Taggar (rekommenderat):

| Tag | Exempel |
|-----|---------|
| `environment` | `test` / `prod` |
| `service` | `zerotier-controller` |
| `owner` | `it@company.se` |

Alla resurser nedan i **samma resource group** underlättar teardown och kostnadsuppföljning.

### 9.4 Nätverk (VNet + subnet + NSG)

#### Skapa VNet (Portal)

**Create a resource** → **Virtual network**:

| Fält | Värde |
|------|-------|
| Name | `vnet-zt` |
| Address space | `10.50.0.0/24` (valfritt privat — krockar inte med ZeroTier overlay) |
| Subnet name | `snet-zt` |
| Subnet range | `10.50.0.0/26` |

> ZeroTier overlay (t.ex. `10.147.0.0/16`) skapas av controllern — Azure VNet är bara **infrastruktur** för VM:en.

#### Skapa NSG

**Network security group** → `nsg-zt-vm` → koppla till subnet `snet-zt` **eller** till VM NIC.

**Inbound rules (minimum):**

| Priority | Name | Port | Protocol | Source | Action | Syfte |
|----------|------|------|----------|--------|--------|-------|
| 100 | Allow-ZT-UDP | 9993 | UDP | `*` | Allow | ZeroTier peer traffic |
| 110 | Allow-SSH-Admin | 22 | TCP | `DinOfficeIP/32` | Allow | SSH (begränsa!) |
| 120 | Allow-UI-HTTPS | 3443 | TCP | `DinOfficeIP/32` | Allow | ztncui (lab/pilot) |
| 130 | Allow-UI-443 | 443 | TCP | `DinOfficeIP/32` | Allow | Om du sätter reverse proxy |
| 4096 | Deny-All | * | * | * | Deny | Azure default |

**Outbound:** låt default (`AllowInternetOutbound`) — controllern behöver nå ZeroTier root servers och uppdateringar.

> **Produktion:** öppna **inte** 3443 mot `0.0.0.0/0`. Admin-UI via **VPN**, **Bastion**, eller **IP-whitelist**.

#### Azure CLI (alternativ till Portal)

```bash
az group create --name rg-zerotier-prod --location swedencentral

az network vnet create \
  --resource-group rg-zerotier-prod \
  --name vnet-zt \
  --address-prefix 10.50.0.0/24 \
  --subnet-name snet-zt \
  --subnet-prefix 10.50.0.0/26

az network nsg create -g rg-zerotier-prod -n nsg-zt-vm

az network nsg rule create -g rg-zerotier-prod --nsg-name nsg-zt-vm \
  -n Allow-ZT-UDP --priority 100 --direction Inbound \
  --access Allow --protocol Udp --destination-port-range 9993 \
  --source-address-prefixes '*' --destination-address-prefixes '*'

az network nsg rule create -g rg-zerotier-prod --nsg-name nsg-zt-vm \
  -n Allow-SSH-Admin --priority 110 --direction Inbound \
  --access Allow --protocol Tcp --destination-port-range 22 \
  --source-address-prefixes '<DIN_KONTORS_IP>/32'

az network vnet subnet update -g rg-zerotier-prod --vnet-name vnet-zt \
  --name snet-zt --network-security-group nsg-zt-vm
```

### 9.5 Virtual Machine — konkreta val i Portal

**Create a resource** → **Virtual machine**:

| Flik | Inställning | Rekommendation |
|------|-------------|----------------|
| **Basics — Name** | `vm-zt-controller` | |
| **Region** | Samma som VNet | |
| **Image** | Ubuntu Server **24.04 LTS** | Långt stöd, bra Docker-dokumentation |
| **Size** | **Standard_B2s** (2 vCPU, 4 GiB) | Test/pilot; **B2ms** (8 GiB) om ni kör fler tjänster på samma VM |
| **Authentication** | SSH public key | Undvik lösenord-only |
| **Inbound ports** | **None** (eller bara 22 tillfälligt) | NSG styr — duplicera inte regler |
| **Disks — OS disk** | Premium SSD, **32 GiB** | Räcker gott; controller-data är liten |
| **Networking — VNet** | `vnet-zt` / `snet-zt` | |
| **Public IP** | **Create new** → Name: `pip-zt-controller` | |
| **Public IP — Assignment** | **Static** | ⚠️ Viktigt — klienter cache:ar controller endpoint |
| **NSG** | `nsg-zt-vm` | |
| **Management** | Boot diagnostics: On | Felsökning vid boot-problem |

**Vad du INTE behöver kryssa i:**

- Load balancing
- Availability zone (kan läggas till senare för prod)
- Azure Spot (controller ska vara stabil)
- Extensions (utom ev. Azure Monitor Agent senare)

#### VM-storlek — riktlinje

| SKU | vCPU / RAM | Användning |
|-----|------------|------------|
| **Standard_B2s** | 2 / 4 GiB | Pilot, &lt;50 noder, låg kostnad |
| **Standard_B2ms** | 2 / 8 GiB | Prod med marginal, Docker + ev. monitoring |
| Standard_D2s_v5 | 2 / 8 GiB | Om ni vill ha "general purpose" SLA-känsla |

ZeroTier controller är **CPU/RAM-lätt** — nätverk (UDP 9993) och **disk-I/O på identity/config** är viktigare än kärnor.

### 9.6 DNS (valfritt men rekommenderat)

Utan DNS måste klienter hitta controllern via **fast publik IP**. Med DNS kan ni byta VM bakom samma namn vid migrering.

| Alternativ | Hur |
|------------|-----|
| **Azure DNS** | Zone `company.se` → A-record `zt` → `pip-zt-controller` IP |
| Extern DNS (Cloudflare, etc.) | Samma A-record |
| ZeroTier | Klienter använder Network ID — DNS påverkar inte overlay direkt, men underlättar **admin-UI** |

```bash
az network dns zone create -g rg-zerotier-prod -n company.se   # om zonen hostas i Azure
az network dns record-set a add-record -g rg-zerotier-prod -z company.se -n zt -a <PUBLIC_IP>
```

### 9.7 Konfigurera VM (samma som lab)

SSH till VM:

```bash
ssh azureuser@<PUBLIC_IP>
```

Installera Docker (samma steg som [§3 Förbered LXC](#3-förbered-lxc)):

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl ca-certificates gnupg
# … Docker install enligt lab-runbook …
sudo mkdir -p /opt/ztncui/data/{ztncui,zt1,zt-mkworld-conf}
```

Kopiera `/opt/ztncui/docker-compose.yml` från lab (§4) — justera ev. `MYADDR` till `zt.company.se`.

```bash
cd /opt/ztncui
sudo docker compose up -d
sudo ss -ulnp | grep 9993
curl -k -s -o /dev/null -w "%{http_code}\n" https://127.0.0.1:3443/
```

### 9.8 Migrering lab → Azure

1. **Lab:** `docker compose down` på srv-ztnc01
2. **Backup:** `tar czf ztncui-backup.tar.gz -C /opt/ztncui/data .`
3. **Överför** till Azure (scp, `az storage` — **kryptera filen**, innehåller `identity.secret`):

   ```bash
   scp ztncui-backup.tar.gz azureuser@<PUBLIC_IP>:/tmp/
   ssh azureuser@<PUBLIC_IP>
   sudo tar xzf /tmp/ztncui-backup.tar.gz -C /opt/ztncui/data
   sudo chown -R root:root /opt/ztncui/data
   cd /opt/ztncui && sudo docker compose up -d
   ```

4. **Verifiera** från laptop utanför labbet:

   ```bash
   zerotier-cli join <SAMMA_NETWORK_ID>
   zerotier-cli listnetworks
   ```

Samma Network ID behålls om `identity.secret` och `controller.d/` följer med.

### 9.9 Hårdning för produktion

| Område | Åtgärd |
|--------|--------|
| **Admin-UI** | Begränsa 3443/443 till kontors-IP; överväg **Azure Bastion** istället för öppen SSH |
| **SSH** | Endast nyckel, `PermitRootLogin no`, ev. fail2ban |
| **Patch** | `unattended-upgrades` eller månatlig maintenance window |
| **Backup** | Daglig backup av `/opt/ztncui/data` → Azure Blob (krypterad) eller Backup vault |
| **Monitoring** | Azure Monitor agent + alert om VM down / disk full |
| **Identity.secret** | Lägg **inte** i Git; Key Vault för backup-fil om policy kräver |
| **NSG** | Logga denied traffic (NSG flow logs → Storage / Log Analytics) |

#### Azure Backup (valfritt)

**Recovery Services vault** → backup policy för VM → OS-disk + datadisk.  
Komplettera med **logisk backup** av `/opt/ztncui/data` — VM-backup räcker inte alltid för fil-konsistens i Docker-volymer om backup tas medan container kör.

### 9.10 Kostnad (grovt, 2025–2026)

| Post | Ungefär / månad |
|------|-----------------|
| VM B2s + 32 GB disk | ~300–450 SEK |
| Static Public IP | ~30–50 SEK |
| Bandwidth | Ofta låg för controller; beror på antal peers |
| Azure DNS zone | ~7 SEK + queries |
| **Totalt pilot** | **~350–500 SEK/mån** |

Använd [Azure Pricing Calculator](https://azure.microsoft.com/pricing/calculator/) med `Sweden Central` + `Standard_B2s`.

### 9.11 Checklista efter deploy

```
□ Public IP är Static
□ NSG: UDP 9993 inbound
□ NSG: admin-UI/SSH begränsad till kända IP
□ docker ps → ztncui Up
□ ss -ulnp | grep 9993
□ ztncui UI nås (från tillåten IP)
□ Testklient utanför Azure: join + authorize + ping overlay
□ Backup av /opt/ztncui/data schemalagd
□ DNS A-record (om används)
□ Dokumenterat Network ID + var identity.secret backup lagras
```

### 9.12 När ska ni **inte** self-hosta på Azure?

| Scenario | Bättre val |
|----------|------------|
| &lt;20 användare, minimal IT-drift | **ZeroTier Central** (SaaS) |
| Krav på SLA utan egen drift | Managed overlay (Tailscale, etc.) eller ZeroTier Business |
| Redan AKS-standard | Överväg **separat** liten VM ändå — blanda inte controller med app-kluster |
| Compliance kräver data i EU | VM i `Sweden Central` + dokumentera var controller-state lagras |

> **Self-hosted på Azure** = ni äger VM, NSG, backup och patch. Bra när ni vill **lära er** (som lab) eller **kontrollera** controller-identiteten. SaaS är enklare om "det ska bara funka".

---

## 10. Felsökning

| Symptom | Trolig orsak | Åtgärd |
|---------|--------------|--------|
| Klient fastnar `REQUESTING_CONFIGURATION` | UDP 9993 blockeras | OPNsense/NSG-regel, rätt IP |
| UI når inte | Fel VLAN / TLS | Ping IP, `curl -k https://IP:3443` |
| `docker` startar inte i LXC | nesting saknas | `features: nesting=1` + omstart CT |
| `/dev/net/tun` saknas | Unprivileged utan map | Privileged CT eller tun-mount i LXC config |
| Peers offline efter flytt | Ny identitet / fel backup | Återställ `zt1/` från backup |

```bash
# Diagnostik på srv-ztnc01
docker logs ztncui --tail 100
zerotier-cli -D/var/lib/zerotier-one info    # om CLI installerad på värden
ss -ulnp | grep 9993
```

---

## Relaterad dokumentation

- [VLAN och OPNsense](../book-03-natverk/01-vlan-opnsense.md)
- [Cloudflare / extern åtkomst](../book-03-natverk/03-cloudflare-tls.md) — komplement, inte ersättning
- [Planerat Proxmox-underhåll](05-planerat-proxmox-underhall.md)

## Externa referenser

- [ZeroTier controller (upstream)](https://github.com/zerotier/zerotierone/blob/dev/nonfree/controller/README.md)
- [ztncui-aio (Docker)](https://github.com/kmahyyg/ztncui-aio)
- [ZeroTier docs](https://docs.zerotier.com/)
