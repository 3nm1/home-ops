# 🏗️ Home Lab Architecture

This document describes the overall architecture of my home lab — a glorious Frankenstein of Kubernetes, Proxmox, OPNsense, Cisco networking, GitOps, and questionable life choices.
It’s built to be reproducible, automated, and just complicated enough to make me feel like a cloud provider in my own house.

---

## 🧩 High‑Level Overview

The home lab consists of several major components working together:

- **Proxmox** as the virtualization layer
- **Talos Linux** running as Kubernetes nodes
- **Flux CD** managing the entire cluster state
- **Cilium** providing eBPF‑powered networking
- **OPNsense** handling routing, firewalling, and VLAN segmentation
- **Cisco switches** providing enterprise‑grade networking (for a non‑enterprise home)

Everything is declarative, version‑controlled, and designed so that if I accidentally destroy the cluster, I can rebuild it with minimal crying.

---

## 🖥️ Virtualization Layer: Proxmox

Proxmox is the foundation of the entire environment.

### What it does

- Hosts all Talos nodes as VMs
- Provides snapshots (aka “my safety net”)
- Manages storage pools
- Allows me to pretend I’m running a datacenter

### Why Proxmox?

Because it’s stable, powerful, and doesn’t require me to sell a kidney for a VMware license.

---

## 🧊 Kubernetes Layer: Talos Linux

Talos Linux runs all Kubernetes nodes — control plane and workers.

### Key characteristics

- Immutable OS
- No SSH
- No pets, only cattle
- Fully API‑driven
- Perfect for GitOps

Talos ensures that every node is predictable and rebuildable.
If a node misbehaves, I don’t fix it — I replace it.

---

## ☸️ Kubernetes Cluster

The Kubernetes cluster is built for:

- Learning
- Experimentation
- Hosting self‑hosted apps
- Breaking things safely
- Rebuilding them even safer

### Cluster roles

- **Control Plane Nodes**
  Handle API server, scheduler, controller manager, etcd (talos01–03).

- **Worker Nodes**
  Workloads and GPU apps on srv-talos04 (worker-only); CP nodes may also run workloads.

---

## 🌐 Networking: OPNsense + Cisco + Cilium

### OPNsense

OPNsense is the gateway, firewall, and general packet‑bouncer.

It handles:

- Routing
- Firewall rules
- VLANs
- DHCP
- DNS overrides
- Deciding which packets deserve to live

### Cisco Switches

Cisco switches provide:

- VLAN segmentation
- Trunking
- PoE for devices
- Enough blinking LEDs to light up a small village

### Cilium (Inside Kubernetes)

Cilium handles:

- Pod‑to‑pod networking
- Network policies
- eBPF‑powered magic
- Making me feel like I understand Linux networking (I don’t)

---

## 🔁 GitOps: Flux CD

Flux is the brain of the operation.

### Responsibilities

- Watches Git for changes
- Applies manifests to the cluster
- Reverts manual changes
- Keeps everything consistent
- Judges me silently when I kubectl apply something manually

Flux ensures the cluster always matches what’s in Git — even if I forget what’s in Git.

---

## 🔐 Secrets Management: SOPS

All secrets are encrypted using SOPS with age keys.

### Why?

Because committing plain‑text secrets to Git is a crime against humanity.

---

## 🗄️ Storage

Storage is provided by Proxmox and exposed to Kubernetes via CSI drivers (depending on setup).

### Goals

- Persistent volumes for apps
- Snapshots
- Backups
- Not losing my data when I inevitably break something

---

## 🧱 Architecture Diagram (Conceptual)

```bash
       ┌──────────────────────────────┐
       │          OPNsense            │
       │   Routing / Firewall / VLAN  │
       └──────────────┬───────────────┘
                      │
            ┌─────────┴─────────┐
            │   Cisco Switch    │
            │   VLAN Trunking   │
            └─────────┬─────────┘
                      │
       ┌──────────────┼──────────────┐────────────────┐
       │              │              │                │
       │              │              │                │
┌────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ Proxmox VM │ │ Proxmox VM  │ │ Proxmox VM  │ │ Proxmox VM  │
│ Talos CP   │ │ Talos CP    │ │ Talos CP    │ │ Talos Worker│
└──────┬─────┘ └───────┬─────┘ └──────┬──────┘ └──────┬──────┘
       │               │              │               │
       │               │              │               │
       └───────────────┴──────────────┘───────────────┘
                      Kubernetes Cluster
                              │
                        ┌─────┴──────┐
                        │  Flux CD   │
                        │  GitOps    │
                        └────────────┘

```

---

## 🧪 Philosophy

This home lab is built on three principles:

1. **Automate everything**
2. **Document everything**
3. **Break everything (but be able to rebuild it)**

If I can’t rebuild the entire cluster from scratch using Git, then something is wrong.

---

## 🏁 Final Thoughts

This architecture is the result of curiosity, experimentation, and a desire to learn modern infrastructure the hard way — by doing it myself.

If you’re building something similar, I salute you.
If you’re not, you probably value your free time more than I do.

