# Pterodactyl — extra Wings-nod

En andra maskin som kan köra spel. Panelen på [srv-mc01](09-pterodactyl-srv-mc01.md) behålls. Den här sidan är bara den nya noden.

## Vad som räcker

| På den nya VM:en | Inte på den nya VM:en |
|------------------|------------------------|
| Ubuntu, Docker, Wings | Panel, MariaDB, Redis, nginx, PHP |
| Eget certifikat för nodens namn | Kopia av mc01:s `config.yml` eller token |
| Ny nod i den befintliga panelen | Ny location, om maskinen står i samma hus |

Wings på mc01 och Wings på den nya VM:en är två daemoner. De delar panelen och platsen `se-morbylanga`.

En ny nod flyttar inte en befintlig värld. Den ger en plats att skapa en ny server på. En värld flyttas som backup från den gamla servern och restore på den nya.

## Placering

| Val | Här |
|-----|-----|
| Proxmox-värd | En annan än den som kör srv-mc01. Inte px-node03. |
| OS | Ubuntu 24.04, VM, inte LXC |
| CPU-typ | `host` |
| Resurser | 4 vCPU, 8–12 GB RAM, 40 GB+ lokal disk. Anpassa efter spelet. |
| Nät | VLAN 20, egen statisk IP |
| Namn | `srv-mc02.lab.engstrom.live` |
| Plats i panelen | `se-morbylanga` |
| Nodnamn | `mc02` |

Följ VM-inställningarna i [srv-mc01](09-pterodactyl-srv-mc01.md) (VirtIO SCSI, cache `none`, QEMU Guest Agent, start at boot).

## Brandvägg

mc01 och mc02 sitter på samma VLAN 20. Trafik mellan dem går inte via OPNsense. Panelen når Wings på mc02:s port **8080** direkt.

Klienter på VLAN 10 gör det inte. Öppna spelporten mot **mc02:s IP**, inte mot 192.168.20.70.

| Från | Till | Port | Syfte |
|------|------|------|--------|
| VLAN 10 | mc02 | spelets TCP-port | Själva spelet. 25565 om det är en andra Minecraft och den lyssnar där. |
| VLAN 10, din admin-dator | mc02 | 2022/tcp | SFTP |
| WAN | mc02 | spelporten | Bara om vänner utifrån ska in |

Stäng WAN mot 8080, 2022 och 22. Lägg servern manuellt i klienten. LAN-sökning ser den inte.

## 1. Förbered VM:en

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y qemu-guest-agent curl ca-certificates
sudo systemctl enable --now qemu-guest-agent
sudo hostnamectl set-hostname srv-mc02
```

DNS-override i OPNsense: `srv-mc02.lab.engstrom.live` → VM:ens IP.

Certifikat med en **ny** API-token, samma mall som `certbot-srv-mc01` (Zone DNS Edit, bara zonen `engstrom.live`). Kopiera inte `cloudflare.ini` från mc01.

```bash
sudo apt install -y certbot python3-certbot-dns-cloudflare
sudo mkdir -p /root/.secrets
sudo nano /root/.secrets/cloudflare.ini
```

```ini
dns_cloudflare_api_token = klistra-token-här
```

Utan citationstecken.

```bash
sudo chmod 600 /root/.secrets/cloudflare.ini
sudo certbot certonly \
  --dns-cloudflare \
  --dns-cloudflare-credentials /root/.secrets/cloudflare.ini \
  -d srv-mc02.lab.engstrom.live
```

## 2. Docker och Wings

```bash
curl -sSL https://get.docker.com/ | CHANNEL=stable sudo bash
sudo systemctl enable --now docker
sudo mkdir -p /etc/docker /etc/pterodactyl
printf '%s\n' '{
  "dns": ["192.168.20.1"]
}' | sudo tee /etc/docker/daemon.json
sudo systemctl restart docker
sudo curl -L -o /usr/local/bin/wings \
  https://github.com/pterodactyl/wings/releases/latest/download/wings_linux_amd64
sudo chmod u+x /usr/local/bin/wings
```

`daemon.json` gör att vanliga `docker run` använder OPNsense som DNS. Wings själv skickar med en egen DNS om den inte står i `config.yml`. Det läggs in i nästa steg.

## 3. Noden i panelen

På mc01, i panelen: **Admin → Nodes → Create New**.

| Fält | Värde |
|------|-------|
| Location | `se-morbylanga` |
| Name | `mc02` |
| FQDN | `srv-mc02.lab.engstrom.live` |
| Communicate Over SSL | Ja |
| Behind Proxy | Nej |
| Daemon Port | `8080` |
| SFTP Port | `2022` |
| Total Memory | Det du kan avvara, i MB. Lämna minst 2 GB till OS och Wings. |
| Memory Over-Allocation | `0` |
| Disk | Storleken på speldisken, i MB. Lämna plats till OS. |
| Disk Over-Allocation | `0` |

Noden har inget CPU-fält. Taket är VM:ens kärnor.

Öppna noden → **Configuration**. Rutan är text i panelen. Spara den på **mc02**, inte på mc01:

```bash
sudo nano /etc/pterodactyl/config.yml
```

Klistra in hela rutan. Längst ned, om blocket `docker:` inte redan finns:

```yaml
docker:
  network:
    dns:
      - 192.168.20.1
```

Finns `docker:` redan, lägg bara till `dns` under `network`. Utan den raden använder Wings `1.1.1.1`, och OPNsense släpper inte det.

```bash
sudo chmod 600 /etc/pterodactyl/config.yml
```

`/etc/systemd/system/wings.service`:

```ini
[Unit]
Description=Pterodactyl Wings
After=docker.service
Requires=docker.service

[Service]
User=root
WorkingDirectory=/etc/pterodactyl
LimitNOFILE=4096
ExecStart=/usr/local/bin/wings
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now wings
sudo systemctl status wings
```

Noden ska bli grön i panelen. `Configuration File Not Found` betyder att filen inte ligger på `/etc/pterodactyl/config.yml` på just den här VM:en.

På noden: **Allocation**. Lägg till mc02:s egen IP och porten spelet ska ha. Använd inte 192.168.20.70.

## 4. Server på den nya noden

**Admin → Servers → Create New.** Välj nod **mc02** och den nya allokeringen. Resten är samma som en server på mc01.

För Minecraft: startup-raden behöver `-Djava.net.preferIPv4Stack=true` före `-jar`. VLAN 20 har ingen fungerande IPv6-väg ut, och utan flaggan misslyckas Papers första nedladdning från Mojang.

## Hälsokoll

På mc02:

```bash
systemctl is-active docker wings
ss -tlpn | grep -E '8080|2022'
```

Från mc01:

```bash
timeout 3 bash -c 'echo > /dev/tcp/<mc02-ip>/8080' && echo open || echo closed
```

`open` och en grön nod betyder att panelen ser Wings. Spelporten testas från VLAN 10 mot mc02:s IP, inte mot mc01.
