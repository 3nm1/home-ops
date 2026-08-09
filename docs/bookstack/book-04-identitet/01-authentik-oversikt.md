# Authentik — översikt

**URL:** `https://auth.engstrom.live`

SSO för hela homelabben. Körs i namespace `authentik` (security tier).

## Gateways

Authentik nås via **både** internal och external gateway — behövs för OIDC callbacks och forward-auth outpost.

## Outpost

Embedded outpost (`ak-outpost-authentik-embedded-outpost:9000`) används av Envoy **forward-auth** för media-appar.

## Providers / Applications

Skapa i Authentik UI:

| App | Typ | Redirect / callback |
|-----|-----|-------------------|
| BookStack | OIDC | enligt BookStack-dokumentation |
| Homarr | OIDC | Homarr callback URL |
| Nextcloud | OIDC | `https://cloud.engstrom.live/apps/user_oidc/code` |
| Seerr | OIDC | Seerr callback |

Slug för Nextcloud: `nextcloud` → discovery URI:
`https://auth.engstrom.live/application/o/nextcloud/.well-known/openid-configuration`

## Secrets

Client ID/secret i 1Password → ExternalSecret → app env vars.

## Forward-auth vs OIDC

| Metod | Appar | Hur |
|-------|-------|-----|
| **Forward-auth** | *arr, Sabnzbd, Maintainerr, … | Envoy SecurityPolicy → outpost |
| **OIDC in-app** | Homarr, BookStack, Nextcloud, Seerr | App läser OIDC env, hanterar login själv |
