# SMTP-relay (Milestone)

Intern utgående mail-gateway för homelabben — baserad på [onedr0p/home-ops smtp-relay](https://github.com/onedr0p/home-ops) och [Maddy](https://github.com/foxcpp/maddy).

## Arkitektur

```
Authentik / Nextcloud / BookStack
         │  port 25, ingen auth (internt)
         ▼
  smtp-relay (Maddy)          LoadBalancer: 192.168.20.143
         │  SMTPS :465 + auth (SSL/TLS, som Nextcloud/Bahnhof)
         ▼
  mailout.privat.bahnhof.se   (Bahnhof upstream)
         ▼
  mottagarens inbox (Gmail, iCloud, …)
```

## Repo

```text
kubernetes/apps/selfhosted/smtp-relay/
├── ks.yaml
└── app/
    ├── helmrelease.yaml
    ├── externalsecret.yaml
    └── ocirepository.yaml
```

## 1Password — skapa post `smtp-relay`

| Fält | Exempel | Beskrivning |
|------|---------|-------------|
| `SMTP_RELAY_SERVER` | `mailout.privat.bahnhof.se` | Bahnhof utgående SMTP |
| `SMTP_RELAY_USERNAME` | `mc957275` | Inloggningsnamn från Mina sidor (inte alltid full e-postadress) |
| `SMTP_RELAY_PASSWORD` | `…` | Bahnhof e-postlösenord |
| `SMTP_RELAY_HOSTNAME` | `engstrom.live` | HELO-hostname för Maddy |
| `SMTP_FROM` | `admin@engstrom.live` | Avsändare (From) i Authentik m.fl. |

> **OBS:** Upstream mot Bahnhof använder **port 465 med SSL/TLS** (SMTPS), samma som fungerande Nextcloud på TrueNAS — inte port 587/STARTTLS.

Företagskund? Byt till `mailout.foretag.bahnhof.se`.

## App-kopplingar

| App | SMTP-host | Port | Auth |
|-----|-----------|------|------|
| Authentik | `smtp-relay.selfhosted.svc.cluster.local` | 25 | Nej |
| Nextcloud | samma (via occ hooks) | 25 | Nej |
| BookStack | samma (MAIL_HOST env) | 25 | Nej |

`SMTP_FROM` hämtas från 1Password-posten `smtp-relay` till Authentik/Nextcloud/BookStack via ExternalSecret.

## Kluster-adresser

| Typ | Värde |
|-----|-------|
| Service (in-cluster) | `smtp-relay.selfhosted.svc.cluster.local:25` |
| LoadBalancer (LAN) | `192.168.20.143:25` |

## Deploy

Child Kustomizations ligger i app-namespaces, inte `flux-system`:

```bash
flux reconcile kustomization smtp-relay -n selfhosted --with-source
flux reconcile kustomization authentik -n authentik --with-source
kubectl get pods -n selfhosted -l app.kubernetes.io/name=smtp-relay
kubectl get svc -n selfhosted smtp-relay
```

## Testa Authentik

Efter deploy och pod restart:

```bash
# Verifiera att worker fått SMTP-env (ska visa HOST och PORT=25)
kubectl exec -n authentik deploy/authentik-worker -- env | grep AUTHENTIK_EMAIL

# Verifiera att SMTP_FROM fyllts i från 1Password
kubectl get secret authentik-secret -n authentik -o jsonpath='{.data.SMTP_FROM}' | base64 -d; echo

kubectl exec -n authentik deploy/authentik-server -- ak test_email <din@mottagare.se>
```

Eller via Authentik UI → System → Test email.

## Testa manuellt (från klustret)

```bash
kubectl run -n selfhosted mail-test --rm -it --restart=Never \
  --image=nicolaka/netshoot -- \
  sh -c 'apk add -q swaks && swaks --to dig@test.se --from din@bahnhof.se \
    --server smtp-relay.selfhosted.svc.cluster.local:25 --body "test"'
```

(Ersätt adresser — `dig@test.se` behöver vara en riktig mottagare du kan kolla.)

## Felsökning

| Symptom | Åtgärd |
|---------|--------|
| `kustomization "smtp-relay" not found` i flux-system | Använd `-n selfhosted` (Authentik: `-n authentik`) |
| `Connection refused` / `from_email: authentik@localhost` | Worker saknar `AUTHENTIK_EMAIL__HOST` — pusha Git, `flux reconcile helmrelease authentik -n authentik --force`, restart worker |
| Tom `SMTP_FROM` i `authentik-secret` | Skapa/fyll 1Password-post `smtp-relay` med fält `SMTP_FROM`, force-sync ExternalSecret |
| `AUTHENTIK_EMAIL__PORT=587` utan `HOST` | Gammal Helm-config på klustret — samma som ovan |
| Pod CrashLoop | Kolla secret sync: `kubectl get externalsecret -n selfhosted smtp-relay` |
| Relay auth fail | Verifiera Bahnhof user/pass på Mina sidor |
| `TLS required but unsupported by downstream` | Port 465 uses implicit TLS — Maddy måste ha `starttls no` med `tls://` (fixat i config) |
| Mail når inte fram | Kolla spam; verifiera `SMTP_RELAY_USERNAME` (t.ex. `mc957275`) |
| Port 25 ut spärrad | OK — Maddy använder Bahnhof :465 (SMTPS), inte direkt utgående 25 |
| Maddy loggar `accepted` men inget mail | Se avsnittet *accepted men inget mail* nedan |

### `accepted` men inget mail

Authentik → Maddy fungerar om du ser `smtp: accepted` i relay-loggen. Då fastnar leveransen troligen på **Bahnhof → mottagare**.

1. **Kolla utgående leverans i relay-loggen** (sök efter msg_id eller fel):

```bash
kubectl logs -n selfhosted deploy/smtp-relay --since=30m | grep -Ei 'msg_id|remote|queue|fail|reject|deliver|550|553|554'
kubectl exec -n selfhosted deploy/smtp-relay -- maddy queue list 2>/dev/null || true
```

2. **Verifiera 1Password matchar TrueNAS/Nextcloud** som fungerar:

   - `SMTP_RELAY_SERVER` = `mailout.privat.bahnhof.se`
   - `SMTP_RELAY_USERNAME` = inloggningsnamn (t.ex. `mc957275`)
   - `SMTP_RELAY_PASSWORD` = samma lösenord som i Nextcloud
   - Upstream ska vara **465 SSL/TLS** (fixat i Maddy-config)

```bash
kubectl get secret smtp-relay-secret -n selfhosted -o jsonpath='{.data.SMTP_RELAY_USERNAME}' | base64 -d; echo
```

3. **Testa Bahnhof direkt** (kringgår Authentik):

```bash
kubectl run -n selfhosted mail-test --rm -it --restart=Never \
  --image=nicolaka/netshoot -- \
  sh -c 'apk add -q swaks && swaks --to enmi@telia.com --from DIN@BAHNHOF.SE \
    --server smtp-relay.selfhosted.svc.cluster.local:25 --body "relay test"'
```

4. **Kolla skräppost** hos mottagaren (Telia filtrerar hårt utan SPF/DKIM).

Efter Git-push med uppdaterad Maddy-config (Bahnhof **465 SMTPS**):

```bash
flux reconcile kustomization smtp-relay -n selfhosted --with-source
kubectl rollout restart deployment/smtp-relay -n selfhosted
kubectl logs -n selfhosted deploy/smtp-relay -f
```

Efter Git-push, kör i ordning:

```bash
flux reconcile source git flux-system -n flux-system
flux reconcile kustomization smtp-relay -n selfhosted --with-source
kubectl annotate externalsecret authentik -n authentik force-sync=$(date +%s) --overwrite
flux reconcile kustomization authentik -n authentik --with-source
flux reconcile helmrelease authentik -n authentik --force
kubectl rollout status deployment/authentik-worker -n authentik
```

## Säkerhet

- Maddy lyssnar på LoadBalancer **endast** på LAN (`192.168.20.143`)
- Ingen auth internt — förutsätter att endast klustret/LAN når den
- Exponera **inte** mot internet utan TLS + auth

## Framtida förbättringar

- Byt upstream till Brevo/SES för `@engstrom.live` som avsändare
- Full inbox (IMAP) — hosted eller separat milestone, inte Maddy IMAP
