# Alerting — Discord, Apprise och standarder

Mål: **du ska inte behöva komma ihåg att öppna Loki** — kritiska saker ska till **Discord**. Loggar är forensik när en alert redan pekar dit.

## Tre signalnivåer

| Nivå | Fråga | Verktyg | Discord |
|------|--------|---------|---------|
| Symptom | Når användare tjänsten? | Uptime Kuma | Ja (konfig i UI) |
| Orsak | Pod/disk/etcd/Longhorn? | Prometheus → Alertmanager | Ja (GitOps) |
| Forensik | Vad skrev loggen? | Loki (srv-syslog01) | Sällan (utom få log-alerts på VM) |

## 1Password

Skapa vault-item **`observability-notifications`**:

| Fält | Innehåll |
|------|----------|
| `DISCORD_WEBHOOK_URL` | Full URL: `https://discord.com/api/webhooks/<id>/<token>` |

Samma webhook kan återanvändas i Uptime Kuma och (valfritt) manuellt i Apprise.

**GitOps:** `ExternalSecret` `alertmanager-notifications` → Secret monteras i Alertmanager som fil `discord-webhook-url`.

## Kluster — Alertmanager → Discord

| Path | Syfte |
|------|--------|
| `kubernetes/apps/observability/kube-prometheus-stack/app/externalsecret-alertmanager-notifications.yaml` | Webhook från 1Password |
| `helmrelease.yaml` → `alertmanager.config` | Routing: `critical`/`warning` → Discord; `Watchdog`/`InfoInhibitor` → null |

Efter deploy:

```bash
flux reconcile kustomization kube-prometheus-stack -n observability
kubectl get externalsecret alertmanager-notifications -n observability
kubectl port-forward -n observability svc/kube-prometheus-stack-alertmanager 9093:9093
# http://localhost:9093 — Status, active alerts
```

Test (försiktigt — skickar till Discord):

```bash
kubectl exec -n observability alertmanager-kube-prometheus-stack-0 -- \
  amtool alert add alertname=TestHomelab severity=warning --alertmanager.url=http://127.0.0.1:9093
```

## Kluster — Grafana

`grafana.engstrom.live` har **Loki-datasource** mot `http://srv-syslog01.lab.engstrom.live:3100` — metrics och loggar i samma UI vid incident.

Kräver att Talos-pods når syslog-VM på VLAN 20 (brandväggsregel om den saknas).

## Apprise

`apprise.engstrom.live` är **hub** för tjänster som inte har inbyggt stöd som Alertmanager:

- **Uptime Kuma:** Settings → Notifications → Discord (samma webhook-URL) eller Apprise-URL `discord://…`
- **Skript / manuellt:** `curl -X POST "https://apprise.engstrom.live/notify" -d "urls=discord://…&title=…&body=…"` (om Apprise exponerar notify; annars Discord direkt)

Alertmanager använder **Discord native** (pålitligt). Apprise samlar övriga kanaler så du inte sprider webhook-token i tio UIs.

## Uptime Kuma — minimilista

Lägg monitors (HTTP(S) mot internal gateway eller extern URL):

- Authentik, Jellyfin, Seerr (externa)
- `grafana`, `uptime-kuma`, `envoy-internal` health
- Ping mot `192.168.20.20` (TrueNAS) / syslog-VM om önskat

Notification: **Discord** med samma webhook som ovan.

## Ny “viktig” app — checklista

1. HTTPRoute + Uptime-monitor  
2. ServiceMonitor om appen har metrics  
3. Ev. `PrometheusRule` (pod not ready > 15 min)  
4. Dokumentera URL i BookStack media/selfhosted-lista  

## Relaterat

- [Observability-översikt](09-observability-oversikt.md)
- [OPNsense IPS/IDS och loggar](../../book-03-natverk/04-opnsense-ips-ids-och-loggar.md)
