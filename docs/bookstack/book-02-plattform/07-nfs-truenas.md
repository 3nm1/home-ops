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
