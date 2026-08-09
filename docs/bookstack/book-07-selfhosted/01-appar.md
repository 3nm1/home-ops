# Self-hosted verktyg

Namespace: `selfhosted`  
Repo: `kubernetes/apps/selfhosted/`

## Appar

| App | URL | Auth | DB / storage |
|-----|-----|------|--------------|
| **Homarr** | `homarr.engstrom.live` | OIDC | PVC |
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

## Stirling PDF & IT-Tools

Utility-appar utan SSO — enkla verktyg i webbläsaren.

## Gemensamt mönster

- bjw-s **app-template** via OCIRepository
- HTTPRoute → `envoy-internal`
- Secrets från 1Password där det behövs
