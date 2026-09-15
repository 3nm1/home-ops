# sa7mie.se — inkommande mail (Maddy)

Self-hosted **inkommande** e-post för domänen **sa7mie.se** (Loopia), körs i klustret med **Maddy** — samma motor som [SMTP-relay](08-smtp-relay.md) men med lokal mailbox-lagring och IMAP.

## Arkitektur

```
Internet / andra mail-servrar
         │  SMTP :25 (MX)
         ▼
  OPNsense (port forward)
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
    ├── helmrelease.yaml
    ├── ocirepository.yaml
    └── pvc.yaml
```

## Förutsättningar (läs detta först)

Inkommande mail kräver mer än bara Kubernetes:

| Krav | Varför |
|------|--------|
| **Publik IP** | MX pekar hit från internet |
| **Port 25 inbound öppen** | Många ISP:er blockerar — verifiera |
| **OPNsense port forward** | `25, 587, 993` → `192.168.20.144` |
| **Loopia DNS** | MX, A, SPF, DKIM, DMARC |
| **TLS-certifikat** | Bootstrap = self-signed; produktion = Let's Encrypt |

> **Cloudflare Tunnel** hjälper **inte** för SMTP — det är HTTP. Mail måste nå LoadBalancer-IP:n direkt (eller via Loopia vidarebefordran till er publika IP).

### Om port 25 är blockerad

Alternativ utan egen MX:

1. **Loopia e-postpaket / vidarebefordran** → vidare till befintlig adress (ingen egen server)
2. **VPS/Azure** med öppen port 25 som MX (inte hemma-labb)
3. **Migrera DNS till Cloudflare Email Routing** (receive forward) — annan modell

---

## Loopia DNS (sa7mie.se)

Logga in på Loopia → **sa7mie.se** → DNS.

Ersätt `DIN_PUBLIKA_IP` med er faktiska WAN-IP (samma som OPNsense WAN).

| Typ | Host | Värde | TTL |
|-----|------|-------|-----|
| **A** | `mail` | `DIN_PUBLIKA_IP` | 300 |
| **MX** | `@` | `mail.sa7mie.se` (prio **10**) | 300 |
| **TXT** (SPF) | `@` | `v=spf1 ip4:DIN_PUBLIKA_IP -all` | 300 |
| **TXT** (DKIM) | `default._domainkey` | *(från Maddy efter start — se nedan)* | 300 |
| **TXT** (DMARC) | `_dmarc` | `v=DMARC1; p=none; rua=mailto:postmaster@sa7mie.se` | 300 |

---

## Deploy (Flux)

```bash
flux reconcile kustomization sa7mie-mail -n selfhosted --with-source
kubectl get pods -n selfhosted -l app.kubernetes.io/name=sa7mie-mail
kubectl get svc -n selfhosted sa7mie-mail
```

Förväntat:

| Check | OK |
|-------|-----|
| Pod | `Running` |
| Service EXTERNAL-IP | `192.168.20.144` |
| Portar | 25, 587, 993 |

---

## Skapa mailbox

Maddy skiljer **inloggningsuppgifter** och **IMAP-konto** — båda behövs.

```bash
# Byt lösenord interaktivt
kubectl exec -it -n selfhosted deploy/sa7mie-mail -- maddy creds create hej@sa7mie.se

# Skapa mailbox
kubectl exec -n selfhosted deploy/sa7mie-mail -- maddy imap-acct create hej@sa7mie.se

# Lista konton
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
| Användare | `hej@sa7mie.se` |

---

## DKIM (efter första start)

```bash
kubectl exec -n selfhosted deploy/sa7mie-mail -- cat /data/dkim/default.dns
```

Kopiera TXT-värdet till Loopia som `default._domainkey.sa7mie.se`.

---

## TLS (bootstrap → produktion)

Vid första deploy skapas ett **self-signed** cert i `/data/tls/` via initContainer. Det räcker för labbtest men ger varningar i klienter och sämre leverans till Gmail.

**Produktion:** ersätt med Let's Encrypt (DNS-01 via Loopia eller manuell certbot):

```bash
# Exempel — generera cert lokalt, kopiera till pod
certbot certonly --manual --preferred-challenges dns -d mail.sa7mie.se

kubectl cp fullchain.pem selfhosted/$(kubectl get pod -n selfhosted -l app.kubernetes.io/name=sa7mie-mail -o name | head -1 | cut -d/ -f2):/data/tls/fullchain.pem
kubectl cp privkey.pem selfhosted/$(kubectl get pod -n selfhosted -l app.kubernetes.io/name=sa7mie-mail -o name | head -1 | cut -d/ -f2):/data/tls/privkey.pem

kubectl rollout restart deployment sa7mie-mail -n selfhosted
```

---

## OPNsense port forward

| WAN port | Protokoll | Dest IP | Dest port |
|----------|-----------|---------|-----------|
| 25 | TCP | 192.168.20.144 | 25 |
| 587 | TCP | 192.168.20.144 | 587 |
| 993 | TCP | 192.168.20.144 | 993 |

Lägg regeln i rätt WAN-interface. Verifiera att ISP inte blockerar inkommande 25.

---

## Testa inkommande mail

1. Skapa mailbox `test@sa7mie.se` (ovan)
2. Skicka mail från Gmail/Outlook till `test@sa7mie.se`
3. Kolla loggar:

```bash
kubectl logs -n selfhosted deploy/sa7mie-mail -f
```

4. Läs via IMAP-klient (Thunderbird, Apple Mail, etc.)

Intern test från klustret:

```bash
kubectl run -n selfhosted mail-in-test --rm -it --restart=Never \
  --image=nicolaka/netshoot -- \
  sh -c 'apk add -q swaks && swaks --to test@sa7mie.se --from avsandare@gmail.com \
    --server sa7mie-mail.selfhosted.svc.cluster.local:25 --body "internal test"'
```

*(Extern leverans kräver korrekt MX + port forward.)*

---

## Felsökning

| Symptom | Åtgärd |
|---------|--------|
| Pod CrashLoop | `kubectl logs` — saknad `/data/maddy.conf` (PVC maskerar image-config; fixat via ConfigMap) eller saknad `/data/tls` |
| Inget mail från internet | MX? Port 25 forward? ISP block? |
| Mail i spam | SPF + DKIM + DMARC; riktigt TLS-cert; PTR (sällan hemma) |
| IMAP login fail | Kör både `creds create` **och** `imap-acct create` |
| `451` / greylisting | Normalt tillfälligt — försök igen |
| LoadBalancer pending | Cilium LB IPAM — kolla `192.168.20.144` ledig |

```bash
kubectl describe pod -n selfhosted -l app.kubernetes.io/name=sa7mie-mail
kubectl get endpoints -n selfhosted sa7mie-mail
dig MX sa7mie.se +short
dig A mail.sa7mie.se +short
```

---

## Säkerhet

- LoadBalancer-IP är på **LAN** — internet når den via OPNsense NAT
- Håll Maddy uppdaterad (samma image-tag som smtp-relay)
- Starka lösenord per mailbox
- Överväg fail2ban / rate limits vid abuse (Maddy har inbyggda limits)
- Backup av PVC `sa7mie-mail` (Longhorn/Velero) — innehåller all mail

---

## Skillnad mot smtp-relay

| | smtp-relay | sa7mie-mail |
|--|------------|-------------|
| Domän | engstrom.live (HELO) | sa7mie.se |
| IP | 192.168.20.143 | 192.168.20.144 |
| Inkommande | Nej | Ja (:25) |
| IMAP | Nej | Ja (:993) |
| Upstream | Bahnhof | — (lokal leverans) |
| Config | Custom maddy.conf | Auto `/data/maddy.conf` |
