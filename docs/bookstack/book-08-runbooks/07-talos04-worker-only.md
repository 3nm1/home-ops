# srv-talos04: worker-only

Runbook för **srv-talos04** som ren worker-nod (GPU / Jellyfin).

Repot: `talos/talconfig.yaml` — `controlPlane: false`, ingen API-VIP, GPU-schematic i `schematic-gpu.yaml`.

## Målbild

| Nod | Roll |
|-----|------|
| srv-talos01–03 | Control plane + worker |
| srv-talos04 | **Worker only** — GPU |

- **API VIP:** `192.168.20.150` (talos01–03)
- **etcd:** 3 medlemmar (kvorum 2/3)

## GPU-schematic (talos04)

| | CP-noder (talos01–03) | GPU worker (talos04) |
|--|----------------------|----------------------|
| Schematic | `schematic.yaml` | `schematic-gpu.yaml` |
| Hash (aug 2026) | `e8df334d…` | **`6cbb524…`** |
| NVIDIA | — | `nonfree-kmod-nvidia-lts`, `nvidia-container-toolkit-lts` |

**`-lts` fungerar med Talos v1.13.6.** Install kan ta flera minuter — vänta innan du byter schematic.

Regenerera efter ändring i `schematic-gpu.yaml`:

```bash
curl -s -X POST -H "Content-Type: text/plain" \
  --data-binary @schematic-gpu.yaml https://factory.talos.dev/schematics
# → uppdatera talosImageURL för srv-talos04 i talconfig.yaml
```

Verifiera på nod:

```bash
talosctl -n 192.168.20.154 get extensions
# ska visa nonfree-kmod-nvidia-lts och schematic 6cbb524…
```

## CP → worker (levande kluster)

**Kräver reset** — `apply-config reboot` utan reset behåller `type: controlplane` och promotar etcd igen.

### Förutsättningar

- Longhorn volymer mestadels `healthy`
- `talosctl --nodes 192.168.20.150 health` OK
- **`talconfig.yaml` committad lokalt** — `controlPlane: false` + rätt schematic **innan** `talhelper genconfig`

### 1. etcd-snapshot

```bash
talosctl -n 192.168.20.151 etcd snapshot /tmp/etcd-backup-$(date +%F).db
```

### 2. Longhorn evict (valfritt)

```bash
kubectl patch nodes.longhorn.io srv-talos04 -n longhorn-system --type=merge \
  -p '{"spec":{"evictionRequested":true,"allowScheduling":false}}'
```

### 3. Cordon + drain

```bash
kubectl cordon srv-talos04
kubectl drain srv-talos04 --ignore-daemonsets --delete-emptydir-data --force --grace-period=120
```

Avbryt (`Ctrl+C`) om drain fastnar på `instance-manager` (PDB).

### 4. Lämna etcd

```bash
talosctl -n 192.168.20.154 etcd leave
talosctl -n 192.168.20.151 etcd members   # ska vara 3
```

### 5. Generera config — verifiera worker

```bash
cd talos
talhelper genconfig
grep "type:" clusterconfig/kubernetes-srv-talos04.yaml | head -1
# MÅSTE: type: worker
```

### 6. Reset + apply (maintenance)

```bash
talosctl -n 192.168.20.154 reset --reboot --graceful=false
```

Om boot disk saknas efter reset — boota **GPU-ISO** i Proxmox:

```
https://factory.talos.dev/image/6cbb52469113114e47c80217d808377a5bbc346de554f8ca8d52b3e897925e56/v1.13.6/noinsecure-amd64.iso
```

När maintenance visar `192.168.20.154`:

```bash
talosctl apply-config -n 192.168.20.154 \
  -f clusterconfig/kubernetes-srv-talos04.yaml \
  --insecure --mode=auto
```

Ta bort ISO och sätt boot order till disk efter install.

### 7. Kubernetes + Longhorn

```bash
kubectl delete node srv-talos04   # om gammal CP-post finns
kubectl get nodes -w
kubectl uncordon srv-talos04
kubectl patch nodes.longhorn.io srv-talos04 -n longhorn-system --type=merge \
  -p '{"spec":{"allowScheduling":true,"evictionRequested":false}}'
```

### 8. GPU labels/taints

Ska komma från `patches/nodes/srv-talos04-nvidia.yaml`. Verifiera:

```bash
kubectl get node srv-talos04 --show-labels | tr ',' '\n' | grep nvidia
kubectl get node srv-talos04 -o jsonpath='{.spec.taints}{"\n"}'
```

Om saknas efter apply — tillfällig fix:

```bash
kubectl label node srv-talos04 nvidia.com/gpu.present=true media.engstrom.live/gpu-transcode=true
kubectl taint node srv-talos04 media.engstrom.live/gpu=true:NoSchedule
kubectl rollout restart deployment gpu-operator -n gpu-operator
```

Permanent: `just talos apply-node 192.168.20.154 reboot` (efter korrekt genconfig).

## Verifiering

```bash
kubectl get node srv-talos04                    # ROLES: <none> (worker — normalt)
talosctl -n 192.168.20.154 get machineconfig -o yaml | grep "type:"  # worker
kubectl get pods -n kube-system --field-selector spec.nodeName=srv-talos04
# INTE kube-apiserver / scheduler / controller-manager
talosctl -n 192.168.20.151 etcd members       # 3 medlemmar
kubectl describe node srv-talos04 | grep nvidia.com/gpu
kubectl get pods -n media -l app.kubernetes.io/name=jellyfin -o wide
```

## just-syntax

```bash
just talos apply-node 192.168.20.154 reboot   # rätt
just talos apply-node 192.168.20.154 mode=auto  # FEL
```

## Vanliga misstag

| Misstag | Konsekvens |
|---------|------------|
| `controlPlane: true` i talconfig vid genconfig | `type: controlplane`, etcd rejoin |
| Apply utan reset vid rollbyte | CP kvar, etcd promotar igen |
| `git checkout` under install | Fel schematic i repot vs kluster |
| Radera inte ISO efter maintenance boot | Boot loop eller fel version |
