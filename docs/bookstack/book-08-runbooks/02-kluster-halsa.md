# Klusterhälsa

## Snabb check

```bash
kubectl get nodes
kubectl get pods -A | grep -v Running
talosctl --nodes 192.168.20.150 health
```

## etcd (vanlig pain point)

Symptom:
- API timeouts
- Flux reconcile timeout
- Talos markerar etcd **Fail** trots `status OK`

Orsaker i litet HA-kluster:
- talos01–03 är control plane **och** kör workloads (`allowSchedulingOnControlPlanes: true`)
- talos04 är worker-only — tunga GPU/media-workloads bör i första hand hamna där

### Åtgärder

1. **Cordon** överbelastade CP-noder tillfälligt
2. **Reboot** noder i ordning (en i taget) — börja med minst kritisk. Planerat Proxmox-underhåll (RAM, kernel): se [Planerat Proxmox-underhåll](05-planerat-proxmox-underhall.md)
3. **Minska load** — suspend tunga Flux apps tillfälligt
4. Överväg att flytta tunga workloads från CP-noder till **srv-talos04** (worker-only)
5. Migrera talos04 till worker-only om den fortfarande kör CP: se [srv-talos04 worker-only](07-talos04-worker-only.md)

### etcd status

```bash
talosctl --nodes 192.168.20.151 etcd status
talosctl --nodes 192.168.20.151 etcd alarm list
```

## Longhorn

```bash
kubectl get pods -n longhorn-system
# UI: longhorn.engstrom.live
```

PVC Pending → kolla nod Ready, disk space, volume attachment events.

## Nätverk

```bash
kubectl get gateway -n network
kubectl get httproute -A
```

## Observability

| Verktyg | URL | Syfte |
|---------|-----|--------|
| Grafana (kluster) | `grafana.engstrom.live` | Metrics, dashboards (Prometheus) |
| Uptime Kuma | `uptime-kuma.engstrom.live` | HTTP/ping-checks |
| srv-syslog01 | VM internt `:3000` / syslog `:514` | Centrala loggar (Loki) — **inte** i klustret |

Översikt: [Observability](../book-02-plattform/09-observability-oversikt.md).

**Loggserver nere / disk full?** → [srv-syslog01 drift](06-srv-syslog01-drift.md) (inte kluster-reboot).

## Nextcloud-specifikt

Om cloud.engstrom.live strular men klustret är frisk → se *Nextcloud felsökning*, inte reboot hela klustret.
