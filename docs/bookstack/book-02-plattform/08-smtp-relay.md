# SMTP-relay (Milestone)

Intern utgående mail-gateway för homelabben — baserad på [onedr0p/home-ops smtp-relay](https://github.com/onedr0p/home-ops) och [Maddy](https://github.com/foxcpp/maddy).

## Arkitektur

```
Authentik / Nextcloud / BookStack
         │  port 25, ingen auth (internt)
         ▼
  smtp-relay (Maddy)          LoadBalancer: 192.168.20.143
         │  STARTTLS :587 + auth
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
| `SMTP_RELAY_USERNAME` | `din@bahnhof-adress.se` | Full e-postadress från Mina sidor |
| `SMTP_RELAY_PASSWORD` | `…` | Bahnhof e-postlösenord |
| `SMTP_RELAY_HOSTNAME` | `engstrom.live` | HELO-hostname för Maddy |
| `SMTP_FROM` | `din@bahnhof-adress.se` | Avsändare (From) i alla appar |

> **OBS:** Bahnhof förväntar sig normalt att From matchar ditt Bahnhof-konto. `@engstrom.live` kräver egen domänhantering/DNS — spara till senare.

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

```bash
flux reconcile kustomization smtp-relay -n flux-system --with-source
kubectl get pods -n selfhosted -l app.kubernetes.io/name=smtp-relay
kubectl get svc -n selfhosted smtp-relay
```

## Testa Authentik

Efter deploy och pod restart:

```bash
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
| Pod CrashLoop | Kolla secret sync: `kubectl get externalsecret -n selfhosted smtp-relay` |
| Relay auth fail | Verifiera Bahnhof user/pass på Mina sidor |
| Mail når inte fram | Kolla spam; From måste vara giltig Bahnhof-adress |
| Port 25 ut spärrad | OK — Maddy använder Bahnhof :587, inte direkt utgående 25 |

## Säkerhet

- Maddy lyssnar på LoadBalancer **endast** på LAN (`192.168.20.143`)
- Ingen auth internt — förutsätter att endast klustret/LAN når den
- Exponera **inte** mot internet utan TLS + auth

## Framtida förbättringar

- Byt upstream till Brevo/SES för `@engstrom.live` som avsändare
- Full inbox (IMAP) — hosted eller separat milestone, inte Maddy IMAP
