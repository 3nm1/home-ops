# Media — appar och URL:er

Basdomän: `engstrom.live` (via `${SECRET_DOMAIN}`).

## Publika webb-UI (internal gateway)

| App | URL | Auth |
|-----|-----|------|
| Prowlarr | `prowlarr.engstrom.live` | forward-auth |
| Sonarr | `sonarr.engstrom.live` | forward-auth |
| Sonarr 4K | `sonarr4k.engstrom.live` | forward-auth |
| Radarr | `radarr.engstrom.live` | forward-auth |
| Radarr 4K | `radarr4k.engstrom.live` | forward-auth |
| Lidarr | `lidarr.engstrom.live` | forward-auth |
| Bazarr | `bazarr.engstrom.live` | forward-auth |
| Sabnzbd | `sabnzbd.engstrom.live` | forward-auth |
| Jellyfin | `jellyfin.engstrom.live` | eget login (+ external) |
| Seerr | `seerr.engstrom.live` | OIDC (+ external) |
| Maintainerr | `maintainerr.engstrom.live` | forward-auth |
| Profilarr | `profilarr.engstrom.live` | forward-auth |
| Apprise | `apprise.engstrom.live` | forward-auth |
| Theme Park | `theme-park.engstrom.live` | — |

## Interna (ingen/intern URL)

| App | Syfte |
|-----|--------|
| Recyclarr | TRaSH guide sync till *arr |
| Unpackerr | Post-process downloads |
| Autoscan | Jellyfin scan triggers |
| Deduparr | Hitta dubbletter i Radarr/Sonarr |

## Namespace

Alla i `media`.

## Repo-path

`kubernetes/apps/media/<app>/`
