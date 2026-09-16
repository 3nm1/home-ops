# Self-hosted verktyg

Namespace: `selfhosted`  
Repo: `kubernetes/apps/selfhosted/`

## Appar

| App | URL | Auth | DB / storage |
|-----|-----|------|--------------|
| **Homarr** | `homarr.engstrom.live` | OIDC | PVC |
| **SMTP-relay** | `192.168.20.143:25` (LAN) | — | emptyDir |
| **sa7mie-mail** | `mail.sa7mie.se` (MX → WAN) | Maddy creds | PVC `@sa7mie.se` |
| **BookStack** | `bookstack.engstrom.live` | OIDC | MariaDB sidecar + PVC |
| **Homebox** | `homebox.engstrom.live` | Lokalt | PVC |
| **Stirling PDF** | `stirling-pdf.engstrom.live` | — | — |
| **IT-Tools** | `it-tools.engstrom.live` | — | — |

## Homarr

Central dashboard — länkar till övriga tjänster. Bra startpunkt efter login.

## BookStack

**Den här dokumentationen** — kör i klustret men markdown-källorna ligger i Git under `docs/bookstack/`.

Import: se `docs/bookstack/README.md`.

## Homebox

Inventering av saker i hemmet — separat från Home Lab infra.

## sa7mie-mail

Inkommande e-post för domänen **sa7mie.se** (Loopia) — Maddy med IMAP på `:993`.

- LoadBalancer: `192.168.20.144` (LAN)
- WAN via OPNsense NAT → `217.27.189.66`
- Ingen HTTPRoute — nås via MX/SMTP/IMAP, inte Envoy

Se [sa7mie.se mail](../book-02-plattform/12-sa7mie-mail.md).

## Stirling PDF & IT-Tools

Utility-appar utan SSO — enkla verktyg i webbläsaren.

## Gemensamt mönster

- bjw-s **app-template** via OCIRepository
- HTTPRoute → `envoy-internal`
- Secrets från 1Password där det behövs
