# Nextcloud — felsökning

Dokumenterat aug 2026 efter första deploy.

## Problem 1: CAN_INSTALL saknas

**Symptom:** Webben visar att ominstallation kräver `CAN_INSTALL`.

**Orsak:** Config-PVC (Longhorn) hade rester från avbruten/halv install — t.ex. efter `helm uninstall` eller misslyckade Helm upgrades.

**Fix:** Rensa config och installera om (se nedan).

---

## Problem 2: "not overwriting config.php"

**Symptom:** Tom eller ogiltig `config.php` (0 byte).

**Orsak:** `config.php` fanns men var ogiltig — entrypoint skriver inte över.

**Fix:** Ta bort filen **helt** medan podden är stoppad (annars återskapas tom fil):

```bash
kubectl scale deployment nextcloud -n family --replicas=0
# radera config.php från PVC (busybox-pod mot claim nextcloud)
kubectl scale deployment nextcloud -n family --replicas=1
```

---

## Problem 3: occ install — fel DB-host

**Symptom:** `could not translate host name "ne11xtcloud-postgresql"`

**Orsak:** Stavfel — rätt hostname är `nextcloud-postgresql`.

```bash
kubectl exec -n family deploy/nextcloud -- getent hosts nextcloud-postgresql
```

---

## Problem 4: "files already exist for this user"

**Symptom:** `occ maintenance:install` failar trots tom DB.

**Orsak:** DB nollställd (`DROP SCHEMA`) men `data/admin/` fanns kvar på NFS.

**Fix:**

```bash
kubectl exec -n family deploy/nextcloud -- sh -c '
  rm -rf /var/www/html/data/admin
  rm -f /var/www/html/data/.ocdata
  rm -f /var/www/html/config/config.php
'
```

Kör sedan `occ maintenance:install` igen.

---

## Manuell install (occ)

När autoinstall via Helm/env fastnat:

```bash
kubectl exec -n family deploy/nextcloud -- su -s /bin/bash www-data -c \
  'php occ maintenance:install \
    --admin-user=admin \
    --admin-pass="<från 1Password>" \
    --data-dir=/var/www/html/data \
    --database=pgsql \
    --database-name=nextcloud \
    --database-user=nextcloud \
    --database-pass="<från 1Password>" \
    --database-host=nextcloud-postgresql'
```

Verifiera:

```bash
kubectl exec -n family deploy/nextcloud -- su -s /bin/bash www-data -c "php occ status"
# installed: true
```

---

## Tidigare deploy-problem (Git/Helm)

| Problem | Orsak | Fix i Git |
|---------|-------|-----------|
| Inga pods | `${OIDC_*}` i hooks | Escapa som `$${OIDC_*}` |
| Helm upgrade fail | Dubbel mount `/var/www/html/data` | Använd `nextcloudData` PVC, ta bort extraVolumeMounts |
| Postgres Pending | Nod NotReady, Longhorn attach | Infrastruktur — se klusterhälsa |

---

## 503 på / men 200 på status.php

Nextcloud **inte installerad** — Apache kör, appen inte redo. Normalt under felsökning ovan.

---

## Flux vid klusterstress

```bash
flux suspend kustomization nextcloud -n flux-system
# fixa problem
flux resume kustomization nextcloud -n flux-system
```

---

## Nollställ databas (sista utväg)

Endast om ingen produktionsdata:

```bash
kubectl exec -n family nextcloud-postgresql-0 -- bash -c \
  'PGPASSWORD=$(cat /opt/bitnami/postgresql/secrets/password) psql -U nextcloud -d nextcloud -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"'
```

Rensa **även** NFS userdata efteråt.
