# Central loggning (srv-syslog01)

**srv-syslog01** är en Ubuntu-VM på Proxmox (VLAN 20) som samlar syslog från lab-infrastruktur, skriver till disk och indexerar i Loki för sökning i Grafana.

Konfigurationen ligger **på VM:en** — inte i home-ops Git. Denna sida dokumenterar upplägget så du slipper gissa nästa gång.

## Dataflöde

```
Host (OPNsense, Proxmox, …)
  → UDP/TCP :514
  → rsyslogd
  → /var/log/remote/{hostname}/{program}.log
  → Promtail (tail + labels)
  → Loki :3100
  → Grafana :3000
```

Exempel på sökväg:

```text
/var/log/remote/fw-core01.lab.engstrom.live/filterlog.log
/var/log/remote/px-node01.lab.engstrom.live/messages.log
```

## Tjänster

| Tjänst | systemd | Port | Config |
|--------|---------|------|--------|
| rsyslog | `rsyslog` (+ `syslog.socket`) | 514 | `/etc/rsyslog.conf`, `/etc/rsyslog.d/` |
| Promtail | `promtail` | 9080 | `/etc/promtail/config.yml` |
| Loki | `loki` | 3100 | `/etc/loki/config.yml` (typisk sökväg) |
| Grafana | `grafana-server` | 3000 | `/etc/grafana/` |

Startordning vid omstart:

```bash
sudo systemctl start syslog.socket rsyslog
sudo systemctl start loki
sleep 3
sudo systemctl start grafana-server promtail
```

## Syslog-källor (kända hosts)

Hosts skapar underkataloger under `/var/log/remote/` baserat på syslog-hostnamn:

| Host / roll | Exempel-katalog | Notering |
|-------------|-----------------|----------|
| OPNsense | `fw-core01.lab.engstrom.live/` | `filterlog.log` är volymtung |
| TrueNAS | `nas-core01…` | |
| Proxmox | `px-node01` … `px-node04` | |
| docker-sandbox | `docker-sandbox01…` | |
| Övrigt | `srv-ldap01`, `srv-plex01`, `unifi-controller01` | |

**Talos-noder skickar inte syslog hit än** — se [Observability-översikt](09-observability-oversikt.md).

På varje källa: peka remote syslog till **srv-syslog01** (hostname eller IP i VLAN 20).

## Promtail

Promtail läser filer under `/var/log/remote/` och pushar till `http://localhost:3100/loki/api/v1/push`.

Typiska inställningar (ur er config):

| Inställning | Värde | Kommentar |
|-------------|-------|-----------|
| `clients.url` | `http://127.0.0.1:3100/loki/api/v1/push` | Lokal Loki |
| `positions.filename` | `/tmp/positions.yaml` | **Bör flyttas** till `/var/lib/promtail/positions.yaml` (överlever reboot, undviker full `/tmp`) |
| Host-label | Från katalognamn | Kolla efter trailing space i hostnamn (dubblett-label i Loki) |

### Känd quirk: dubbel host-label

OPNsense kan skicka hostnamn med **trailing space**, t.ex. både `fw-core01.lab.engstrom.live` och `fw-core01.lab.engstrom.live ` som separata labels i Loki. Fix: `pipeline_stages` med `trim`/`regex` i Promtail — valfritt städjobb.

## Loki

| Check | Kommando |
|-------|----------|
| Ready | `curl -s http://localhost:3100/ready` → `ready` |
| Data | `/var/lib/loki/` (WAL, chunks) |

Loki **kräver diskutrymme**. Vid full disk: crash loop, Promtail kan inte pusha — se runbook.

## Grafana (logg-UI)

Grafana på srv-syslog01 är **separat** från kluster-Grafana (`grafana.engstrom.live`):

| | srv-syslog01 | Kluster |
|---|--------------|---------|
| Syfte | Loggsökning (Loki) | Metrics + dashboards |
| URL | Internt `:3000` på VM | `https://grafana.engstrom.live` |
| Auth | Lokal Grafana-admin | 1Password / OIDC |

## Verifiering (end-to-end)

På srv-syslog01:

```bash
# Tjänster
systemctl is-active rsyslog promtail loki grafana-server
ss -tlpn | grep -E '514|3100|3000|9080'
curl -s http://localhost:3100/ready

# Skriv testrad → ska synas i Loki inom ~30 s
logger -t verify-test "e2e test $(date -Is)"
```

I Grafana → Explore → Loki, query:

```logql
{job="syslog"} |= "verify-test"
```

(Exakt `{job=…}` beror på er Promtail-konfig — anpassa label om det skiljer sig.)

## Disk och VM

| Egenskap | Värde (efter aug 2026) |
|----------|------------------------|
| Proxmox-disk | 100 GB |
| Root LV | ~97 GB (`ubuntu-vg/ubuntu-lv`) |
| Största risk | OPNsense `filterlog.log` + Loki-data under `/var/lib/loki` |

Utökning av disk: Proxmox resize → `growpart` → `pvresize` → `lvextend` → `resize2fs`. Se [srv-syslog01 drift](../../book-08-runbooks/06-srv-syslog01-drift.md).

## Relaterade sidor

- [Observability-översikt](09-observability-oversikt.md)
- [Logrotation och integritet](11-loggrotation-och-integritet.md)
- [srv-syslog01 drift (runbook)](../../book-08-runbooks/06-srv-syslog01-drift.md)
