# Nextcloud — Milestone 1

**URL:** `https://cloud.engstrom.live`  
**Namespace:** `family`  
**Repo:** `kubernetes/apps/family/nextcloud/`

## Mål (milestone 1)

- [x] Nextcloud för familj
- [x] PostgreSQL (Bitnami legacy chart)
- [x] Användardata på **NFS** (TrueNAS)
- [x] App-config på **Longhorn**
- [x] Authentik OIDC (`user_oidc`)
- [x] HTTPRoute via `envoy-internal`
- [x] CronJob (bakgrundsjobb)
- [x] Redis (fil-låsning / memcache)
- [x] Admin-varningar åtgärdade (HSTS, maintenance window, m.m.)
- [x] Skeleton directory (nya användare)
- [x] Group provisioning från Authentik
- [ ] Group folders `Familj` (struktur i UI — se [användare och grupper](04-nextcloud-anvandare-grupper-skeleton.md))
- [ ] Collabora (medvetet pausat — milestone 2)
- [ ] Custom tema via Theming app (pausat)

## Arkitektur

```
Browser → Envoy (internal) → Nextcloud (Apache)
                              ├── Config PVC (Longhorn: nextcloud)
                              ├── Data PVC (NFS: nextcloud-data)
                              ├── PostgreSQL (Longhorn: nextcloud-postgresql)
                              ├── Redis (nextcloud-redis-master)
                              └── CronJob (nextcloud-cron, var 5:e min)
```

## NFS

| Setting | Värde |
|---------|-------|
| TrueNAS path | `/mnt/NFS/family/nextcloud` |
| PV | `family-nextcloud-data-nfs` |
| subPath i pod | `data` → `/var/www/html/data` |
| Skeleton | `data/__skeleton/` → `/var/www/html/data/__skeleton/` |

**Maproot root** på TrueNAS + init container `fix-nfs-data-permissions` (chown 33:33).

## Helm

- Chart: `nextcloud` **9.2.2** från `https://nextcloud.github.io/helm`
- `persistence.nextcloudData.enabled: true` + `existingClaim: nextcloud-data`
- **Inte** `extraVolumeMounts` för data (gav duplicate mount — fixat)
- `cronjob.enabled: true`, `type: cronjob`, kör som UID 33
- `redis.enabled: true` (standalone, utan persistence)
- HSTS via HTTPRoute `ResponseHeaderModifier`
- Hooks: `before-starting` (OIDC, SMTP), `post-upgrade` (cron mode, repair)

## Secrets (1Password item `nextcloud`)

| Key | Användning |
|-----|------------|
| `NEXTCLOUD_ADMIN_PASSWORD` | Admin-lösenord (break-glass) |
| `POSTGRES_PASSWORD` | PostgreSQL |
| `OIDC_CLIENT_ID` / `OIDC_CLIENT_SECRET` | Authentik — måste matcha provider i Authentik |
| `REDIS_PASSWORD` | Redis subchart |
| `SMTP_FROM` | Från `smtp-relay`-post (via ExternalSecret) |

## OIDC

- Discovery: `https://auth.engstrom.live/application/o/nextcloud/.well-known/openid-configuration`
- Redirect: `https://cloud.engstrom.live/apps/user_oidc/code`
- App `user_oidc` + provider `authentik` via `before-starting`-hook
- Group provisioning: `--mapping-groups=groups --group-provisioning=1`
- Detaljer: [användare, grupper och skeleton](04-nextcloud-anvandare-grupper-skeleton.md)

## E-post (SMTP-relay)

- Relay: `smtp-relay.selfhosted.svc.cluster.local:25` (ingen auth internt)
- Upstream: Bahnhof port **465** SMTPS
- From-adress: `SMTP_FROM` från 1Password-posten `smtp-relay`
- Konfigureras via `before-starting`-hook (`occ config:system:set mail_*`)

## Deploy-beroenden

```yaml
dependsOn:
  - external-secrets-stores
  - longhorn
  - authentik
  - smtp-relay  # namespace selfhosted
```

## Viktigt

**Kör inte `helm uninstall nextcloud` manuellt** — låt Flux äga releasen. Manuell avinstallation lämnade config-PVC i halvläge (CAN_INSTALL-problemet).

**Kör alltid `occ` som www-data** — inte root:

```bash
kubectl exec -n family deploy/nextcloud -- su -s /bin/bash www-data -c "php occ status"
```

## Relaterade sidor

- [Felsökning](02-nextcloud-felsokning.md)
- [Användare, grupper och skeleton](04-nextcloud-anvandare-grupper-skeleton.md)
- [Authentik branding och flows](../book-04-identitet/04-authentik-branding-flows.md)
