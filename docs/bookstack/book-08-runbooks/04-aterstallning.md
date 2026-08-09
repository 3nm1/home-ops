# Återställning och rebuild

## Filosofi

> Om jag inte kan återskapa hela klustret från Git har något gått fel i designen.

## Vad som finns var

| Data | Plats | Återställning |
|------|-------|---------------|
| Git manifests | GitHub `home-ops` | `git clone` |
| Krypterade secrets | SOPS i Git + age-nyckel | age key säker backup! |
| App secrets | 1Password | Oberoende av kluster |
| Media | TrueNAS NFS | Oberoende av kluster |
| Familjefiler (Nextcloud) | TrueNAS NFS | Oberoende av kluster |
| Longhorn-volymar | På Talos-noder | Longhorn backup → NFS |
| BookStack-innehåll | MariaDB + PVC | Backup PVC/DB |
| etcd state | Talos noder | Kluster "minne" — rebuild = nytt kluster |

## Full kluster-rebuild (översikt)

1. Säkerställ age-nyckel + 1Password + TrueNAS lever
2. Proxmox VMs för Talos — recreate från `talos/talconfig.yaml`
3. Bootstrap (`bootstrap/helmfile`) → Flux
4. Flux synkar `kubernetes/apps/` — allt kommer tillbaka
5. NFS-PV binder automatiskt om samma export paths
6. Verifiera Authentik → OIDC-appar fungerar
7. Importera BookStack-innehåll från `docs/bookstack/` om DB förlorad

## Velero

Backups till MinIO på `192.168.20.20:/mnt/NFS/velero`.

Stora NFS-volymar (media) backas **inte** via Velero — de lever på NAS.

## Nextcloud disaster

1. NFS-data kvar på TrueNAS → användardata säker
2. Recreate PostgreSQL PVC → ny tom DB
3. `occ maintenance:install` eller ren Helm-install
4. OIDC hooks konfigurerar Authentik igen

## Dokumentation

Om BookStack-databasen dör: **detta repo** (`docs/bookstack/`) är backup av dokumentationen.

## age-nyckel

**KRITISKT:** Utan age-nyckeln kan Flux inte dekryptera SOPS. Förvara utanför klustret (password manager, offline backup).
