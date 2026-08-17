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

## MFA och recovery

**MFA** är obligatorisk för alla via `default-authentication-flow` (TOTP + WebAuthn).

**Recovery** (`default-recovery-flow`) importeras från bundled blueprint — finns inte färdigt i ny installation.

Se [Authentik — MFA och recovery](05-authentik-mfa-och-recovery.md) för setup, test och felsökning.

### E-post (lösenordsåterställning m.m.)

Authentik skickar mail via intern relay (miljövariabler på **server och worker**):

```yaml
AUTHENTIK_EMAIL__HOST: smtp-relay.selfhosted.svc.cluster.local
AUTHENTIK_EMAIL__PORT: 25
AUTHENTIK_EMAIL__FROM:  # från authentik-secret → SMTP_FROM (1Password smtp-relay)
```

Test:

```bash
kubectl exec -n authentik deploy/authentik-worker -- env | grep AUTHENTIK_EMAIL
kubectl exec -n authentik deploy/authentik-server -- ak test_email mottagare@example.com
```

Kolla worker-loggar om det timeoutar: `kubectl logs -n authentik deploy/authentik-worker --tail=50`

## Secrets

Client ID/secret i 1Password → ExternalSecret → app env vars. **Authentik är källan** — vid mismatch får du *Client ID is missing or invalid*.

## Fil-lagring och branding

Authentik 2026.x kräver PVC monterad på **`/data`** för logo, favicon och Customization → Files.

Repo: `authentik-data` PVC (2Gi Longhorn) i `kubernetes/apps/security/authentik/app/`.

Se [Authentik — branding och flows](04-authentik-branding-flows.md) och [MFA och recovery](05-authentik-mfa-och-recovery.md).

## Forward-auth vs OIDC

| Metod | Appar | Hur |
|-------|-------|-----|
| **Forward-auth** | *arr, Sabnzbd, Maintainerr, … | Envoy SecurityPolicy → outpost |
| **OIDC in-app** | Homarr, BookStack, Nextcloud, Seerr | App läser OIDC env; login via Authentik (MFA) |
