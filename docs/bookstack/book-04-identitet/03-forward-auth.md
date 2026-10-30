# Envoy forward-auth

Skyddar media-appar **utan** att appen själv implementerar OIDC.

## Manifest

`kubernetes/apps/media/authentik-forward-auth/` — SecurityPolicies som pekar på Authentik outpost.

## Skyddade appar (urval)

- Prowlarr, Sonarr, Radarr, Lidarr, Bazarr
- Sonarr4k, Radarr4k
- Sabnzbd
- Maintainerr, Profilarr, Apprise, Unpackerr

## Flöde

```
Browser → Envoy → forward-auth check → Authentik login → tillbaka → app
```

## Ny media-app med URL

När du lägger till en ny `*.engstrom.live`-host (t.ex. Unpackerr):

1. **HTTPRoute** + **SecurityPolicy** i Git (som övriga media-appar).
2. **Authentik:** samma **Proxy provider** som Sonarr/Radarr — lägg till **External host** `https://<app>.engstrom.live` (eller motsvarande wildcard som redan täcker subdomänen).
3. Verifiera **DNS** (samma som t.ex. `apprise.engstrom.live` → internal gateway `192.168.20.140`).
4. Lägg **inte** ömsesidiga `dependsOn` mellan app-kustomization och `authentik-forward-auth` (Flux deadlock).
5. `flux reconcile helmrelease <app> -n media` om HTTPRoute saknas trots Running pod.

## Undantag

- **Jellyfin** — ingen Authentik (familjevänligt, eget auth)
- **Seerr** — OIDC in-app istället
- **Recyclarr / Autoscan** — typiskt utan publik URL

## Theme Park

Injicerar CSS via EnvoyExtensionPolicy på *arr-hostnames — separat från auth.
