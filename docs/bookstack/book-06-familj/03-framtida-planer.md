# Familjetjänster — framtida planer

Pausade idéer att återkomma till.

## Klart (aug 2026)

- OIDC via Authentik + group provisioning
- Skeleton directory för nya användare
- CronJob, Redis, admin-varningar
- Authentik branding (PVC `/data`, mörkt tema, flows)

Se [användare, grupper och skeleton](04-nextcloud-anvandare-grupper-skeleton.md) och [Authentik branding](../book-04-identitet/04-authentik-branding-flows.md).

## Nästa steg (milestone 1.5)

- [ ] **Group folder `Familj`** med delad mappstruktur i UI
- [ ] **Onboarda familjemedlemmar** i Authentik
- [ ] **Skeleton i GitOps** (`skeletondirectory` i `helmrelease.yaml`)
- [ ] **Group provisioning i hook** (`--group-provisioning=1` permanent i Git)
- [x] **Velero `daily-family`** för PostgreSQL + config-PVC
- [ ] **TrueNAS-backup** verifierad för `/mnt/NFS/family/nextcloud`

## Nextcloud tema

- **Theming app** — färger, logo, namn via `occ config:app:set theming`
- Kan automatiseras i Helm hooks + ConfigMap för logo
- Medvetet pausat — Authentik-brand räcker för SSO-upplevelsen

## Collabora (milestone 2)

Online-redigering av dokument. Medvetet **av** i milestone 1:

```yaml
collabora:
  enabled: false
```

Kräver extra resurser och egen subdomain — planera separat.

## Backup

- Userdata redan på TrueNAS (NFS) — **TrueNAS snapshots/replikering krävs**
- PostgreSQL + config-PVC: Velero `daily-family` (namespace `family`)
- Authentik PostgreSQL + branding: Velero `daily-authentik`
- Se [Återställning](../book-08-runbooks/04-aterstallning.md)

## Full svenska i Authentik

Svenska locale (`sv`) är ~3% översatt. Praktisk lösning idag: svenska **flow-titlar** och **prompt-labels**, engelska systemknappar accepteras.
