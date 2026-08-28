# srv-talos04: worker-only

Runbook för att **demota** `srv-talos04` från control plane till ren worker-nod.

Repot (`talos/talconfig.yaml`) har `controlPlane: false` och **ingen API-VIP** på talos04. Detta dokument beskriver hur du applicerar ändringen på det **levande** klustret.

## Målbild

| Nod | Roll |
|-----|------|
| srv-talos01–03 | Control plane + worker (`allowSchedulingOnControlPlanes: true`) |
| srv-talos04 | **Worker only** — GPU, Jellyfin, tunga workloads |

- **API VIP:** `192.168.20.150` (talos01–03)
- **etcd:** 3 medlemmar (kvorum 2/3)

## Förutsättningar

- Alla Longhorn-volymer `healthy`
- Longhorn-manager `1/1` på talos01–03
- `talosctl --nodes 192.168.20.150 health` grön
- Planerat underhållsfönster (~30–60 min)

## 1. etcd-snapshot

```bash
talosctl -n 192.168.20.151 etcd snapshot /tmp/etcd-backup-$(date +%F).db
```

## 2. Longhorn: evict replikor från talos04 (valfritt)

```bash
kubectl patch nodes.longhorn.io srv-talos04 -n longhorn-system --type=merge \
  -p '{"spec":{"evictionRequested":true,"allowScheduling":false}}'
```

Vänta tills replikor flyttats. Kolla i Longhorn UI eller:

```bash
kubectl get replicas.longhorn.io -n longhorn-system \
  -o custom-columns=NAME:.metadata.name,NODE:.spec.nodeID,STATE:.status.currentState \
  | grep srv-talos04
```

## 3. Cordon och drain

```bash
kubectl cordon srv-talos04
kubectl drain srv-talos04 \
  --ignore-daemonsets \
  --delete-emptydir-data \
  --force \
  --grace-period=120
```

Drain kan fastna på `instance-manager` (PDB) — avbryt med `Ctrl+C` om resten är evicted.

## 4. Lämna etcd

```bash
talosctl -n 192.168.20.154 etcd leave
talosctl -n 192.168.20.151 etcd members
```

talos04 ska **inte** finnas kvar i medlemslistan.

## 5. Generera och applicera worker-config

```bash
cd talos
talhelper genconfig
just talos apply-node 192.168.20.154 mode=auto
```

Om rollbyte kräver reset (Talos rekommenderar detta vid CP → worker):

```bash
talosctl -n 192.168.20.154 reset --reboot --graceful=false
# När noden är i maintenance:
just talos apply-node 192.168.20.154 mode=auto
```

**Obs:** Reset wipear systemdisken. Longhorn-data på `/var/mnt/longhorn` ligger på `!system_disk` (UserVolumeConfig) och bör överleva, men räkna med att replikor rebuildar om något går fel.

## 6. Städa Kubernetes-registrering

Om gammal nod-post finns kvar efter reset:

```bash
kubectl delete node srv-talos04
kubectl get node srv-talos04 -w
```

## 7. Efter join

```bash
kubectl uncordon srv-talos04
kubectl patch nodes.longhorn.io srv-talos04 -n longhorn-system --type=merge \
  -p '{"spec":{"allowScheduling":true,"evictionRequested":false}}'
talosctl -n 192.168.20.150 health
```

## Verifiering

```bash
kubectl get node srv-talos04
# ROLES ska INTE innehålla control-plane

kubectl get pods -n kube-system --field-selector spec.nodeName=srv-talos04
# Ska INTE ha kube-apiserver, kube-scheduler, kube-controller-manager

kubectl get pods -n media -l app.kubernetes.io/name=jellyfin -o wide
# Ska landa på srv-talos04 (nodeSelector)
```

## Vid problem

| Problem | Åtgärd |
|---------|--------|
| `etcd leave` misslyckas | `talosctl -n 192.168.20.151 etcd remove-member <ID>` från healthy CP |
| Nod joinar inte | Kolla `talosctl -n 192.168.20.154 dmesg`, applicera config igen |
| Longhorn degraded efter reset | Vänta 15–30 min; radera inte replikor manuellt |
| Jellyfin inte på talos04 | Kolla GPU-taint och nodeSelector i `kubernetes/apps/media/jellyfin/` |
