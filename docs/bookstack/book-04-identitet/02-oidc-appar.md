# OIDC-appar

Appar som använder **OpenID Connect** direkt (inte forward-auth).

## BookStack

- `OIDC_ISSUER`: `https://auth.engstrom.live/application/o/bookstack/`
- Konfigurerat i `kubernetes/apps/selfhosted/bookstack/app/helmrelease.yaml`

## Homarr

- OIDC via Authentik provider
- Dashboard för alla tjänster

## Nextcloud

- App: **user_oidc**
- Provisioneras via Helm **post-install/post-upgrade hooks**:
  - `occ app:install user_oidc`
  - `occ user_oidc:provider authentik ...`
- Env: `OIDC_CLIENT_ID`, `OIDC_CLIENT_SECRET`, `OIDC_DISCOVERY_URI`
- **Flux-tips:** escapa `$${OIDC_*}` i hooks så postBuild inte äter variablerna

## Seerr

- Media requests
- OIDC för familj/användare
- Jobb i manifest för initial setup

## Checklista ny OIDC-app

1. Skapa Provider + Application i Authentik
2. Lägg client ID/secret i 1Password
3. ExternalSecret + env i HelmRelease
4. Verifiera redirect URI exakt (trailing slash matters ibland)
5. Testa login i inkognito
