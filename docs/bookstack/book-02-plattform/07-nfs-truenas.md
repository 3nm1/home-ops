# NFS på TrueNAS

**Server:** `192.168.20.20`

## Exports

| Export | Path på TrueNAS | Används av |
|--------|-----------------|------------|
| Media library | `/mnt/Backup/data` | Jellyfin, *arr, Sabnzbd, Autoscan, Unpackerr |
| Familj / Nextcloud | `/mnt/NFS/family/nextcloud` | Nextcloud user data |
| Longhorn backup | `/mnt/NFS/longhorn` | Longhorn backups |
| Velero | `/mnt/NFS/velero` | MinIO/Velero backup storage |

## Kubernetes-mönster

**Static PV** för stora NFS-volymar:

```yaml
# nfs-pv.yaml
nfs:
  server: 192.168.20.20
  path: /mnt/NFS/family/nextcloud
```

PVC binder med `volumeName: family-nextcloud-data-nfs`.

## Rättigheter (Nextcloud-lärdom)

TrueNAS kan inte enkelt `chown 33:33` (www-data) på NFS.

**Lösning:** Maproot till root + **init container** som kör `chown 33:33` på mount i podden.

## Velero

Stora NFS-volymar exkluderas ofta från pod-backup — data lever på NAS, inte i etcd/Longhorn.

## Globala NFS-inställningar (TrueNAS)

**System → Services → NFS** (tjänsten, inte en enskild share):

| Inställning | Värde | Varför |
|-------------|-------|--------|
| **Enabled Protocols** | NFSv3, NFSv4 | Longhorn stödjer v4.0–4.2 |
| **Allow non-root mount** | **På** | Longhorn Manager mountar backup-NFS **inifrån podden** (icke-privilegierade portar). Utan detta: `mount.nfs4: Operation not permitted` i Longhorn UI |

Detta påverkar **inte** vanliga Kubernetes NFS-PV (kubelet mountar på noden). Det krävs för **Longhorn backup target**.

## Longhorn backup-share

**Shares → Unix Shares (NFS) →** `/mnt/NFS/longhorn`:

| Inställning | Värde |
|-------------|-------|
| Path | `/mnt/NFS/longhorn` |
| Maproot User / Group | `root` / `root` |
| Networks | `192.168.20.0/24` (Talos-noder) |
| Read Only | Av |

Backup target i klustret (Helm): `nfs://192.168.20.20:/mnt/NFS/longhorn` — se [Longhorn](06-longhorn.md).

### Verifiera mount från klustret

```bash
kubectl exec -n longhorn-system -it \
  $(kubectl get pod -n longhorn-system -l app=longhorn-manager -o name | head -1) \
  -- sh -c 'mkdir -p /tmp/t && mount -t nfs4 -o nfsvers=4.1 192.168.20.20:/mnt/NFS/longhorn /tmp/t && echo OK && umount /tmp/t'
```
