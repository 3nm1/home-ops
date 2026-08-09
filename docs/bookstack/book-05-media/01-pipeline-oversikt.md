# Media pipeline — översikt

## Flöde

```
                    ┌─────────────┐
                    │  Prowlarr   │  Indexers
                    └──────┬──────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
   ┌──────────┐     ┌──────────┐     ┌──────────┐
   │  Sonarr  │     │  Radarr  │     │  Lidarr  │
   │ Sonarr4k │     │ Radarr4k │     │          │
   └────┬─────┘     └────┬─────┘     └────┬─────┘
        │                │                │
        └────────────────┼────────────────┘
                         ▼
                   ┌──────────┐
                   │ Sabnzbd  │  Usenet download
                   └────┬─────┘
                        ▼
                   ┌──────────┐
                   │ Unpackerr│  Extrahera arkiv
                   └────┬─────┘
                        ▼
                   ┌──────────┐
                   │ Autoscan │  Trigger library scan
                   └────┬─────┘
                        ▼
                   ┌──────────┐
                   │ Jellyfin │  Uppspelning (GPU på srv-talos04)
                   └──────────┘

   Seerr ──requests──► Sonarr/Radarr
   Bazarr ──subtitles──► Sonarr/Radarr
```

## 1080p vs 4K

Separata instanser:

- `sonarr` / `radarr` — 1080p
- `sonarr4k` / `radarr4k` — 4K (restriktivare profiler)

## Data

All media-data på NFS: `192.168.20.20:/mnt/Backup/data`

## GPU

Jellyfin transcode på **srv-talos04** med NVIDIA (taint/toleration).

## Auth

*arr m.fl.: Authentik **forward-auth** via Envoy.

Seerr: **OIDC** in-app.
