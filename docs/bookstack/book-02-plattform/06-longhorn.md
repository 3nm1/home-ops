# Longhorn

Distribuerat block storage för Kubernetes — **default StorageClass**.

## Användning

| Användning | Exempel |
|------------|---------|
| App-config / DB | Nextcloud config-PVC, PostgreSQL, MariaDB |
| **Inte** stora mediebibliotek | Media och familjdata på NFS |

## Inställningar

- **Replika:** 2
- **Data path på nod:** `/var/mnt/longhorn` (Talos patch)
- **UI:** `longhorn.engstrom.live`

## Backup

Longhorn backup target: `nfs://192.168.20.20:/mnt/NFS/longhorn`

## Vanliga problem

| Symptom | Möjlig orsak |
|---------|--------------|
| PVC Pending | Nod NotReady, disk full, attach timeout |
| Pod stuck Terminating | Volume detach — kolla Longhorn UI |

## Nextcloud

- `nextcloud` PVC — config på Longhorn
- `nextcloud-postgresql` — databas på Longhorn
- `nextcloud-data` — **NFS** (användardata)
