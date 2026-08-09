# Envoy forward-auth

Skyddar media-appar **utan** att appen själv implementerar OIDC.

## Manifest

`kubernetes/apps/media/authentik-forward-auth/` — SecurityPolicies som pekar på Authentik outpost.

## Skyddade appar (urval)

- Prowlarr, Sonarr, Radarr, Lidarr, Bazarr
- Sonarr4k, Radarr4k
- Sabnzbd
- Maintainerr, Profilarr, Apprise

## Flöde

```
Browser → Envoy → forward-auth check → Authentik login → tillbaka → app
```

## Undantag

- **Jellyfin** — ingen Authentik (familjevänligt, eget auth)
- **Seerr** — OIDC in-app istället
- **Recyclarr / Unpackerr / Autoscan** — typiskt utan publik URL

## Theme Park

Injicerar CSS via EnvoyExtensionPolicy på *arr-hostnames — separat från auth.
