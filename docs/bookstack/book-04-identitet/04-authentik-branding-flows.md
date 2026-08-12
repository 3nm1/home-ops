# Authentik — branding och flows

Dokumenterat aug 2026 för *Engströms hemmalabb*.

## Fil-lagring (Customization → Files)

Authentik 2026.x kräver persistent volym på **`/data`** (med `/data/media` inuti) för uppladdning av logo, favicon och filhantering i UI.

Utan detta: *"configured file backend does not support file management"*.

### GitOps

| Resurs | Värde |
|--------|-------|
| PVC | `authentik-data` (2Gi, Longhorn) |
| Mount | `/data` på server + worker |
| Ägare | UID/GID 1000 (`fsGroup: 1000`) |

Repo: `kubernetes/apps/security/authentik/app/pvc.yaml` + `helmrelease.yaml`.

### Verifiera

```bash
kubectl exec -n authentik deploy/authentik-server -- ls -la /data/media
```

---

## Brand — grundinställningar

**System → Brands → [brand för auth.engstrom.live]**

| Fält | Exempel |
|------|---------|
| Brand name | Engströms hemmalabb |
| Title | Engströms hemmalabb |
| Domain | `auth.engstrom.live` |
| Logo / Favicon | Uppladdade via Files |
| Authentication flow | `default-authentication-flow` (eller klon) |

---

## Mörkt tema (Attributes)

Under **Other global settings → Attributes** — YAML, inte `key = value`:

```yaml
settings:
  theme:
    base: dark
  locale: en
```

| Värde | Effekt |
|-------|--------|
| `dark` | Tvinga mörkt tema |
| `light` | Ljust |
| `automatic` | Följ webbläsaren (default) |

**Locale:** Svenska (`sv`) finns i Authentik men är ~3% översatt — de flesta systemtexter förblir engelska. Sätt svenska texter i **flows** istället (nedan).

---

## Custom CSS

**Brand settings → Custom CSS** (separat fält, inte Attributes).

Authentik bygger på Patternfly — använd CSS-variabler (`--ak-*`, `--pf-global--*`) istället för hårdkodade färger.

Minimal mörk grund:

```css
:root,
html[data-theme="dark"] {
  --ak-global--BackgroundColor--100: #1a1d21;
  --ak-global--BackgroundColor--200: #21252b;
  --ak-global--Color--100: #e8eaed;
  --ak-global--link--Color: #7cb8ff;
}

ak-flow-executor::part(main) {
  border-radius: 12px;
}
```

Mer: [Authentik Custom CSS](https://docs.goauthentik.io/brands/custom-css/)

---

## Flows — svenska texter

Systemtexter (knappar som "Log in") översätts via locale — svagt på svenska. **Flow Title** och **Prompt labels** är helt fria.

### Viktiga flows

| Slug | Användning |
|------|------------|
| `default-authentication-flow` | Inloggning |
| `default-invalidation-flow` | Utloggning |
| `default-recovery-flow` | Glömt lösenord |

Koppla under **System → Brands** (Authentication flow, Invalidation flow, Recovery flow).

### Snabbaste förbättringen

1. **Flows and Stages → Flows →** `default-authentication-flow` → **Edit**
2. Sätt **Title**, t.ex. `Välkommen till Engströms hemmalabb`
3. Title visas som rubrik och följer **inte** språkpaket

### Prompts (egna etiketter)

**Flows and Stages → Prompts** — redigera Label och Placeholder per fält.

Typ **Static** i en Prompt stage ger instruktionstext utan input.

### Applikationsnamn vid OIDC-login

Texten *"Login to continue to …"* kommer från Authentik. Appnamnet efter styrs av **Applications → [app] → Name** (t.ex. `Familjmolnet` istället för `Nextcloud`).

---

## OIDC-credentials — källan

| Fråga | Svar |
|-------|------|
| Var skapas Client ID/Secret? | **Authentik** (Provider) |
| Var lagras de för Nextcloud? | **1Password** → `nextcloud-secret` |
| Vanligt fel | Mismatch → *Client ID is missing or invalid* |

Efter ändring i 1Password:

```bash
flux reconcile externalsecret nextcloud -n family --force
```

Uppdatera provider i Nextcloud (eller vänta på pod restart + `before-starting`-hook).

---

## Användare och grupper

| Uppgift | Var |
|---------|-----|
| Skapa användare | Authentik → Directory → Users |
| Grupp `Familj` | Authentik → Directory → Groups |
| App-access | Applications → Nextcloud → bindings |
| Nextcloud-grupp (auto) | Group provisioning vid login |

Se även [Nextcloud — användare, grupper och skeleton](../book-06-familj/04-nextcloud-anvandare-grupper-skeleton.md).
