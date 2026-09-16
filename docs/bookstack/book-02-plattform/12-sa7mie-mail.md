# sa7mie.se — inkommande mail (Maddy)

Self-hosted **inkommande** e-post för domänen **sa7mie.se** (Loopia), körs i klustret med **Maddy** — samma motor som [SMTP-relay](08-smtp-relay.md) men med lokal mailbox-lagring och IMAP.

**Status (2026-09):** Driftsatt och verifierad — inkommande mail från Outlook/Gmail fungerar.

## Arkitektur

```
Internet / andra mail-servrar
         │  SMTP :25 (MX → mail.sa7mie.se)
         ▼
  OPNsense WAN (217.27.189.66)
         │  NAT: EMAIL_PORTS → 192.168.20.144
         ▼
  sa7mie-mail (Maddy)          LoadBalancer: 192.168.20.144
         │  lokala mailboxes (Longhorn PVC)
         ▼
  Klient läser mail            IMAP :993, Submission :587
```

| Tjänst | Roll |
|--------|------|
| **smtp-relay** (`192.168.20.143`) | Utgående mail för homelab (`engstrom.live`) |
| **sa7mie-mail** (`192.168.20.144`) | Inkommande + mailbox för `@sa7mie.se` |

## Repo

```text
kubernetes/apps/selfhosted/sa7mie-mail/
├── ks.yaml
└── app/
    ├── helmrelease.yaml    # Maddy + ConfigMap (maddy.conf) + init TLS
    ├── ocirepository.yaml
    └── pvc.yaml
```

Tekniskt:

- **ConfigMap** med `maddy.conf.docker` — PVC på `/data` maskerar annars config från imagen (CrashLoop utan den).
- **initContainer** `bootstrap-tls` — self-signed cert i `/data/tls/` vid första körning.
- **LoadBalancer** med `externalTrafficPolicy: Local` (samma mönster som smtp-relay).

---

## Förutsättningar

| Krav | Varför |
|------|--------|
| **Korrekt publik WAN-IP i DNS** | Fel IP = MXToolbox timeout trots fungerande kluster |
| **Port 25 inbound** | Verifiera mot ISP (Bahnhof privat: fungerade med rätt IP) |
| **OPNsense port forward** | `25, 587, 993` → `192.168.20.144` |
| **Loopia DNS** | MX, A, SPF, DKIM, DMARC |
| **TLS** | Bootstrap self-signed; Let's Encrypt rekommenderas för produktion |

> **Cloudflare Tunnel** hjälper **inte** för SMTP — mail går direkt till WAN-IP → NAT → LoadBalancer.

### Bahnhof: WAN-IP vs gateway (viktigt)

På Bahnhof kan **WAN-IP** och **gateway** skilja sig (t.ex. `.66` vs `.65`).

| IP | Typisk roll |
|----|-------------|
| `217.27.189.66` | Er **publika IP** (NAT/OPNsense WAN) — ska stå i DNS |
| `217.27.189.65` | Kan vara gateway/grann-IP — **använd inte** i `mail` A om den inte svarar på :25 |

Symptom vid fel IP:

- LAN-test `nc 192.168.20.144 25` → **OK**
- `nc 217.27.189.65 25` → timeout
- OPNsense WAN-logg → **ingen trafik på port 25**
- MXToolbox SMTP Test → "Unable to connect"

Fix: kontrollera WAN-IP i OPNsense → uppdatera `mail` A + SPF.

---

## Loopia DNS (sa7mie.se)

Domänen hanteras hos Loopia. **`@` A → 194.9.94.x`** (Loopia-parkering) kan ligga kvar för webb — **mail går via MX**, inte apex-A.

### Obligatoriska poster

| Typ | Host | Värde |
|-----|------|-------|
| **A** | `mail` | `217.27.189.66` |
| **MX** | `@` | `10 mail.sa7mie.se.` (eller `10 mail` med `$ORIGIN`) |
| **TXT** (SPF) | `@` | `"v=spf1 ip4:217.27.189.66 -all"` |
| **TXT** (DKIM) | `default._domainkey` | `"v=DKIM1; k=rsa; p=MIIBIj..."` *(hela strängen, inga `"` runt p=)* |
| **TXT** (DMARC) | `_dmarc` | `"v=DMARC1; p=none; rua=mailto:postmaster@sa7mie.se"` |

> **Wildcard `*`** till 194.9.94.x täcker `mail` om ingen explicit A-post finns — **lägg alltid explicit `mail` A`**.

> **DKIM:** Långa nycklar kan delas i flera `"..."`-segment i zone-filen — resolvers slår ihop dem. I Loopia UI: en TXT med `v=DKIM1; k=rsa; p=...` utan extra citattecken runt base64.

### Verifiera DNS

```bash
dig MX sa7mie.se +short
dig A mail.sa7mie.se +short
dig TXT sa7mie.se +short
dig TXT default._domainkey.sa7mie.se +short
```

Förväntat:

```
10 mail.sa7mie.se.
217.27.189.66
"v=spf1 ip4:217.27.189.66 -all"
"v=DKIM1; k=rsa; p=..."
```

---

## OPNsense

Port forward (alias **`EMAIL_PORTS`**: 25, 587, 993):

| Interface | Protokoll | Dest port | Redirect | Beskrivning |
|-----------|-----------|-----------|----------|-------------|
| WAN | TCP | `EMAIL_PORTS` | `192.168.20.144` | WAN → EMAIL |

Kontrollera att **associerad pass-regel** på WAN finns (skapas ofta automatiskt med port forward).

Felsökning i **Firewall → Log Files → Live View**:

- Filtrera på **`dst port = 25`** (exakt) — inte "contains 25" (ger falska träffar som `25688`).
- Ingen trafik vid extern test → fel WAN-IP i DNS eller ISP-block upstream.

---

## Dynamic DNS (OPNsense → Loopia)

Om **WAN-IP** byts (sällan, men möjligt) ska **`mail.sa7mie.se`** följa med — annars slutar inkommande mail fungera trots fungerande kluster.

**Services → Dynamic DNS → Settings → Accounts**

| Fält | Rekommenderat värde |
|------|---------------------|
| Enabled | ✓ |
| Service | `loopia` |
| Username | Loopia-kontoinloggning (testa domän om Loopia accepterar det) |
| Password | Loopia-kontolösenord |
| **Hostname(s)** | **`mail.sa7mie.se`** *(kritiskt)* |
| Interface to monitor | `WAN` |
| Check ip method | `akamai` (eller `dyndns.loopia.se/checkip`) |
| Check ip timeout | `10` |
| Force SSL | ✓ |

Valfritt — uppdatera apex också:

```text
sa7mie.se,mail.sa7mie.se
```

> **Vanligt misstag:** bara `sa7mie.se` i Hostname(s) uppdaterar `@` men **inte** `mail` — MX pekar på `mail.sa7mie.se` som då behåller gammal IP.

### Wildcard

Sätt **wildcard OFF / NOCHG** om alternativet finns — `ON` kan störa manuella DNS-poster (`MX`, DKIM, `_dmarc`).

### Vad DDNS inte fixar

| Post | Uppdateras av DDNS? |
|------|---------------------|
| `mail` A | Ja (om `mail.sa7mie.se` finns i Hostname(s)) |
| `@` MX | Nej — manuell post, ändras sällan |
| DKIM TXT | Nej |
| DMARC TXT | Nej |
| **SPF TXT** | **Nej** — uppdatera manuellt vid IP-byte: `v=spf1 ip4:NY_IP -all` |

### Verifiera DDNS

1. Spara kontot i OPNsense → kolla **Dynamic DNS-loggen** (ska ge `good`, inte `badauth`).
2. Bekräfta DNS:

```bash
dig A mail.sa7mie.se +short
# ska matcha nuvarande WAN (t.ex. 217.27.189.66)
```

3. Vid IP-byte: uppdatera **SPF** manuellt i Loopia efter DDNS-körning.

---

## Deploy (Flux)

```bash
flux reconcile kustomization sa7mie-mail -n selfhosted --with-source
kubectl get pods,svc,endpoints -n selfhosted -l app.kubernetes.io/name=sa7mie-mail -o wide
```

Förväntat:

| Check | OK |
|-------|-----|
| Pod | `1/1 Running` på t.ex. `srv-talos03` |
| Service EXTERNAL-IP | `192.168.20.144` |
| Endpoints | `:25`, `:587`, `:993` |
| Portar | 25, 587, 993 |

---

## Skapa mailbox

Maddy skiljer **inloggningsuppgifter** och **IMAP-konto** — båda behövs.

```bash
kubectl exec -it -n selfhosted deploy/sa7mie-mail -- maddy creds create me@sa7mie.se
kubectl exec -n selfhosted deploy/sa7mie-mail -- maddy imap-acct create me@sa7mie.se
kubectl exec -n selfhosted deploy/sa7mie-mail -- maddy creds list
kubectl exec -n selfhosted deploy/sa7mie-mail -- maddy imap-acct list
```

Klientinställningar:

| Inställning | Värde |
|-------------|-------|
| IMAP server | `mail.sa7mie.se` |
| IMAP port | **993** (SSL/TLS) |
| SMTP submission | `mail.sa7mie.se` |
| SMTP port | **587** (STARTTLS) |
| Användare | `me@sa7mie.se` |

---

## DKIM

Nycklar under **`/data/dkim_keys/`** — filnamn: `sa7mie.se_default.dns`.

Generera manuellt (behövs inte vänta på utgående mail):

```bash
kubectl exec -n selfhosted deploy/sa7mie-mail -- maddy dkim generate sa7mie.se default
kubectl exec -n selfhosted deploy/sa7mie-mail -- cat /data/dkim_keys/sa7mie.se_default.dns
```

Publicera som TXT på **`default._domainkey.sa7mie.se`**.

---

## TLS (bootstrap → produktion)

Vid första deploy: **self-signed** cert i `/data/tls/` (initContainer). Fungerar för inkommande test; klienter varnar.

**Produktion:** Let's Encrypt (DNS-01 via Loopia):

```bash
certbot certonly --manual --preferred-challenges dns -d mail.sa7mie.se
# kopiera fullchain.pem + privkey.pem till /data/tls/ i podden
kubectl rollout restart deployment sa7mie-mail -n selfhosted
```

---

## Verifiering (checklista)

Kör i ordning efter deploy + DNS:

### 1. Kluster internt

```bash
nc -zv 192.168.20.144 25
kubectl logs -n selfhosted deploy/sa7mie-mail --tail=10
```

### 2. WAN utifrån

```bash
nc -zv 217.27.189.66 25
# Förväntat: Connection succeeded
```

### 3. MXToolbox

- **MX Lookup** → `mail.sa7mie.se` → `217.27.189.66`
- **SMTP Test** → banner `220 mail.sa7mie.se ESMTP Service Ready`
- **Blacklist Check** → inga listningar

Varning **"Reverse DNS does not match SMTP Banner"** är förväntad på Bahnhof privat:

| | Värde |
|--|-------|
| Banner | `mail.sa7mie.se` |
| PTR | `h-217-27-189-66.A980.priv.bahnhof.se` |

Påverkar sällan **inkommande** mail; kan ge högre spam-score vid **utgående**. Fråga Bahnhof om egen PTR vid behov.

Varning **"DMARC Policy Not Enabled"** = `p=none` — OK i testfas. Skärp senare till `quarantine`/`reject`.

### 4. End-to-end

1. Skapa mailbox (`creds` + `imap-acct`)
2. Skicka från extern adress (Outlook/Gmail) → `me@sa7mie.se`
3. Loggar ska visa:

```text
smtp: incoming message  {"sender":"...","src_host":"...outbound.protection.outlook.com",...}
smtp: RCPT ok           {"rcpt":"me@sa7mie.se"}
smtp: accepted          {"msg_id":"..."}
```

4. Läs via IMAP-klient (port 993)

---

## Felsökning

| Symptom | Trolig orsak | Åtgärd |
|---------|--------------|--------|
| Pod CrashLoop | Saknad `/data/maddy.conf` | ConfigMap i HelmRelease (redan fixat) |
| Pod CrashLoop | Saknad TLS | Kolla initContainer `bootstrap-tls` |
| LAN OK, WAN timeout | Fel IP i DNS (.65 vs .66) | Uppdatera `mail` A + SPF |
| LAN OK, WAN timeout, rätt IP | ISP blockar inbound 25 | Kontakta Bahnhof; alternativ MX hos VPS/Loopia |
| MXToolbox OK, inget mail | Mailbox saknas | `creds create` + `imap-acct create` |
| `550 User doesn't exist` | Saknad `imap-acct` | Kör `imap-acct create` |
| Loggar `connection reset` från `.153` | Kubelet TCP-prober | Harmlöst brus |
| Mail i spam (utgående) | PTR mismatch, self-signed TLS | LE-cert + ev. PTR hos Bahnhof |
| IMAP login fail | Bara `creds` utan `imap-acct` | Skapa båda |

```bash
kubectl describe pod -n selfhosted -l app.kubernetes.io/name=sa7mie-mail
kubectl get endpoints -n selfhosted sa7mie-mail
dig MX sa7mie.se +short
dig A mail.sa7mie.se +short
```

Intern SMTP-test (kräver inte WAN):

```bash
kubectl run -n selfhosted mail-in-test --rm -it --restart=Never \
  --image=nicolaka/netshoot -- \
  sh -c 'apk add -q swaks && swaks --to me@sa7mie.se --from test@example.com \
    --server sa7mie-mail.selfhosted.svc.cluster.local:25 --body "internal test"'
```

---

## Säkerhet och drift

- LoadBalancer-IP är på **LAN** — internet når via OPNsense NAT
- Håll Maddy uppdaterad (samma image-tag som smtp-relay: `0.9.5`)
- Starka lösenord per mailbox
- **Backup** av PVC `sa7mie-mail` (Longhorn/Velero) — all mail + credentials.db + imapsql.db
- Planera LE-cert + DMARC `p=quarantine` innan heavy utgående användning

---

## Skillnad mot smtp-relay

| | smtp-relay | sa7mie-mail |
|--|------------|-------------|
| Domän | engstrom.live (HELO) | sa7mie.se |
| LB IP | 192.168.20.143 | 192.168.20.144 |
| Inkommande | Nej | Ja (:25) |
| IMAP | Nej | Ja (:993) |
| Upstream | Bahnhof utgående | — (lokal leverans) |
| Config | Custom maddy.conf (relay) | ConfigMap maddy.conf (full server) |
| Secrets | 1Password (Bahnhof) | — (mailbox-lösenord via `maddy creds`) |

---

## Relaterat

- [SMTP-relay](08-smtp-relay.md) — utgående mail homelab
- [Self-hosted appar](../book-07-selfhosted/01-appar.md)
