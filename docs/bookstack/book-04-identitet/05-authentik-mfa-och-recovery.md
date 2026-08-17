# Authentik — MFA och recovery

Dokumenterat aug 2026 efter verifierad drift (MFA-inloggning + lösenordsåterställning).

## Översikt

MFA och recovery styrs i **Authentik login/recovery flows** — inte per app. När det fungerar gäller det för alla OIDC-appar (Nextcloud, Homarr, BookStack, …) och samma identitet vid forward-auth.

```
Inloggning (OIDC / auth.engstrom.live):
  1. Identification (användarnamn/e-post)
  2. Password
  3. Authenticator Validation (MFA)
  4. User Login → redirect till app

Recovery (glömt lösenord):
  1. Identification
  2. E-post med länk
  3. MFA-verifiering
  4. Nytt lösenord → inloggad
```

---

## MFA — obligatorisk för alla

Authentik levererar **inte** MFA enforcement out of the box — det konfigureras i befintliga stages/flows.

### Login-flow (stage bindings)

**Flows and Stages → Flows → `default-authentication-flow` → Stage Bindings**

| Order | Stage |
|-------|-------|
| 10 | Identification |
| 20 | Password |
| **30** | **`default-authentication-mfa-validation`** |
| 100 | User Login |

### MFA-validering (stage)

**Flows and Stages → Stages → `default-authentication-mfa-validation` → Edit**

| Fält | Värde |
|------|-------|
| **Device classes** | TOTP, WebAuthn (rekommenderat) |
| **Not configured action** | **Configure** — tvingar registrering vid första login |
| **Configuration stages** | `default-authenticator-totp-setup`, `default-authenticator-webauthn-setup` |
| (valfritt backup) | `default-authenticator-static-setup` |

| Metod | Användning |
|-------|------------|
| **TOTP** | Authenticator-app (1Password, Aegis, Google Authenticator, …) |
| **WebAuthn** | Passkey / Face ID / Touch ID / YubiKey |
| **Static tokens** | Nödkoder — särskilt för admin |

### Brand

**System → Brands → [auth.engstrom.live]**

| Fält | Värde |
|------|-------|
| Authentication flow | `default-authentication-flow` |

### Beteende

- **Ny användare / utan MFA:** måste registrera MFA innan login slutförs
- **Befintlig användare med MFA:** kod eller passkey krävs varje login
- **OIDC-appar:** ingen extra konfiguration — samma Authentik-flow

### Break-glass (admin)

1. Registrera MFA på admin **innan** enforcement till alla
2. Skapa **static recovery tokens** för admin och spara offline
3. Vid tappad MFA-enhet: **Directory → Users → MFA Authenticators → Delete** — användaren registrerar om vid nästa login

Nextcloud har dessutom lokal break-glass: `https://cloud.engstrom.live/login?direct=1` (lokal admin, inte SSO).

---

## Recovery flow — import krävs

Authentik har **inget färdigt recovery flow** i brand-dropdown förrän ett flow med designation **recovery** skapats/importerats.

### Importera (rekommenderat med MFA)

**Flows and Stages → Flows → Import → Local path**

| Blueprint | Innehåll |
|-----------|----------|
| `example/flows-recovery-email-mfa-verification.yaml` | E-post → MFA → nytt lösenord (**använd denna**) |
| `example/flows-recovery-email-verification.yaml` | Utan MFA (Authentik avråder) |

Skapar flow med slug **`default-recovery-flow`**.

### Obligatorisk justering efter import

Exempel-blueprinten sätter fel authentication-nivå för admin-verktyg (*Create recovery link*).

**Flows and Stages → Flows → `default-recovery-flow` → Edit**

| Fält | Sätt till |
|------|-----------|
| **Authentication** | **No requirement** |

> **Inte** "Require no authentication" — det ger missvisande fel när admin skapar recovery-länk.

### E-poststage

**Stages → `default-recovery-email`**

| Fält | Värde |
|------|-------|
| **Use global settings** | ✅ På |

Använder SMTP från Helm (`smtp-relay.selfhosted.svc.cluster.local:25`, `AUTHENTIK_EMAIL__FROM`).

### Brand

**System → Brands → [auth.engstrom.live]**

| Fält | Värde |
|------|-------|
| Recovery flow | `default-recovery-flow` |

Inloggningssidan visar då **Forgot password?** / glömt lösenord.

---

## Test (checklista)

### SMTP

```bash
kubectl exec -n authentik deploy/authentik-server -- ak test_email mottagare@example.com
```

### MFA

1. Inkognito → `https://cloud.engstrom.live` (eller `https://auth.engstrom.live`)
2. Lösenord → MFA-setup (första gången) eller MFA-kod
3. Verifiera: **Directory → Users → [user] → MFA Authenticators**

### Recovery (användare)

1. Användare med **e-post** ifylld i Authentik
2. *Forgot password?* på login → följ mail-länk
3. Verifiera MFA → sätt nytt lösenord

### Recovery (admin)

**Directory → Users → [user]**

| Åtgärd | När |
|--------|-----|
| **Email recovery link** | Användaren ska få mail |
| **Create recovery link** | Kopiera länk manuellt (support) |

Kräver recovery flow på brand + **Authentication: No requirement**.

---

## Drift — vanliga admin-uppgifter

| Scenario | Åtgärd |
|----------|--------|
| Användare tappat telefon (MFA) | Ta bort MFA Authenticators → användaren registrerar om vid login |
| Glömt lösenord | Email recovery link / Forgot password |
| Låst ute helt | Recovery-länk + ev. ta bort MFA först |
| Ny familjemedlem | Skapa user i Authentik med e-post → första login: lösenord + MFA-setup |

Alla användare som ska kunna återställa lösenord behöver **Email** i Authentik.

---

## Felsökning

| Symptom | Orsak / fix |
|---------|-------------|
| Tom lista under Recovery flow | Importera blueprint — inget `recovery`-flow finns |
| *"brand must have a recovery flow configured"* trots att flow är satt | Flow **Authentication** → **No requirement** |
| Recovery-mail skickas inte | `ak test_email` failar — kolla smtp-relay, `SMTP_FROM` i 1Password |
| MFA krävs inte | Kontrollera stage binding order ~30 och **Not configured action** |
| Recovery failar efter MFA | Använd MFA-blueprinten, inte email-only-varianten |
| Admin recovery link funkar inte | Inloggad admin + fel authentication på recovery flow |

---

## Relaterat

- [Authentik — översikt](01-authentik-oversikt.md) — SMTP, gateways
- [Authentik — branding och flows](04-authentik-branding-flows.md) — brand, svenska flow-titlar
- [OIDC-appar](02-oidc-appar.md) — appar som använder samma login
- [Nextcloud — användare och grupper](../book-06-familj/04-nextcloud-anvandare-grupper-skeleton.md) — onboarding familj
- [SMTP-relay](../book-02-plattform/08-smtp-relay.md) — mailväg för recovery
