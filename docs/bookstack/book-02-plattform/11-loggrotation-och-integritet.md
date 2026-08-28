# Loggrotation och integritet

srv-syslog01 lagrar syslog **på disk** innan Promtail skickar till Loki. Utan rotation och rimlig disk växer filer — särskilt OPNsense **filterlog** — tills hela systemet stoppar (Loki crash loop, Promtail kan inte skriva positions-fil).

## Två logrotate-filer

| Fil | Roterar | Frekvens |
|-----|---------|----------|
| `/etc/logrotate.d/rsyslog` | Lokala `/var/log/syslog`, `auth.log`, … | Veckovis |
| `/etc/logrotate.d/remote-syslog` | **`/var/log/remote/*/*.log`** | Daglig + storleksgräns |

Blanda inte ihop dem — filterlog-problemet aug 2026 var **remote-syslog**, inte rsyslog-blocket.

## Rekommenderad `/etc/logrotate.d/remote-syslog`

Efter felsökning aug 2026 — **ingen `copytruncate`** på stora filer (kopierar hela filen innan truncate → disk-explosion vid multi-GB filterlog).

```text
/var/log/remote/*/*.log {
    daily
    rotate 7
    size 200M
    missingok
    notifempty
    compress
    delaycompress
    create 0640 syslog adm
    sharedscripts
    postrotate
        /usr/lib/rsyslog/rsyslog-rotate
    endscript
    su root adm
}
```

| Direktiv | Varför |
|----------|--------|
| `size 200M` | OPNsense filterlog kan bli GB på timmar; `daily` alone räcker inte |
| `create` + `postrotate` + `rsyslog-rotate` | Standard rotation — rsyslog öppnar ny fil (inte copytruncate) |
| `rotate 7` | ~7 dagars historik; justera efter behov/disk |
| `su root adm` | Logrotate behöver rättigheter att hantera syslog-filer |

### Timvis körning

Utöver daglig cron: **`/etc/cron.hourly/remote-syslog`** som kör:

```bash
/usr/sbin/logrotate /etc/logrotate.d/remote-syslog
```

Så triggas `size 200M` oftare än en gång per dygn.

Testa config (torrkörning):

```bash
sudo logrotate -d /etc/logrotate.d/remote-syslog
```

## Lokala loggar — `/etc/logrotate.d/rsyslog`

Behåll Ubuntu-standard med explicit `su root adm`:

```text
/var/log/syslog
/var/log/mail.log
/var/log/kern.log
/var/log/auth.log
/var/log/user.log
/var/log/cron.log
{
    su root adm
    rotate 4
    weekly
    missingok
    notifempty
    compress
    delaycompress
    sharedscripts
    postrotate
        /usr/lib/rsyslog/rsyslog-rotate
    endscript
}
```

## `chattr` — integritet vs drift

Historiskt har **`chattr +a`** (append-only) använts för att skydda loggar mot tampering:

| Flagga | Effekt |
|--------|--------|
| `+a` | Endast append tillåtet — **truncate, rm, logrotate blockeras** |
| `+i` | Immutable — inga ändringar alls |

**Lärdom aug 2026:** `+a` på **`filterlog.log`** gjorde att logrotate och manuell `truncate` misslyckades → 6 GB fil → 100 % disk → Loki nere.

### Policy (rekommenderad)

| Objekt | `+a`? |
|--------|-------|
| Aktiva `.log` som ska roteras (filterlog) | **Nej** |
| Arkiverade audit-/compliance-loggar (efter rotation) | Ev. ja — **efter** att de blivit `.gz` och inte ska roteras igen |
| Hela `/var/log/remote/` katalogträd | **Nej** — blockerar städning |

Kolla flaggor:

```bash
sudo lsattr /var/log/remote/fw-core01.lab.engstrom.live/filterlog.log
sudo lsattr -R /var/log/remote/ | grep '\----a'
```

Ta bort append-only innan rotation/städning:

```bash
sudo chattr -a /path/to/file
# Rekursivt på gamla arkiv:
sudo chattr -R -a /var/log/remote/
```

## OPNsense filterlog

Största diskäten:

```bash
sudo du -xh /var/log/remote --max-depth=2 | sort -h | tail -10
```

Långsiktiga alternativ (utöver rotation):

- Minska filterlog-nivå på OPNsense
- Dedikerad retention i rsyslog (drop/filter regler)
- Separat volym för `/var/log/remote` (framtida)

## Loki-retention

Loki-data under `/var/lib/loki/` växer oberoende av textloggar. Övervaka:

```bash
sudo du -sh /var/lib/loki/*
df -h /
```

Konfigurera retention i Loki-config om disk återigen blir trång.

## Kvarstående städning (apr–aug 2026 skuld)

Om `logrotate -f` ger **Operation not permitted** på gamla `*.1.gz`:

1. Gamla rotationer har troligen fortfarande `+a`
2. Kör `chattr -R -a /var/log/remote/`
3. Radera föråldrade `.backup`, dubbla `.gz` manuellt
4. Rensa `/var/lib/logrotate/status` om nödvändigt (försiktigt)
5. Kör `logrotate -f` igen

## Relaterade sidor

- [Central loggning](10-central-loggning-srv-syslog01.md)
- [srv-syslog01 drift (runbook)](../../book-08-runbooks/06-srv-syslog01-drift.md)
