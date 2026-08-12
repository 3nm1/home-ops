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
- [ ] **Backup-strategi** för PostgreSQL (Nextcloud + dokumentera RPO/RTO)

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

- Userdata redan på TrueNAS (NFS)
- PostgreSQL på Longhorn — överväg regelbunden DB-backup / Velero för `family`-namespace
- Velero kör redan `daily-authentik`
- Dokumentera RPO/RTO när det känns moget

## Full svenska i Authentik

Svenska locale (`sv`) är ~3% översatt. Praktisk lösning idag: svenska **flow-titlar** och **prompt-labels**, engelska systemknappar accepteras.
