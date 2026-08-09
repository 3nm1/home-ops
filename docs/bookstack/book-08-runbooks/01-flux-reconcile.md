# Flux reconcile

## Tvinga sync från Git

```bash
# Git source
flux reconcile source git flux-system -n flux-system

# Hela app-trädet
flux reconcile kustomization cluster-apps -n flux-system --with-source

# En specifik app
flux reconcile kustomization nextcloud -n flux-system --with-source
```

## Status

```bash
flux get kustomizations -A
flux get helmreleases -A
```

## Suspend / resume

```bash
flux suspend kustomization <name> -n flux-system
flux resume kustomization <name> -n flux-system
```

Använd vid:
- Kluster överbelastat (etcd timeout)
- Manuell felsökning utan att Flux skriver över

## HelmRelease fastnat

```bash
flux reconcile helmrelease nextcloud -n family --force
kubectl describe helmrelease nextcloud -n family
```

## External Secrets

```bash
kubectl get externalsecrets -A
kubectl describe externalsecret nextcloud -n family
```

## GitOps-regel

Om du fixat något manuellt i klustret — **commita motsvarande ändring till Git** annars försvinner fixen vid nästa reconcile.
