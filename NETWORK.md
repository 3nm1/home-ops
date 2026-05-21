# 🌐 Home Lab Networking Architecture

This document describes the networking layer of my home lab — a heroic combination of OPNsense, Cisco switches, VLANs, Cilium, and enough routing rules to make future‑me wonder what past‑me was thinking.

The goal is simple:
**Segment everything, automate everything, and keep the packets flowing (preferably in the right direction).**

---

## 🧱 Core Components

The networking stack is built from three main pillars:

- **OPNsense** — the gateway, firewall, and general packet judge
- **Cisco switches** — providing VLANs, trunking, and enterprise‑grade blinking lights
- **Cilium** — handling Kubernetes networking with eBPF‑powered wizardry

Together, they form a network that is far more advanced than any normal household needs — and that’s exactly the point.

---

## 🚪 OPNsense: The Gatekeeper

OPNsense sits at the edge of the network and handles:

- Routing
- Firewall rules
- NAT
- DHCP
- DNS overrides
- VLAN interfaces
- Deciding which packets deserve to live

### Why OPNsense?

- Open source
- Powerful
- Flexible
- Doesn’t randomly explode like some alternatives
- Has a UI that doesn’t make me cry

---

## 🧩 VLAN Architecture

Everything in the home lab is segmented using VLANs.
Because flat networks are for people who enjoy chaos.

### Current VLANs

- **VLAN 10 — LAN**
  Normal household devices that don’t need special treatment.

- **VLAN 20 — Servers**
  For Kubernetes nodes, storage, and backend services.

- **VLAN 30 — Cameras**
  Because cameras should never talk to anything except the NVR.

- **VLAN 40 — IoT**
  For smart devices that I don’t trust (which is all of them).

- **VLAN 50 — Guest**
  For visitors, neighbors, delivery drivers, and anyone else who wants “the Wi‑Fi password.”
  Completely isolated so guests can browse cat videos without touching anything important — including my sanity.

- **VLAN 99 — Management**
  For Proxmox, OPNsense, switches, and other “please don’t break this” devices.

- **VLAN 199 — IPMI**
  For out‑of‑band management interfaces that absolutely must be isolated.
  This is the “break glass in case of emergency” network — where servers whisper their deepest hardware secrets and beg for firmware updates.

Each VLAN has its own subnet, firewall rules, and routing policies.

---

## 🔌 Cisco Switches: The Backbone

Cisco switches provide:

- VLAN tagging
- Trunk ports
- Access ports
- PoE where needed
- Enough LEDs to simulate a small airport runway

### Why Cisco?

Because they’re reliable, fast, and make me feel like I’m running a real datacenter.

---

## ☸️ Cilium: Kubernetes Networking

Inside the Kubernetes cluster, all pod‑to‑pod and pod‑to‑service traffic is handled by **Cilium**.

### What Cilium provides

- eBPF‑powered networking
- Network policies
- Load balancing
- Observability tools
- Hubble (aka “Wireshark but for your soul”)

Cilium integrates cleanly with Talos and gives me deep insight into what’s happening inside the cluster — usually more insight than I wanted.

---

## 🔐 Firewall Philosophy

The firewall rules follow a simple philosophy:

1. **Block everything**
2. **Allow only what’s needed**
3. **Regret nothing**

Examples:

- IoT cannot talk to LAN
- Cameras cannot talk to the internet
- Servers can talk to the internet only when necessary
- Management VLAN is sacred

---

## 🗺️ High‑Level Network Diagram

```bash
        ┌──────────────────────────┐
        │        Internet          │
        └──────────────┬───────────┘
                       │
               ┌───────┴──────────┐
               │     OPNsense     │
               │ Routing / FW /   │
               │ VLAN Interfaces  │
               └───────┬──────────┘
                       │
       ┌───────────────┼─────────────┐
       │               │             │
VLAN 99 Mgmt    VLAN 20 Servers   VLAN 10 LAN
       │               │             │
┌──────┴────── ┐  ┌────┴────┐   ┌────┴────┐
│ Cisco Switch │  │ Switch  │   │ Switch  │
└──────┬────── ┘  └────┬────┘   └────┬────┘
       │               │             │
┌──────┴───────┐  ┌────┴─────┐  ┌────┴─────┐
│ Proxmox Host │  │ Talos CP │  │ Talos WK │
└──────────────┘  └──────────┘  └──────────┘

```

---

## 🧪 Monitoring & Observability

Tools used to keep the network sane:

- **OPNsense Insight** — traffic graphs and flow data
- **Cilium Hubble** — deep Kubernetes traffic visibility
- **Prometheus + Grafana** — dashboards for everything
- **Logs** — for when dashboards lie

---

## 🧠 Lessons Learned

- VLANs are your friend
- IoT devices should never be trusted
- Cilium is magic
- OPNsense will save you from yourself
- Cisco switches are built like tanks
- Document everything or future‑you will suffer

---

## 🏁 Final Thoughts

The networking layer is the backbone of the entire home lab.
It keeps things isolated, secure, and predictable — and gives me a playground to learn real‑world networking concepts without breaking anything important.

(Except when I accidentally delete the wrong firewall rule. Then everything breaks.)

