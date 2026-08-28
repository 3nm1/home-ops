# srv-syslog01 drift

Runbook för **srv-syslog01** — central syslog, Promtail, Loki och Grafana. Arkitektur: [Central loggning](../book-02-plattform/10-central-loggning-srv-syslog01.md).

## Snabb hälsokontroll

```bash
df -h /
systemctl is-active rsyslog promtail loki grafana-server
ss -tlpn | grep -E '514|3100|3000|9080'
curl -s http://localhost:3100/ready
ls -lh /var/log/remote/fw-core01.lab.engstrom.live/filterlog.log
```

| Check | OK |
|-------|-----|
| Disk `/` | Minst ~20 % ledigt |
| Alla fyra tjänster | `active` |
| Port 514, 3100, 9080 | LISTEN |
| Loki | `ready` |
| filterlog | MB–hundratals MB, inte GB |

End-to-end:

```bash
logger -t verify-test "runbook check $(date -Is)"
# Sök i Grafana/Loki efter verify-test inom ~30 s
```

---

## Scenario: disk full (100 %)

**Symptom:** rsyslog `write error`, Loki omstartar i loop (`no space left on device`), Promtail kan inte skriva positions-fil, port 3100 nere.

### 1. Bekräfta

```bash
df -h /
df -i
sudo du -xh /var/log/remote --max-depth=2 | sort -h | tail -15
sudo du -sh /var/lib/loki/* 2>/dev/null
```

### 2. Stoppa skrivare

```bash
sudo systemctl stop promtail loki grafana-server
sudo systemctl stop rsyslog syslog.socket
```

`syslog.socket` måste stoppas — annars startar rsyslog om via socket.

### 3. Frigör utrymme

Kolla `chattr` på filterlog:

```bash
sudo lsattr /var/log/remote/fw-core01.lab.engstrom.live/filterlog.log
```

Om **`a`** (append-only):

```bash
sudo chattr -a /var/log/remote/fw-core01.lab.engstrom.live/filterlog.log
```

Nolla eller rotera:

```bash
sudo truncate -s 0 /var/log/remote/fw-core01.lab.engstrom.live/filterlog.log
df -h /
```

Rensa gamla `.gz` / `.backup` om de finns kvar efter misslyckad rotation.

### 4. Starta om (ordning)

```bash
sudo systemctl start syslog.socket rsyslog
sudo systemctl start loki
sleep 3
sudo systemctl start grafana-server promtail
curl -s http://localhost:3100/ready
```

---

## Scenario: utöka VM-disk (Proxmox + LVM)

När Proxmox-disk växts men gästen fortfarande ser gammal LV-storlek:

```bash
lsblk
sudo pvs && sudo vgs && sudo lvs
df -h /
```

Typisk kedja (100 GB disk, partition sda3):

```bash
sudo apt install -y cloud-guest-utils
sudo growpart /dev/sda 3
sudo pvresize /dev/sda3
sudo lvextend -l +100%FREE /dev/ubuntu-vg/ubuntu-lv
sudo resize2fs /dev/mapper/ubuntu--vg-ubuntu-lv
df -h /
```

**Mål efter aug 2026:** ~97 GB root, ~80+ GB ledigt.

---

## Scenario: logrotate failar (`Operation not permitted`)

**Orsak:** `chattr +a` på aktiva loggar eller gamla arkiv; eller `copytruncate` på multi-GB filterlog.

### Engångsstädning

```bash
sudo systemctl stop promtail
sudo systemctl stop rsyslog syslog.socket

sudo chattr -R -a /var/log/remote/
# Radera manuellt trasiga *.log.1, *.backup, dubbla .gz

sudo systemctl start syslog.socket rsyslog promtail
sudo logrotate -f /etc/logrotate.d/remote-syslog
```

Se [Logrotation och integritet](../book-02-plattform/11-loggrotation-och-integritet.md) för mål-config (**inte** `copytruncate` på remote-loggar).

---

## Scenario: Loki crash loop

```bash
sudo journalctl -u loki -n 50 --no-pager
```

| Loggrad | Åtgärd |
|---------|--------|
| `no space left on device` | [Disk full](#scenario-disk-full-100-) |
| WAL/korruption | Stoppa Loki, backup `/var/lib/loki`, ev. rensa WAL (dataförlust — sista utväg) |

Efter disk fix:

```bash
sudo systemctl restart loki
curl -s http://localhost:3100/ready
```

---

## Scenario: Promtail pushar inte

```bash
sudo journalctl -u promtail -n 30 --no-pager
ls -la /tmp/positions.yaml
```

| Problem | Fix |
|---------|-----|
| Loki nere | Fixa Loki först |
| positions-fil | Flytta till `/var/lib/promtail/positions.yaml` i config |
| Rättigheter på loggar | `syslog:adm`, se remote-syslog `create 0640` |

---

## Underhåll — rutin

| Uppgift | Frekvens |
|---------|----------|
| `df -h /` | Veckovis (eller Uptime Kuma/disk-alert) |
| Största remote-loggar | `du` månadsvis |
| `/var/lib/loki` storlek | Månadsvis |
| `logrotate -d` torrkörning | Efter config-ändring |

---

## Relaterade sidor

- [Observability-översikt](../book-02-plattform/09-observability-oversikt.md)
- [Central loggning](../book-02-plattform/10-central-loggning-srv-syslog01.md)
- [Logrotation och integritet](../book-02-plattform/11-loggrotation-och-integritet.md)
- [Klusterhälsa](02-kluster-halsa.md) (kluster-Grafana, Uptime Kuma)
