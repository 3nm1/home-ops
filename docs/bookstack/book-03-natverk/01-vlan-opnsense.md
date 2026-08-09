# VLAN och OPNsense

Se även repo-root `NETWORK.md`.

## VLAN-översikt

| VLAN | Namn | Syfte |
|------|------|-------|
| 10 | LAN | Vanliga klienter |
| 20 | Servers | Talos, TrueNAS, backend |
| 30 | Cameras | Isolerade kameror |
| 40 | IoT | Smarta prylar (misstrodda) |
| 50 | Guest | Gäst-WiFi, isolerat |
| 99 | Management | Proxmox, switchar, OPNsense |
| 199 | IPMI | Out-of-band |

## OPNsense

- Routing mellan VLAN
- Brandvägg: default deny, öppna endast det som behövs
- DHCP/DNS per VLAN
- DNS overrides för interna tjänster vid behov

## Brandväggsfilosofi

1. Blockera allt
2. Tillåt explicit det som behövs
3. IoT → aldrig LAN/Servers utan regel

## Kubernetes-noder

Alla Talos-noder sitter på **VLAN 20** (`192.168.20.0/24`).
