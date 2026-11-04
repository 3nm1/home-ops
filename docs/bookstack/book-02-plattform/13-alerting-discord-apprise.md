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

### Grupper i UI (v2.5 — svenska etiketter)

I v2.x är **grupp = en egen monitor-typ**, inte bara ett textfält. Därför hittar du ofta **inte** “Monitor Group” förrän en grupp finns — på svenska heter fältet **Övervakningsgrupp**, och innan du skapat grupper står det: *Inte tillgängligt. Skapa en gruppövervakare först.*

| Begrepp (UI sv) | Engelska / internt | Syfte |
|-----------------|-------------------|--------|
| **Grupp** (monitor-typ) | Type `group` | Tom “mapp”-monitor i listan — kan fällas ihop/ut |
| **Övervakningsgrupp** | Monitor Group / parent | Vilket **Grupp**-objekt en HTTP/ping-monitor **hänger under** |
| **Taggar** | Tags | Filter i sidofältet — oberoende av grupp |
| **Statussidor** | Status Pages | Egen sida med utvalda monitors — inte samma som Grupp |

#### Så skapar du en grupp (steg för steg)

1. **+ Lägg till ny övervakare**
2. **Typ:** välj **Grupp** (inte HTTP/ping).
3. **Vänligt namn:** t.ex. `Homelab — Kritisk` → spara.
4. Öppna en befintlig monitor (HTTP, ping, …) → scrolla till **Övervakningsgrupp** → välj gruppen i listan → spara.
5. Upprepa steg 4 för alla monitors som ska ligga i samma mapp.

**Alternativ (snabbare):** på **Infopanelen**, dra en monitor och släpp den **på** en annan monitor/grupp — då sätts överordnad grupp via drag-and-drop (samma `parent`-relation som ovan).

**Tips:**

- En **Grupp**-monitor behöver oftast **ingen URL** — den aggregerar barn. Notifiering kan sitta på **gruppen** (en Discord-larm per grupp) eller på **varje barn** (mer brus).
- Grupper kan **nästlas** (grupp under grupp) i v2.5+.
- **Taggar** (`infra`, `media`, …) sätter du separat — de ersätter inte Övervakningsgrupp.

### Grupper och taggar (driftsatt lista)

Tillgängliga **taggar:** `dns-internal`, `infra`, `servers`, `k8s`, `media`, `family`, `external`.  
**Grupp** = fältet **Övervakningsgrupp** (kräver **Grupp**-monitorer enligt avsnittet ovan).

#### Grupp-monitorer

| Grupp-monitor (typ Grupp) | Innehåll |
|---------------------------|----------|
| `PacketLab` | *(finns)* — fw, px, HA, docker-sandbox, nas, syslog, Talos ping, DNS extern |
| `Homelab — Kritisk` | Authentik, Internal gateway, K8s API, Longhorn, Nextcloud, Jellyfin (intern) |
| `Homelab — Media` | Sonarr, Radarr, Prowlarr, SABnzbd |
| `Homelab — Extern` | Jellyfin (extern), Seerr, ev. DNS extern |

#### Per monitor — grupp och taggar

| Monitor (vänligt namn) | Övervakningsgrupp | Taggar | Kommentar |
|------------------------|-------------------|--------|-----------|
| PacketLab › fw-core01 (DNS) | `PacketLab` | `dns-internal`, `infra` | |
| PacketLab › docker-sandbox01 (ping) | `PacketLab` | `servers`, `infra` | |
| PacketLab › ha-green01 (http) | `PacketLab` | `servers`, `infra` | |
| PacketLab › px-node01 (ping) | `PacketLab` | `servers`, `infra` | |
| PacketLab › px-node02 (ping) | `PacketLab` | `servers`, `infra` | |
| PacketLab › px-node03 (ping) | `PacketLab` | `servers`, `infra` | |
| PacketLab › px-node04 (ping) | `PacketLab` | `servers`, `infra` | |
| Monitor: DNS extern | `PacketLab` *eller* `Homelab — Extern` | `dns-internal`, `external` | Valfritt vilken grupp |
| nas-core01 | `PacketLab` | `servers`, `infra` | TrueNAS |
| srv-syslog01 | `PacketLab` | `servers`, `infra` | Loki/rsyslog-VM |
| Talos/worker | `PacketLab` | `servers`, `k8s`, `infra` | Ping worker; API separat |
| Authentik | `Homelab — Kritisk` | `k8s`, `infra`, `external` | |
| Internal gateway | `Homelab — Kritisk` | `k8s`, `infra` | t.ex. Grafana via internal gateway |
| Kubernetes API | `Homelab — Kritisk` | `k8s`, `infra` | `192.168.20.150:6443` |
| Longhorn | `Homelab — Kritisk` | `k8s`, `infra` | |
| Nextcloud | `Homelab — Kritisk` | `k8s`, `family` | |
| jellyfin / Jellyfin (intern) | `Homelab — Kritisk` | `k8s`, `media`, `family` | Döp om t.ex. `Jellyfin (internal)` |
| Sonarr | `Homelab — Media` | `k8s`, `media` | |
| Radarr | `Homelab — Media` | `k8s`, `media` | |
| Prowlarr | `Homelab — Media` | `k8s`, `media` | |
| SABnzbd | `Homelab — Media` | `k8s`, `media` | |
| Jellyfin (extern) | `Homelab — Extern` | `k8s`, `media`, `external` | Döp om t.ex. `Jellyfin (extern)` |
| Seerr | `Homelab — Extern` | `k8s`, `media`, `external` | Byt `extern` → taggen `external` |

#### Tagg-regler

| Tagg | Använd när |
|------|------------|
| `infra` | Nät, hypervisor, brandvägg, lagring, loggar, kluster-plattform |
| `servers` | VM/fysisk utanför pod (Proxmox, NAS, syslog, sandbox) |
| `k8s` | Tjänst i Talos/Kubernetes |
| `media` | *arr, Sabnzbd, Jellyfin, Seerr |
| `family` | Nextcloud, intern Jellyfin |
| `external` | Check medvetet “utifrån” / WAN / Cloudflare |
| `dns-internal` | DNS-checks (fw-core01, DNS extern) |

**Konsekvent stavning:** använd gemener (`infra`, `servers`, `external`) — inte `Infra`, `Servers`, `extern`.

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
