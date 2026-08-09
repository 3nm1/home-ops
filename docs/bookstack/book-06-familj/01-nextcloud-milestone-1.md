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
- [ ] Collabora ( medvetet pausat )
- [ ] Custom tema / skeleton ( pausat — se framtida planer )

## Arkitektur

```
Browser → Envoy (internal) → Nextcloud (Apache)
                              ├── Config PVC (Longhorn: nextcloud)
                              ├── Data PVC (NFS: nextcloud-data)
                              └── PostgreSQL (Longhorn: nextcloud-postgresql)
```

## NFS

| Setting | Värde |
|---------|-------|
| TrueNAS path | `/mnt/NFS/family/nextcloud` |
| PV | `family-nextcloud-data-nfs` |
| subPath i pod | `data` → `/var/www/html/data` |

**Maproot root** på TrueNAS + init container `fix-nfs-data-permissions` (chown 33:33).

## Helm

- Chart: `nextcloud` **9.2.2** från `https://nextcloud.github.io/helm`
- `persistence.nextcloudData.enabled: true` + `existingClaim: nextcloud-data`
- **Inte** `extraVolumeMounts` för data (gav duplicate mount — fixat)

## Secrets (1Password item `nextcloud`)

| Key | Användning |
|-----|------------|
| `NEXTCLOUD_ADMIN_PASSWORD` | Admin-lösenord |
| `POSTGRES_PASSWORD` | PostgreSQL |
| `OIDC_CLIENT_ID` / `OIDC_CLIENT_SECRET` | Authentik |

## OIDC

- Discovery: `https://auth.engstrom.live/application/o/nextcloud/.well-known/openid-configuration`
- Redirect: `https://cloud.engstrom.live/apps/user_oidc/code`
- Hooks installerar `user_oidc` och provider `authentik`

## E-post (SMTP-relay)

- Relay: `smtp-relay.selfhosted.svc.cluster.local:25` (ingen auth internt)
- Upstream: Bahnhof `mailout.privat.bahnhof.se:587`
- From-adress: `SMTP_FROM` från 1Password-posten `smtp-relay`
- Konfigureras via post-install/post-upgrade hooks (`occ config:system:set mail_*`)

## Deploy-beroenden

```yaml
dependsOn:
  - external-secrets-stores
  - longhorn
  - authentik
```

## Viktigt

**Kör inte `helm uninstall nextcloud` manuellt** — låt Flux äga releasen. Manuell avinstallation lämnade config-PVC i halvläge (CAN_INSTALL-problemet).
