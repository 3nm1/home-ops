# Högnivåarkitektur

```
                    Internet
                        │
              ┌─────────▼─────────┐
              │   Cloudflare      │
              │   Tunnel + DNS    │
              └─────────┬─────────┘
                        │
              ┌─────────▼─────────┐
              │   OPNsense        │
              │   VLAN 10/20/…    │
              └─────────┬─────────┘
                        │
         ┌──────────────┼──────────────┬──────────────┐
         │              │              │              │
   ┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼─────┐
   │ TrueNAS   │  │ Proxmox   │  │ srv-      │  │  Cisco    │
   │ NFS       │  │ 3× CP +   │  │ syslog01  │  │  switches │
   └─────┬─────┘  └─────┬─────┘  │ rsyslog   │  └───────────┘
         │              │        │ Loki      │
         │              │        └─────▲─────┘
         │              │              │ syslog :514
         │              └──────────────┘ (OPNsense, Proxmox, …)
         │              │
         │      ┌───────▼───────────────────────────┐
         │      │     Kubernetes (Talos)            │
         │      │  ┌─────────┐  ┌─────────────────┐ │
         └──────►  Longhorn │  │ Cilium (CNI)    │ │
                │  └─────────┘  └─────────────────┘ │
                │  ┌─────────┐  ┌─────────────────┐ │
                │  │  Flux   │  │ Envoy Gateway   │ │
                │  │ GitOps  │  │ int / ext LB    │ │
                │  └─────────┘  └─────────────────┘ │
                │  media │ family │ selfhosted │ …  │
                └───────────────────────────────────┘
```

## Ingress-vägar

| Väg | Användning |
|-----|------------|
| **Internal gateway** (`192.168.20.140`) | LAN: *arr, Homarr, Grafana, m.m. |
| **External gateway** (`192.168.20.142`) | Jellyfin, Seerr, Authentik — via Cloudflare |
| **HTTPRoute** | Gateway API — standard för nya appar |

## Autentisering (förenklat)

```
Användare → Envoy → antingen:
  • Authentik forward-auth (*arr, Sabnzbd, …)
  • OIDC in-app (Homarr, BookStack, Nextcloud, Seerr)
    → Authentik: lösenord + MFA
  • Ingen auth (Jellyfin internt, vissa verktyg)
```

## Dataflöde media

```
Prowlarr → Sonarr/Radarr/Lidarr → Sabnzbd → Unpackerr
         → Autoscan → Jellyfin
         → Seerr (requests, OIDC)
```

## Secrets

```
1Password → External Secrets Operator → Kubernetes Secret → Pod
Git secrets → SOPS/age → Flux decrypt → cluster-secrets
```

## Observability (kort)

| Spår | Plats | URL / åtkomst |
|------|-------|----------------|
| Metrics | Kluster (`kube-prometheus-stack`) | `grafana.engstrom.live` |
| Uptime | Kluster (Uptime Kuma) | `uptime-kuma.engstrom.live` |
| Loggar | srv-syslog01 (extern VM) | Grafana `:3000` på VM; syslog `:514` |

Detaljer: *Plattform → Observability* i BookStack.

Se även repo-root `ARCHITECTURE.md` och `NETWORK.md` för tidigare versioner av samma material.
