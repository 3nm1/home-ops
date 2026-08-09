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
- Alla 4 noder är control plane **och** kör workloads
- `allowSchedulingOnControlPlanes: true`
- Longhorn, Cilium, Velero → I/O och lease churn

### Åtgärder

1. **Cordon** överbelastade CP-noder tillfälligt
2. **Reboot** noder i ordning (en i taget) — börja med minst kritisk
3. **Minska load** — suspend tunga Flux apps tillfälligt
4. Överväg att flytta tunga workloads från CP till worker-only (långsiktigt)

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

Grafana: `grafana.engstrom.live` — dashboards för klusterövervakning.

## Nextcloud-specifikt

Om cloud.engstrom.live strular men klustret är frisk → se *Nextcloud felsökning*, inte reboot hela klustret.
