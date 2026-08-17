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
- Provisioneras via Helm **`before-starting`-hook** (körs vid varje pod-start):
  - `occ app:install user_oidc` / `occ app:enable user_oidc`
  - `occ user_oidc:provider authentik ...`
  - SMTP-konfiguration
- Env: `OIDC_CLIENT_ID`, `OIDC_CLIENT_SECRET`, `OIDC_DISCOVERY_URI`
- **Flux-tips:** escapa `$${OIDC_*}` i hooks så postBuild inte äter variablerna
- **Group provisioning:** `--mapping-groups=groups --group-provisioning=1`
- **Credentials:** Client ID/secret i 1Password måste matcha Authentik-providern

Detaljer: [Nextcloud — användare, grupper och skeleton](../book-06-familj/04-nextcloud-anvandare-grupper-skeleton.md)

## Seerr

- Media requests
- OIDC för familj/användare
- Jobb i manifest för initial setup

## Checklista ny OIDC-app

1. Skapa Provider + Application i **Authentik**
2. Kopiera Client ID/secret **från Authentik** till 1Password
3. ExternalSecret + env i HelmRelease
4. Verifiera redirect URI exakt (trailing slash matters ibland)
5. `flux reconcile externalsecret ... --force`
6. Testa login i inkognito (förvänta **MFA** efter lösenord — se [MFA och recovery](05-authentik-mfa-och-recovery.md))

## Authentik som identitetsnav

| Sköts i Authentik | Sköts i appen |
|-------------------|---------------|
| Användare, MFA, grupper (SSO) | App-specifik data |
| OIDC client credentials | Delade mappar (Nextcloud group folders) |
| Brand / login flows | Lokal break-glass-admin |
