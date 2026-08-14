# Återställning och rebuild

## Filosofi

> Om jag inte kan återskapa hela klustret från Git har något gått fel i designen.

## Vad som finns var

| Data | Plats | Velero | Återställning |
|------|-------|--------|---------------|
| Git manifests | GitHub `home-ops` | — | `git clone` |
| Krypterade secrets | SOPS i Git + age-nyckel | — | age key säker backup! |
| App secrets | 1Password | — | Oberoende av kluster |
| Media | TrueNAS NFS | Nej | TrueNAS backup |
| Familjefiler (Nextcloud) | TrueNAS NFS `/mnt/NFS/family/nextcloud` | Nej | **TrueNAS backup/snapshots** |
| Nextcloud config + PostgreSQL | Longhorn i `family` | Ja (`daily-family`) | Velero restore |
| Nextcloud Redis | Ingen persistence | — | Återskapas automatiskt |
| Authentik PostgreSQL + `/data` | Longhorn + PVC `authentik-data` | Ja (`daily-authentik`) | Velero restore |
| BookStack m.fl. | `selfhosted` | Ja (`daily-selfhosted`) | Velero restore |
| Media-appar (config) | `media` | Ja (`daily-media`) | Velero restore |
| Longhorn-volymar (generellt) | Talos-noder | — | Longhorn backup → NFS |
| etcd state | Talos noder | — | Rebuild = nytt kluster |

## Velero — scheman

Backups till MinIO på `192.168.20.20:/mnt/NFS/velero`.

Repo: `kubernetes/apps/storage/velero/schedules/app/schedules.yaml`

| Schedule | Tid (UTC) | Namespace | Innehåll |
|----------|-----------|-----------|----------|
| `daily-media` | 02:00 | `media` | App-config (NFS-volymar exkluderade i pod-annoteringar) |
| `daily-family` | 02:15 | `family` | Nextcloud config-PVC + PostgreSQL |
| `daily-authentik` | 02:30 | `authentik` | PostgreSQL + branding-filer (`authentik-data` på `/data`) |
| `daily-selfhosted` | 03:00 | `selfhosted` | BookStack, Homarr, m.fl. |

TTL: 720h (30 dagar).

Stora NFS-volymar (media, Nextcloud userdata) backas **inte** via Velero — de lever på TrueNAS.

### Verifiera backup

```bash
velero schedule get -n velero
velero backup get -n velero
velero backup describe daily-family-<timestamp> -n velero --details
```

Efter deploy av ny schedule:

```bash
flux reconcile kustomization velero-schedules -n flux-system --with-source
velero schedule get -n velero   # ska visa daily-family
```

### Restore (exempel — family)

```bash
velero restore create family-restore --from-backup daily-family-<timestamp> -n velero
```

## Full kluster-rebuild (översikt)

1. Säkerställ age-nyckel + 1Password + TrueNAS lever
2. Proxmox VMs för Talos — recreate från `talos/talconfig.yaml`
3. Bootstrap (`bootstrap/helmfile`) → Flux
4. Flux synkar `kubernetes/apps/` — allt kommer tillbaka
5. NFS-PV binder automatiskt om samma export paths
6. Velero restore om Longhorn-data förlorades (family, authentik, selfhosted, media)
7. Verifiera Authentik → OIDC-appar fungerar
8. Importera BookStack-innehåll från `docs/bookstack/` om DB förlorad

## Nextcloud disaster

### Scenario A — bara PostgreSQL/config förlorad (NFS userdata OK)

1. NFS-data kvar på TrueNAS → användarfiler säkra
2. Velero restore av `family`-namespace **eller** recreate PVC + Helm
3. Om tom DB: se [Nextcloud felsökning](../book-06-familj/02-nextcloud-felsokning.md) — `occ maintenance:install` / manuell install
4. OIDC hooks (`before-starting`) konfigurerar Authentik igen från Git

### Scenario B — TrueNAS förlorad

**Kritiskt** — användardata kan inte återställas från Velero. Kräver TrueNAS-backup/replikering utanför klustret.

### Scenario C — Redis omstart

Ingen åtgärd — cache byggs om. Fil-låsning återgår till DB tillfälligt om Redis saknas.

## Authentik disaster

1. Velero restore av `authentik`-namespace (PostgreSQL + `authentik-data`)
2. OIDC client secrets finns kvar i 1Password — matcha mot Authentik UI om provider återskapas
3. Branding-filer (logo, favicon) ligger på `/data` — ingår i `daily-authentik` sedan aug 2026

## TrueNAS — familjedata

**Viktigast för Nextcloud:** säkerställ backup av `/mnt/NFS/family/nextcloud` på TrueNAS (ZFS snapshots, replikering eller annan offsite-kopia). Velero täcker **inte** denna data.

## Dokumentation

Om BookStack-databasen dör: **detta repo** (`docs/bookstack/`) är backup av dokumentationen.

## age-nyckel

**KRITISKT:** Utan age-nyckeln kan Flux inte dekryptera SOPS. Förvara utanför klustret (password manager, offline backup).
