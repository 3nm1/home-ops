# BookStack-struktur

```
Hylla: Engström Home Lab
│
├── Bok 01: Översikt & resa
│   ├── Kapitel: Introduktion
│   │   ├── Välkommen och syfte
│   │   ├── Hardware och noder
│   │   └── GitOps-resan (Flux + cluster-template)
│   └── Kapitel: Arkitektur
│       └── Högnivådiagram
│
├── Bok 02: Plattform
│   ├── Kapitel: Kubernetes
│   │   ├── Talos Linux
│   │   └── Cilium och kluster-CIDR
│   ├── Kapitel: GitOps
│   │   ├── Flux — hur det hänger ihop
│   │   └── App-struktur i repot
│   ├── Kapitel: Secrets
│   │   ├── SOPS och age
│   │   └── External Secrets + 1Password
│   └── Kapitel: Lagring
│       ├── Longhorn
│       └── NFS på TrueNAS
│
├── Bok 03: Nätverk
│   ├── Kapitel: Fysiskt / LAN
│   │   ├── VLAN och OPNsense
│   │   └── Cisco switches
│   ├── Kapitel: Kubernetes-ingress
│   │   ├── Envoy Gateway (internal / external)
│   │   └── HTTPRoute-mönster
│   └── Kapitel: Extern åtkomst
│       ├── Cloudflare Tunnel och DNS
│       └── cert-manager + Let's Encrypt
│
├── Bok 04: Identitet & säkerhet
│   ├── Kapitel: Authentik
│   │   ├── Översikt och URL:er
│   │   ├── OIDC-appar
│   │   └── Envoy forward-auth (*arr)
│
├── Bok 05: Media stack
│   ├── Kapitel: Pipeline
│   │   ├── Översikt (Prowlarr → *arr → Jellyfin)
│   │   └── App-lista och URL:er
│   └── Kapitel: Automation
│       ├── Recyclarr vs Profilarr
│       ├── Maintainerr, Autoscan, Unpackerr
│       └── Theme Park och notiser (Apprise)
│
├── Bok 06: Familjetjänster
│   ├── Kapitel: Nextcloud
│   │   ├── Milestone 1 — design och beslut
│   │   ├── Installation och NFS
│   │   └── Felsökning (CAN_INSTALL m.m.)
│   └── Kapitel: Framtida planer
│       └── Tema, skeleton, Collabora (pausat)
│
├── Bok 07: Self-hosted verktyg
│   └── Kapitel: Appar
│       ├── Homarr, BookStack, Homebox
│       └── Stirling PDF, IT-Tools
│
└── Bok 08: Runbooks
    ├── Kapitel: Drift
    │   ├── Flux reconcile
    │   └── Klusterhälsa (etcd, Longhorn)
    ├── Kapitel: Felsökning
    │   └── Vanliga kommandon
    └── Kapitel: Återställning
        └── Rebuild-filosofi
```

## Fil → BookStack-mappning

| Fil | BookStack-sida |
|-----|----------------|
| `book-01-oversikt/01-valkommen.md` | Välkommen och syfte |
| `book-01-oversikt/02-hardware-och-noder.md` | Hardware och noder |
| `book-01-oversikt/03-gitops-resan.md` | GitOps-resan |
| `book-01-oversikt/04-hog-niva-arkitektur.md` | Högnivådiagram |
| `book-02-plattform/01-talos-kubernetes.md` | Talos Linux |
| `book-02-plattform/02-flux-gitops.md` | Flux — hur det hänger ihop |
| `book-02-plattform/03-app-struktur-i-repot.md` | App-struktur i repot |
| `book-02-plattform/04-sops-och-age.md` | SOPS och age |
| `book-02-plattform/05-external-secrets-1password.md` | External Secrets + 1Password |
| `book-02-plattform/06-longhorn.md` | Longhorn |
| `book-02-plattform/07-nfs-truenas.md` | NFS på TrueNAS |
| `book-03-natverk/01-vlan-opnsense.md` | VLAN och OPNsense |
| `book-03-natverk/02-envoy-gateways.md` | Envoy Gateway |
| `book-03-natverk/03-cloudflare-tls.md` | Cloudflare + TLS |
| `book-04-identitet/01-authentik-oversikt.md` | Authentik översikt |
| `book-04-identitet/02-oidc-appar.md` | OIDC-appar |
| `book-04-identitet/03-forward-auth.md` | Forward-auth |
| `book-05-media/01-pipeline-oversikt.md` | Media pipeline |
| `book-05-media/02-appar-och-urls.md` | App-lista och URL:er |
| `book-05-media/03-automation.md` | Automation |
| `book-06-familj/01-nextcloud-milestone-1.md` | Nextcloud milestone 1 |
| `book-06-familj/02-nextcloud-felsokning.md` | Nextcloud felsökning |
| `book-06-familj/03-framtida-planer.md` | Framtida planer |
| `book-07-selfhosted/01-appar.md` | Self-hosted appar |
| `book-08-runbooks/01-flux-reconcile.md` | Flux reconcile |
| `book-08-runbooks/02-kluster-halsa.md` | Klusterhälsa |
| `book-08-runbooks/03-vanliga-kommandon.md` | Vanliga kommandon |
| `book-08-runbooks/04-aterstallning.md` | Återställning |
