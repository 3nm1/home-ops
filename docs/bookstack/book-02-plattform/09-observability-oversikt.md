# Observability — översikt

Home labbet har **tre separata observability-spår**. De kompletterar varandra men körs medvetet på olika ställen.

## Tre spår

| Spår | Var | Verktyg | Syfte |
|------|-----|---------|--------|
| **Metrics** | Kubernetes (`observability`) | Prometheus, Grafana, Alertmanager | CPU, minne, disk, pod-status, Cilium, Longhorn m.m. |
| **Loggar** | VM **srv-syslog01** (utanför klustret) | rsyslog, Promtail, Loki, Grafana | Central syslog från brandvägg, Proxmox, NAS, m.fl. |
| **Uptime** | Kubernetes (`observability`) | Uptime Kuma | HTTP/ping-checks mot tjänster och värdar |

**Princip:** Metrics och uptime hör till klustret (GitOps, Longhorn, samma ingress-mönster). Loggar stannar på en dedikerad VM — stora syslog-volymer och Loki-WAL ska inte konkurrera med etcd/Longhorn.

## Arkitektur (förenklad)

```
┌─────────────────────────────────────────────────────────┐
│  Kubernetes (Talos)                                     │
│  kube-prometheus-stack  →  grafana.engstrom.live        │
│  uptime-kuma            →  uptime-kuma.engstrom.live    │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  srv-syslog01 (Proxmox VM, VLAN 20)                     │
│  syslog :514 → filer → Promtail → Loki → Grafana :3000  │
└─────────────────────────────────────────────────────────┘
         ▲
         │ UDP/TCP 514
   OPNsense, Proxmox, TrueNAS, docker-sandbox, …
```

Se [Central loggning (srv-syslog01)](10-central-loggning-srv-syslog01.md) för dataflöde och hosts.

## Kluster — metrics (kube-prometheus-stack)

| Egenskap | Värde |
|----------|-------|
| GitOps | `kubernetes/apps/observability/kube-prometheus-stack/` |
| URL | `https://grafana.engstrom.live` (envoy-internal) |
| Namespace | `observability` |
| Retention | Prometheus ~14 dagar (Longhorn PVC) |
| Scraping | ServiceMonitors/PodMonitors i hela klustret |

Grafana-admin: 1Password-item `grafana` → ExternalSecret.

**Inte i kluster-Grafana (än):** Loki-datasource från srv-syslog01. Loggsökning sker idag i **Grafana på srv-syslog01** (`:3000` internt). Framtida förbättring: lägg till Loki som datasource i kluster-Grafana.

## Kluster — uptime (Uptime Kuma)

| Egenskap | Värde |
|----------|-------|
| GitOps | `kubernetes/apps/observability/uptime-kuma/` |
| URL | `https://uptime-kuma.engstrom.live` |
| Image | `louislam/uptime-kuma:2` |
| Data | Longhorn PVC → `/app/data` |

Migrerad från **docker-sandbox** aug 2026. Docker-sandbox kör inte längre parallell Prometheus/Grafana/Uptime Kuma.

Flux-reconcile:

```bash
flux reconcile kustomization uptime-kuma -n observability
```

## srv-syslog01 — loggar

Extern Ubuntu-VM som samlar syslog från infrastruktur **utanför** Talos. Konfiguration lever på VM (inte i home-ops Git).

| Tjänst | Port | Roll |
|--------|------|------|
| rsyslog | 514 | Tar emot remote syslog |
| Promtail | 9080 | Skickar loggfiler till Loki |
| Loki | 3100 | Lagring och index |
| Grafana | 3000 | Loggsökning (Loki-datasource) |

Detaljer: [Central loggning](10-central-loggning-srv-syslog01.md), [Logrotation och integritet](11-loggrotation-och-integritet.md).

## Vad som *inte* skickar syslog än

| Källa | Status |
|-------|--------|
| Talos-noder (srv-talos01–04) | **Ej konfigurerade** — planerad förbättring |
| Kubernetes-pods | Loggar via kluster/stack, inte central syslog |

## Konsolidering (aug 2026)

| Plats | Före | Efter |
|-------|------|-------|
| docker-sandbox | Prometheus, Grafana, Alertmanager, node-exporter, cAdvisor, Uptime Kuma | **Stängt** (utom ev. globalping-probe) |
| Kluster | kube-prometheus-stack | **Kanonical** för metrics |
| Kluster | — | **Uptime Kuma** (ny) |
| srv-syslog01 | rsyslog + Loki | **Oförändrat** — canonical för syslog/loggar |

## Relaterade sidor

- [Central loggning (srv-syslog01)](10-central-loggning-srv-syslog01.md)
- [Logrotation och integritet](11-loggrotation-och-integritet.md)
- Runbook: [srv-syslog01 drift](../../book-08-runbooks/06-srv-syslog01-drift.md)
- Runbook: [Klusterhälsa](../../book-08-runbooks/02-kluster-halsa.md) (Grafana, Uptime Kuma)
