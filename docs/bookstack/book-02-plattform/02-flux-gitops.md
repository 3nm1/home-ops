# Flux — hur det hänger ihop

## Rot-Kustomization

`kubernetes/flux/cluster/ks.yaml` pekar på `./kubernetes/apps`.

## Per-app

```yaml
# kubernetes/apps/media/sonarr/ks.yaml (exempel)
spec:
  path: ./kubernetes/apps/media/sonarr/app
  targetNamespace: media
  postBuild:
    substituteFrom:
      - kind: Secret
        name: cluster-secrets
  dependsOn:
    - name: external-secrets-stores
```

## Reconcile

```bash
# Hela klustret
flux reconcile source git flux-system -n flux-system
flux reconcile kustomization cluster-apps -n flux-system --with-source

# En app
flux reconcile kustomization sonarr -n flux-system --with-source
```

## Suspend / resume

Använd vid felsökning eller när klustret är överbelastat:

```bash
flux suspend kustomization nextcloud -n flux-system
flux resume kustomization nextcloud -n flux-system
```

## HelmRelease

De flesta appar använder `HelmRelease` med:

- `remediation.retries` vid install/upgrade
- `OCIRepository` (bjw-s app-template) eller `HelmRepository` (upstream charts)

## Git webhook

Flux kan triggas via webhook: `flux-webhook.engstrom.live` (snabbare sync än poll).
