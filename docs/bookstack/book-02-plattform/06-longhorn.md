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

Mount sker från **longhorn-manager-podden** (inte kubelet). TrueNAS kräver **Allow non-root mount** på tjänsten NFS — se [NFS på TrueNAS](07-nfs-truenas.md#globala-nfs-inställningar-truenas).

Healthy volymer påverkas **inte** om backup target failar; det syns bara under **Backup** i UI.

## Vanliga problem

| Symptom | Möjlig orsak |
|---------|--------------|
| PVC Pending | Nod NotReady, disk full, attach timeout |
| Pod stuck Terminating | Volume detach — kolla Longhorn UI |
| Backup: `Operation not permitted` vid NFS mount | TrueNAS: **Allow non-root mount** av; kolla share `192.168.20.0/24`, Maproot root |
| Backup: `No such file or directory` | Dataset `/mnt/NFS/longhorn` saknas eller fel path i backup target |
| Longhorn bara 3/4 noder | GPU-taint på srv-talos04 — kräver `taintToleration` i Helm (se `kubernetes/apps/storage/longhorn/app/helmrelease.yaml`) |

## Nextcloud

- `nextcloud` PVC — config på Longhorn
- `nextcloud-postgresql` — databas på Longhorn
- `nextcloud-data` — **NFS** (användardata)
