# Talos Linux

[Talos](https://www.talos.dev) är det immutable OS som kör alla Kubernetes-noder.

## Egenskaper

- **Ingen SSH** — all konfiguration via Talos API / `talosctl`
- **Ingen shell på noderna** — tvingar deklarativ drift
- **Immutability** — uppgraderingar via image, inte pakethantering

## Konfiguration i repot

```
talos/
├── talconfig.yaml      # Noder, IP, patches
├── talenv.yaml
├── patches/            # Global + per-nod (GPU på srv-talos04)
└── talsecret.sops.yaml # Känsliga Talos-värden (SOPS)
```

## Vanliga kommandon

```bash
talosctl --nodes 192.168.20.150 health
talosctl --nodes 192.168.20.150 get members
talosctl --nodes 192.168.20.151 dmesg
```

## Kubernetes

- **3× control plane** (talos01–03, HA etcd, kvorum 2/3)
- **1× worker** (talos04, GPU)
- **Cilium** som CNI (Talos inbyggda CNI avstängd)
- **VIP** för API: `192.168.20.150` (talos01–03)

## Vid nodproblem

Byt inte ut noden manuellt i klustret utan plan — Talos är designat för **replace, not repair**. Se runbook *Klusterhälsa*.
