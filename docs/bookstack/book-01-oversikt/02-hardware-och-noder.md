# Hardware och noder

## Proxmox-värdar

| Värd | Roll | CPU | RAM | GPU | Lagring |
|------|------|-----|-----|-----|---------|
| px-node01 | Proxmox | 1× Xeon E5-2697 v2 | 32 GiB | Quadro T400 | 120 GB + 2× 1 TB |
| px-node02 | Proxmox | 2× Xeon E5-2690 v2 | 32 GiB | — | 120 GB + 2× 1 TB |
| px-node03 | Proxmox | 2× Xeon E5504 | 32 GiB | — | 120 GB + 2× 1 TB |
| px-node04 | Proxmox | 1× Xeon E5-2683 v4 | 48 GiB | P2000 + Tesla K80 | 120 GB + 2× 1 TB |

## Talos-noder (Kubernetes)

Alla fyra kör **control plane + worker** (HA-kluster med 4 CP-noder).

| VM | Proxmox-värd | IP (VLAN 20) | vCPU | RAM | Notering |
|----|--------------|--------------|------|-----|----------|
| srv-talos01 | px-node01 | 192.168.20.151 | 4 | 8 GiB | |
| srv-talos02 | px-node02 | 192.168.20.152 | 4 | 8 GiB | |
| srv-talos03 | px-node03 | 192.168.20.153 | 4 | 8 GiB | |
| srv-talos04 | px-node04 | 192.168.20.154 | 4 | 8 GiB | GPU för Jellyfin |

- **API VIP:** `192.168.20.150`
- **Pod CIDR:** `10.42.0.0/16`
- **Service CIDR:** `10.43.0.0/16`
- **Tidszon:** `Europe/Stockholm`

## GPU / media

`srv-talos04` har NVIDIA GPU (Quadro P2000 m.fl.) och en nod-taint:

```
media.engstrom.live/gpu=true:NoSchedule
```

Jellyfin schemaläggs hit för hårdvarutranskodning.

## Nätverk (fysiskt)

- **OPNsense** — gateway, brandvägg, VLAN-routing
- **Cisco switches** — trunk/access, PoE
- **TrueNAS** — `192.168.20.20` — NFS för media, familj, backup

## Lagring per nod

Talos-VM: ~80 GB system + ~700 GB data (`/var/mnt/longhorn` för Longhorn).

## Control plane på alla noder

`allowSchedulingOnControlPlanes: true` är aktiverat i Talos-patches — CP-noder kör också workloads. Praktiskt i ett litet kluster, men kan ge etcd-prestandaproblem under hög belastning (se runbook *Klusterhälsa*).
