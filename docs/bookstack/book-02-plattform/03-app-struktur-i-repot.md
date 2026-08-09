# App-struktur i repot

## Tiers under `kubernetes/apps/`

| Tier | Path | Namespace |
|------|------|-----------|
| Platform | `cert-manager`, `external-secrets`, `flux-system`, `kube-system` | respektive |
| Infrastructure | `network`, `storage`, `security`, `observability` | respektive |
| Media | `media/` | `media` |
| Family | `family/` | `family` |
| Self-hosted | `selfhosted/` | `selfhosted` |
| Test | `default/echo` | `default` |

## Standard app-mapp

```
<app>/
├── ks.yaml                 # Flux Kustomization (refereras från tier-kustomization.yaml)
└── app/
    ├── kustomization.yaml
    ├── helmrelease.yaml    # Huvudmanifest
    ├── externalsecret.yaml
    ├── pvc.yaml
    ├── ocirepository.yaml  # om bjw-s OCI chart
    └── securitypolicy.yaml # om forward-auth behövs
```

## Chart-källor

| Typ | Exempel |
|-----|---------|
| OCI (bjw-s app-template) | Sonarr, Homarr, BookStack |
| Helm repo | Nextcloud, Authentik, Longhorn, Cilium |

## Komponenter

`kubernetes/components/sops/` — ger `cluster-secrets` till alla tiers som inkluderar SOPS-komponenten.

## Lägga till ny app

1. Skapa mapp under rätt tier.
2. Lägg till `ks.yaml` i tierns `kustomization.yaml`.
3. Skapa 1Password-post + `externalsecret.yaml` om secrets behövs.
4. HTTPRoute mot `envoy-internal` (eller external om publikt).
5. Push → Flux deployar.
