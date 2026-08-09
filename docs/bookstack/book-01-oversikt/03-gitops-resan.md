# GitOps-resan

## Flöde

```
Git push → Flux GitRepository → cluster-apps Kustomization
         → per-app ks.yaml → HelmRelease / manifests → Kubernetes
```

Flux jämför kluster med Git var ~1 minut. Vid drift **vinner Git** — manuella ändringar skrivs över vid nästa reconcile.

## Bootstrap → Flux

1. **Bootstrap** (`bootstrap/helmfile.d/`) installerar grundplattform: Cilium, CoreDNS, cert-manager, Flux.
2. **Flux tar över** och synkar `kubernetes/apps/` från Git.

## App-mönster

Varje app har typiskt:

```
kubernetes/apps/<tier>/<app>/
├── ks.yaml              # Flux Kustomization
└── app/
    ├── kustomization.yaml
    ├── helmrelease.yaml # eller OCIRepository + HelmRelease
    ├── externalsecret.yaml
    └── pvc.yaml
```

## Viktiga lärdomar

| Lärdom | Detalj |
|--------|--------|
| Kör inte `helm uninstall` manuellt | Flux återinstallerar — men kan lämna PVC/data i konstigt läge |
| Escapa `${VAR}` i hooks | Flux `postBuild` substituierar — använd `$${OIDC_CLIENT_ID}` i bash-hooks |
| Suspendera Flux vid nödfall | `flux suspend kustomization nextcloud -n flux-system` |
| Renovate | Uppdaterar chart-versioner automatiskt — läs release notes |

## Domän-substitution

`SECRET_DOMAIN` (=`engstrom.live`) kommer från SOPS-krypterad `cluster-secrets` och injiceras i alla manifests via Flux `postBuild.substituteFrom`.

## Namespaces (app-tiers)

| Namespace | Innehåll |
|-----------|----------|
| `kube-system` | Cilium, CoreDNS, GPU operator, Reloader |
| `flux-system` | Flux operator + instance |
| `network` | Envoy, Cloudflare tunnel/DNS |
| `authentik` | SSO |
| `media` | *arr, Jellyfin, automation |
| `family` | Nextcloud |
| `selfhosted` | Homarr, BookStack, m.m. |
| `observability` | Prometheus/Grafana |
| Longhorn/Velero | `longhorn-system`, `storage`, `velero` |
