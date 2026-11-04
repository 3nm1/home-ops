# OPNsense — IPS/IDS och loggning

Perimeter-säkerhet för tjänster som når **internet** (Jellyfin, Seerr, Authentik, mail, Cloudflare-tunnel) ska bygga på **lager**, inte ett enda verktyg i Kubernetes.

## Försvar i lager (er setup)

```
Internet
  → Cloudflare (DNS, proxy/WAF där det passar)
  → OPNsense WAN (NAT, brandvägg, Suricata IPS/IDS)
  → VLAN 20 (Talos, gateways)
  → Envoy (internal / external)
  → App (Authentik, OIDC, forward-auth)
```

**Wazuh/SIEM i klustret** ersätter inte detta — ni har redan **syslog → srv-syslog01 → Loki** för korrelation och **Prometheus/Discord** för drift.

## IPS vs IDS på OPNsense (Suricata)

| Läge | Beteende | Homelab-tips |
|------|----------|----------------|
| **IDS** | Detektera, logga, blockera inte (eller begränsat) | Bra **start** på WAN — lär mönster utan att slå ut legit trafik |
| **IPS (inline)** | Blockera enligt regler | Inför **efter** tuning; falska positiva på HTTPS/QUIC/game-traffic är vanliga |

Rekommenderad ordning:

1. **IDS på WAN** — ET Open / OPNsense-regler, uppdatera regelset veckovis.  
2. Granska **Suricata-alerts i Loki** (se nedan) — veckovis till det blir rutin via Discord-alert.  
3. **IPS** på WAN för tydliga hot (tor nodes, known C2) när du accepterar risken för false positives.  
4. **Intern IPS** (VLAN 10 → 20) endast om du misstänker komprometterade klienter — IoT ska redan vara isolerat (VLAN 40).

## Loggar till er befintliga pipeline

OPNsense skickar redan syslog till **srv-syslog01** (`filterlog.log` m.m.) — se [Central loggning](../book-02-plattform/10-central-loggning-srv-syslog01.md).

### Aktivera / verifiera på OPNsense

| Inställning | Var | Syfte |
|-------------|-----|--------|
| Remote syslog | Settings → Logging / Targets | Peeka på srv-syslog01 `:514` |
| Firewall log | Rules → Log | Default deny + WAN hits |
| Suricata | IDS/IPS → Settings | Alerts till syslog (plugin-standard) |

På srv-syslog01: sök i Loki efter host `fw-core01.lab.engstrom.live` (eller er faktiska OPNsense-hostname).

Typiska queries (LogQL — justera labels efter Promtail):

```logql
{host="fw-core01.lab.engstrom.live"} |= "suricata"
{host="fw-core01.lab.engstrom.live"} |~ "(?i)(block|reject|ips|suricata)"
```

### Discord vid IPS/IDS (utan Wazuh)

Gör alerting **där loggarna redan finns**:

1. **Grafana på srv-syslog01** (eller kluster-Grafana med Loki-datasource): skapa **alert rule** — t.ex. > N Suricata-alerts på 5 min med severity high.  
2. Contact point → **Discord** (samma webhook som [Alerting](13-alerting-discord-apprise.md)).  
3. Håll tröskeln **hög** i början — annars spam.

Alternativ: veckovis manuell Loki-sök tills en alert-regel är kalibrerad.

## Exponerade tjänster — praktik

| Kontroll | Var |
|----------|-----|
| Minimera öppna portar på WAN | OPNsense NAT — bara det ni behöver (mail, ev. game) |
| Resten via Cloudflare Tunnel / proxy | Zero Trust där det går |
| Auth på app-lager | Authentik, Seerr OIDC — inte “öppen port = öppen app” |
| Geo / reputation | OPNsense plugins (valfritt) — blockera länder ni inte använder |
| Regeluppdateringar | Suricata rules + OPNsense updates — månadskalender |

**Kubernetes** syns utåt oftast som **EN IP** (NAT till `192.168.20.140/142`) — Suricata ser WAN-trafik; **east-west** mellan pods hanteras av **Cilium** + NetworkPolicy (separat från OPNsense).

## Vad OPNsense *inte* ersätter

| Behov | Verktyg |
|-------|---------|
| Pod/minne/disk | Prometheus → Discord |
| URL uppe? | Uptime Kuma → Discord |
| App-auth | Authentik |
| Lateral movement i klustret | Cilium, RBAC, image updates |

## Incident — enkel ordning

1. Discord-alert (Uptime / Prometheus / ev. Loki)  
2. OPNsense **Live View** + Loki `filterlog` / Suricata samma tidsfönster  
3. Kluster: `kubectl get pods -A`, Grafana dashboards  
4. Blockera IP / temporär WAN-regel om uppenbart angrepp  

## Relaterat

- [VLAN och OPNsense](01-vlan-opnsense.md)
- [Cloudflare och TLS](03-cloudflare-tls.md)
- [Alerting — Discord](13-alerting-discord-apprise.md)
- [Logrotation srv-syslog01](../book-02-plattform/11-loggrotation-och-integritet.md)
