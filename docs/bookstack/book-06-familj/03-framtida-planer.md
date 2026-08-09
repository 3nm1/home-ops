# Familjetjänster — framtida planer

Pausade idéer att återkomma till.

## Nextcloud tema

- **Theming app** — färger, logo, namn via `occ config:app:set theming`
- Kan automatiseras i Helm hooks + ConfigMap för logo
- Se diskussion aug 2026 — medvetet pausat

## Fördefinierad filstruktur

| Metod | Användning |
|-------|------------|
| **Skeleton directory** | Standardmappar för *nya* användare |
| **Group folders** | Delad familjestruktur alla ser |
| Ersätta hela Files-UI | Kräver custom app — inte realistiskt |

GitOps-vänligt: skeleton på NFS + `skeletondirectory` i config.php via `nextcloud.configs`.

## Collabora (milestone 2?)

Online-redigering av dokument. Medvetet **av** i milestone 1:

```yaml
collabora:
  enabled: false
```

Kräver extra resurser och egen subdomain — planera separat.

## Flertal familjekonton

- Authentik OIDC för inloggning
- `user_oidc` + `allow_multiple_user_backends`
- Skeleton/groupfolders viktigare när fler användare tillkommer

## Backup

- Userdata redan på TrueNAS (NFS)
- PostgreSQL på Longhorn — överväg regelbunden DB-backup / Velero
- Dokumentera RPO/RTO när det känns moget
