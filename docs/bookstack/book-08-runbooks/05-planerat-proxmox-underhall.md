# Planerat Proxmox-underhåll

Runbook för när en **Proxmox-värd** ska tas offline — t.ex. RAM-uppgradering, kernel-uppdatering som kräver omstart, diskbyte eller annat underhåll som kräver reboot av värden.

## Gäller samma procedur för

| Scenario | Kommentar |
|----------|-----------|
| RAM-minne / hårdvara | Proxmox reboot efter fysiskt arbete |
| Kernel-uppdatering (`apt upgrade` + reboot) | Samma evakuering — skillnaden är bara *varför* värden startas om |
| Proxmox-patching som kräver omstart | Planera som underhållsfönster, inte ad hoc-reboot |

**Princip:** Förbered klustret *innan* Proxmox eller Talos-VM försvinner. Oplanerad reboot av Proxmox (utan drain/eviction) ger Longhorn-faulted volymer, hängande attach och app-nedtid — se erfarenhet aug 2026.

## Nodkarta

| Proxmox | Talos-VM | IP |
|---------|----------|-----|
| px-node01 | srv-talos01 | 192.168.20.151 |
| px-node02 | srv-talos02 | 192.168.20.152 |
| px-node03 | srv-talos03 | 192.168.20.153 |
| px-node04 | srv-talos04 | 192.168.20.154 |

En Proxmox-värd = en Talos-VM. Reboot av värden tar **en** Kubernetes-nod offline.

**Undantag:** `srv-talos04` har GPU-taint — Longhorn kräver `taintToleration` för `media.engstrom.live/gpu=true:NoSchedule` (konfigurerat i `kubernetes/apps/storage/longhorn/app/helmrelease.yaml`).

## Översikt

```
Longhorn eviction  →  cordon + drain  →  stoppa VM / reboot Proxmox  →  VM upp  →  Longhorn + uncordon
```

Med 4 control plane-noder klarar klustret **en** nod nere (etcd-quorum 3/4). **En Proxmox-värd i taget** — repetera aldrig rolling reboot av alla värdar om det går att undvika.

---

## Före underhåll

### 1. Baslinje

```bash
kubectl get nodes
kubectl get pods -A -o wide --field-selector spec.nodeName=srv-talos0X
kubectl get volumes.longhorn.io -n longhorn-system \
  -o custom-columns=NAME:.metadata.name,STATE:.status.state,ROB:.status.robustness | grep -v healthy
talosctl --nodes 192.168.20.15X health
```

Byt `srv-talos0X` / `.15X` till aktuell nod. **Alla volymer ska vara `healthy` innan du börjar.**

### 2. Longhorn — evakuera replikor

I UI: `longhorn.engstrom.live` → **Node** → välj nod → **Disable Scheduling** + **Eviction Requested**.

Eller CLI:

```bash
kubectl patch nodes.longhorn.io srv-talos0X -n longhorn-system --type merge \
  -p '{"spec":{"allowScheduling":false,"evictionRequested":true}}'
```

Vänta tills **inga replikor** ligger kvar på noden:

```bash
kubectl get replicas.longhorn.io -n longhorn-system \
  -o custom-columns=NAME:.metadata.name,NODE:.spec.nodeID,STATE:.status.currentState | grep talos0X
```

Verifiera att volymer fortfarande är healthy:

```bash
kubectl get volumes.longhorn.io -n longhorn-system \
  -o custom-columns=NAME:.metadata.name,ROB:.status.robustness | grep -v healthy
```

### 3. Kubernetes — cordon och drain

```bash
kubectl cordon srv-talos0X

kubectl drain srv-talos0X \
  --ignore-daemonsets \
  --delete-emptydir-data \
  --grace-period=300 \
  --timeout=15m
```

`--ignore-daemonsets` behövs för Longhorn, Cilium m.m.

Drain fastnar? Kolla:

```bash
kubectl get pods -A -o wide --field-selector spec.nodeName=srv-talos0X
kubectl get pdb -A
kubectl describe pod -n <namespace> <pod>
```

### 4. Sista check — stoppa VM / reboot Proxmox

```bash
kubectl get pods -A -o wide --field-selector spec.nodeName=srv-talos0X
# Endast DaemonSets kvar — OK

kubectl get nodes
# srv-talos0X: Ready,SchedulingDisabled
```

1. Stäng av **Talos-VM** i Proxmox (Shutdown), **eller**
2. Reboota **Proxmox-värden** (kernel-uppdatering) — VM:en följer med om den inte redan är stoppad

Tips: aktivera **Start at boot** på Talos-VM så den kommer upp automatiskt efter Proxmox-reboot.

---

## Under underhåll

- Klustret kör på övriga 3 noder.
- Stoppa **inte** fler Proxmox-värdar parallellt.
- Appar med Longhorn-PVC ska fortsätta köra om drain lyckades.

---

## Efter underhåll

### 1. VM och nod Ready

Starta VM om den inte autostartade. Vänta:

```bash
kubectl get nodes -w
talosctl --nodes 192.168.20.15X health
```

### 2. Longhorn — tillåt nod igen

```bash
kubectl patch nodes.longhorn.io srv-talos0X -n longhorn-system --type merge \
  -p '{"spec":{"allowScheduling":true,"evictionRequested":false}}'
```

Kontrollera att Longhorn-komponenter finns på noden:

```bash
kubectl get ds -n longhorn-system
kubectl get pods -n longhorn-system -o wide | grep srv-talos0X
```

På **srv-talos04**: verifiera `engine-image` och `longhorn-csi-plugin` (GPU-taint).

Replikor rebalanseras tillbaka över tid — du behöver inte vänta på det innan uncordon.

### 3. Uncordon

```bash
kubectl uncordon srv-talos0X
```

### 4. Slutcheck

```bash
kubectl get nodes
kubectl get pods -A | grep -vE 'Running|Completed'
kubectl get volumes.longhorn.io -n longhorn-system \
  -o custom-columns=NAME:.metadata.name,STATE:.status.state,ROB:.status.robustness | grep -v healthy
```

---

## Snabbreferens (px-node02 / srv-talos02)

```bash
# FÖRE
kubectl patch nodes.longhorn.io srv-talos02 -n longhorn-system --type merge \
  -p '{"spec":{"allowScheduling":false,"evictionRequested":true}}'
# vänta tills replikor evakuerats …
kubectl cordon srv-talos02
kubectl drain srv-talos02 --ignore-daemonsets --delete-emptydir-data --grace-period=300 --timeout=15m

# EFTER (VM uppe, nod Ready)
kubectl patch nodes.longhorn.io srv-talos02 -n longhorn-system --type merge \
  -p '{"spec":{"allowScheduling":true,"evictionRequested":false}}'
kubectl uncordon srv-talos02
```

---

## Proxmox kernel-uppdatering — extra steg

Samma runbook som ovan. På Proxmox-värden *före* reboot:

```bash
# På px-node0X (SSH till Proxmox, inte Talos)
apt update
apt list --upgradable
# Om kernel/proxmox-kernel uppgraderas — planera underhållsfönster
```

Ordning:

1. Kör hela **Före underhåll** för `srv-talos0X` på klustret
2. Stoppa Talos-VM (eller lita på graceful shutdown vid host-reboot)
3. `reboot` på Proxmox-värden
4. Verifiera Proxmox uppe, VM startad
5. Kör **Efter underhåll**

**Gör inte** `reboot` på Proxmox utan drain — det motsvarar oplanerad nodförlust.

---

## Felsökning

| Symptom efter återstart | Åtgärd |
|-------------------------|--------|
| Nod `NotReady` | Proxmox-konsol på VM, ping `.152`, `talosctl health` |
| Volym `degraded` / `faulted` | Longhorn UI → Rebuild/Salvage; kolla att CSI/engine-image kör på alla noder |
| Pod `ContainerCreating` | `kubectl describe pod` — ofta `FailedAttachVolume`; vänta eller restart pod |
| Longhorn bara 3/4 manager | GPU-nod: kolla `taint-toleration`-setting |
| etcd timeout | Vänta tills alla CP-noder Ready; se [Klusterhälsa](02-kluster-halsa.md) |

---

## Relaterat

- [Klusterhälsa](02-kluster-halsa.md) — etcd, Longhorn, övervakning
- [Vanliga kommandon](03-vanliga-kommandon.md)
- [Återställning](04-aterstallning.md) — om något gått riktigt fel
