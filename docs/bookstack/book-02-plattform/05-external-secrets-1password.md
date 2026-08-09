# External Secrets + 1Password

## Arkitektur

```
1Password (vault) → ClusterSecretStore "onepassword"
                 → ExternalSecret per app
                 → Kubernetes Secret → Pod env/volume
```

## ClusterSecretStore

Definieras i `kubernetes/apps/external-secrets/` — SDK-baserad koppling till 1Password.

## App-exempel (Nextcloud)

```yaml
# externalsecret.yaml
dataFrom:
  - extract:
      key: nextcloud   # 1Password item-namn
```

Genererar `nextcloud-secret` med templated keys (`nextcloud-password`, `postgres-password`, OIDC, …).

## Refresh

`refreshInterval: 1h` — ändringar i 1Password propageras inom en timme (eller tvinga reconcile).

## Reloader

Många controllers har `reloader.stakater.com/auto: "true"` — poddar startas om när secret ändras.

## 1Password-postnamn (urval)

| Item | Appar |
|------|-------|
| `nextcloud` | Nextcloud admin, postgres, OIDC |
| `bookstack` | BookStack DB + OIDC |
| (per app) | Se respektive `externalsecret.yaml` |
