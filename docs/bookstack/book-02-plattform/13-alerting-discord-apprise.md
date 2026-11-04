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

**Routing:** standard `receiver: null` — bara `severity=critical|warning` går till Discord. `info`, `Watchdog`, `CPUThrottlingHigh` (ofta brus på Postgres) tystas medvetet.

### Städa brus (Nextcloud cron)

`KubeJobFailed` för `nextcloud-cron-*` betyder att **gamla failed Jobs** ligger kvar. Efter felsökning:

```powershell
kubectl get jobs -n family | findstr nextcloud-cron
kubectl delete jobs -n family --field-selector status.successful=0
# eller: kubectl delete job nextcloud-cron-29828485 -n family
```

Fixa underliggande cron (Nextcloud `cron.php` / job manifest) så nya körningar lyckas.

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

## Uptime Kuma

**URL:** `https://uptime-kuma.engstrom.live`  
**GitOps:** `kubernetes/apps/observability/uptime-kuma/app/helmrelease.yaml` (image `louislam/uptime-kuma`, data på Longhorn PVC `/app/data`).

### Inställningar (gör först)

| Inställning | Rekommendation |
|-------------|----------------|
| **Notifications** | Discord — samma webhook som Alertmanager; **Down** + **Up again** |
| **Intervall** | 60 s (kritiska), 120–300 s (övriga) |
| **Retries** | 2–3 |
| **Taggar** | `infra`, `k8s`, `media`, `family`, `extern` — för filter i sidofältet |
| **Status Pages** | Valfritt senare (t.ex. bara Jellyfin/Seerr mot familj) |

**Authentik / forward-auth:** många interna URL:er svarar **302/401**, inte 200. Under Advanced: **Accepted Status Codes** `200-399`, eller keyword om du bara vill verifiera att gateway svarar.

**Uppdatering av Kuma i klustret:** använd **inte** knappen *Ny uppdatering* i UI — den uppdaterar bara inuti containern och passar inte GitOps. Bumpa **image tag** i HelmRelease → Flux reconcile (se nedan).

### Grupper i UI (v2.x)

I Uptime Kuma 2.x finns **två** sätt att strukturera — lätt att blanda ihop:

| Begrepp | Var | Syfte |
|---------|-----|--------|
| **Monitor Group** | Fält **Parent Group** / **Group** när du skapar/redigerar en monitor | **Mappar i infopanelen** — kollapsbara block (t.ex. `PacketLab`, `Homelab — Kritisk`). Monitors med **samma grupptext** hamnar i samma mapp. Tomt = “ingen grupp” / root. |
| **Taggar (Tags)** | Separat fält + filter **Taggar** i sidofältet | **Etiketter** — en monitor kan ha flera taggar (`infra`, `media`). Filtrera utan att ändra mappstruktur. |

**Praktiskt:**

1. Skapa grupp genom att sätta **Parent Group** till t.ex. `Homelab — Kritisk` på flera monitors (exakt samma stavning).
2. Ge samma monitor **taggar** för tvärsnittsfilter (t.ex. `k8s` + `family` på Nextcloud).
3. **Status Pages** (menyn *Statussidor*) är **inte** samma som Monitor Group — det är en **egen publik/privat sida** med utvalda monitors och egen URL.

Förslag på gruppnamn (parallellt med er befintliga **PacketLab**):

| Monitor Group | Innehåll |
|---------------|----------|
| `PacketLab` | DNS, fw-core01, px-node01–04, HA, docker-sandbox (befintligt) |
| `Homelab — Kritisk` | Auth, cloud, Jellyfin, Grafana, K8s API |
| `Homelab — Media` | Sabnzbd, Sonarr, Radarr, Prowlarr (representanter) |
| `Homelab — Extern` | Samma hostnames som trafik utifrån (Cloudflare/WAN) |

### Monitor-lista (prioritet)

**Tier 1 — Discord ska väcka dig**

| Monitor | Typ | Mål |
|---------|-----|-----|
| Authentik | HTTPS | `https://auth.engstrom.live` |
| Internal gateway | HTTPS | `https://grafana.engstrom.live` (eller Homarr) |
| Kubernetes API | **Port** / TCP | `192.168.20.150:6443` |
| Nextcloud | HTTPS | `https://cloud.engstrom.live` |
| Jellyfin | HTTPS | `https://jellyfin.engstrom.live` |

**Tier 2 — media-pipeline (en per typ, inte alla *arr)**

| Monitor | HTTPS |
|---------|--------|
| Sabnzbd | `https://sabnzbd.engstrom.live` |
| Sonarr | `https://sonarr.engstrom.live` |
| Radarr | `https://radarr.engstrom.live` |
| Prowlarr | `https://prowlarr.engstrom.live` |

Sonarr4k/Radarr4k/Lidarr/Bazarr/Unpackerr — lägg till vid behov; annars räcker Prometheus.

**Tier 3 — plattform (kompletterar PacketLab)**

| Monitor | Typ | Mål |
|---------|-----|-----|
| TrueNAS | Ping | `192.168.20.20` |
| srv-syslog01 | Ping (+ ev. HTTP) | VM-hostname; valfritt `http://<vm>:3100/ready` (Loki) |
| Longhorn | HTTPS | `https://longhorn.engstrom.live` |

**Tier 4 — extern väg (valfritt)**

| Monitor | HTTPS |
|---------|--------|
| Jellyfin / Seerr | Samma URL som används **utifrån** (via Cloudflare) |

**Undvik dubbeljobb:** ping på alla Proxmox-noder **och** alla Talos-noder — behåll px-nodes + API-VIP räcker oftast.

### Uppgradera image (t.ex. 2.5.0 → 2.5.9)

1. Ändra tag i Git:

   `kubernetes/apps/observability/uptime-kuma/app/helmrelease.yaml` → `tag: "2.5.9"` (pin patch; Renovate kan föreslå nästa patch senare).

2. Deploy:

   ```powershell
   git pull
   flux reconcile kustomization uptime-kuma -n observability --with-source
   kubectl rollout status deploy/uptime-kuma -n observability
   kubectl get pod -n observability -l app.kubernetes.io/instance=uptime-kuma -o jsonpath='{.items[0].spec.containers[0].image}{"\n"}'
   ```

3. I UI: *Settings* → About — bekräfta version **2.5.9**.

Data (monitors, notiser) ligger kvar på PVC. **Recreate**-strategy → kort avbrott under omstart.

**Tag `"2"`** (major only) följer inte alltid senaste patch — **pinna `2.5.9`** (eller `2.5`) om du vill styra exakt.

## Ny “viktig” app — checklista

1. HTTPRoute + Uptime-monitor  
2. ServiceMonitor om appen har metrics  
3. Ev. `PrometheusRule` (pod not ready > 15 min)  
4. Dokumentera URL i BookStack media/selfhosted-lista  

## Relaterat

- [Observability-översikt](09-observability-oversikt.md)
- [OPNsense IPS/IDS och loggar](../../book-03-natverk/04-opnsense-ips-ids-och-loggar.md)
