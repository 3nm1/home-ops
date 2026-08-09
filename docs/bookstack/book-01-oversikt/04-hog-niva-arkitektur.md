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
         ┌──────────────┼──────────────┐
         │              │              │
   ┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼─────┐
   │ TrueNAS   │  │ Proxmox   │  │  Cisco    │
   │ NFS       │  │ 4× Talos  │  │  switches │
   └─────┬─────┘  └─────┬─────┘  └───────────┘
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

Se även repo-root `ARCHITECTURE.md` och `NETWORK.md` för tidigare versioner av samma material.
