# Media automation

## Recyclarr vs Profilarr

| Verktyg | Roll | Status (aug 2026) |
|---------|------|-------------------|
| **Recyclarr** | Synkar TRaSH guides direkt till *arr YAML | Ursprunglig lösning |
| **Profilarr** | UI för quality profiles + TRaSH-profiler | Tillfälligt ersatt Recyclarr |

### Profilarr — profilmappning (viktigt att komma ihåg)

| Profilarr | *arr-instans |
|-----------|--------------|
| Series | Sonarr (1080p + 4K) |
| Movie | Radarr HD |
| SQP UHD | **Endast** Radarr 4K |

Fel mappning → fel quality profiles på fel instans.

### Återgå till Recyclarr

Sätt `enabled: false` på Profilarr eller kommentera bort `recyclarr/ks.yaml` i kustomization — reversibelt.

## Maintainerr

Rensar bibliotek baserat på regler (Jellyfin + Seerr + *arr integration).

## Autoscan

Triggar Jellyfin scan när ny media landar — snabbare än schemalagd scan.

## Unpackerr

Extraherar RAR/zip efter Sabnzbd — körs som intern tjänst.

## Apprise

Notification hub — central plats för alerts från olika tjänster.

## Theme Park

Enhetligt mörkt tema på *arr-UIs via CSS-injection (EnvoyExtensionPolicy).

## Deduparr

Hittar duplicerade filmer/serier mellan Radarr/Sonarr-instanser.
