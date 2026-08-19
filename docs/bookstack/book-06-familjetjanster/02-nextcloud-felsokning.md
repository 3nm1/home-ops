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
| `user_oidc` saknas | Fel grep i hook + post-install körs bara en gång | `before-starting`-hook med korrekt `grep 'user_oidc'` |
| Pod CrashLoop | `before-starting` med `set -e` | Best-effort hooks — faila inte pod start |
| Ingen CronJob | `cronjob.enabled: false` | Aktivera cronjob, UID 33, podAffinity |
| Client ID Error (Authentik) | OIDC credentials i 1Password ≠ Authentik | Kopiera från Authentik → 1Password → reconcile secret |

---

## Problem 5: OIDC / user_oidc

**Symptom:** `There are no commands defined in the "user_oidc" namespace` — bara lokal `admin` finns.

**Orsak:** Appen `user_oidc` aldrig installerad, eller provider inte konfigurerad.

**Fix:**

```bash
kubectl exec -n family deploy/nextcloud -- su -s /bin/bash www-data -c "php occ app:install user_oidc"
kubectl exec -n family deploy/nextcloud -- su -s /bin/bash www-data -c "php occ app:enable user_oidc"
kubectl exec -n family deploy/nextcloud -- su -s /bin/bash www-data -c "php occ user_oidc:provider"
```

Provider med credentials från secret (bash — i fish, se nedan):

```bash
CLIENT_ID=$(kubectl get secret nextcloud-secret -n family -o jsonpath='{.data.OIDC_CLIENT_ID}' | base64 -d)
CLIENT_SECRET=$(kubectl get secret nextcloud-secret -n family -o jsonpath='{.data.OIDC_CLIENT_SECRET}' | base64 -d)

kubectl exec -n family deploy/nextcloud -- su -s /bin/bash www-data -c \
  "php occ user_oidc:provider authentik \
    --clientid='${CLIENT_ID}' \
    --clientsecret='${CLIENT_SECRET}' \
    --discoveryuri='https://auth.engstrom.live/application/o/nextcloud/.well-known/openid-configuration' \
    --mapping-groups=groups --group-provisioning=1"
```

**Fish:**

```fish
set CID (kubectl get secret nextcloud-secret -n family -o jsonpath='{.data.OIDC_CLIENT_ID}' | base64 -d)
set CSEC (kubectl get secret nextcloud-secret -n family -o jsonpath='{.data.OIDC_CLIENT_SECRET}' | base64 -d)
kubectl exec -n family deploy/nextcloud -- su -s /bin/bash www-data -c \
  "php occ user_oidc:provider authentik --clientid='$CID' --clientsecret='$CSEC' --discoveryuri='https://auth.engstrom.live/application/o/nextcloud/.well-known/openid-configuration' --mapping-groups=groups --group-provisioning=1"
```

**OBS:** `su www-data` tar bort env vars — kör inte provider-setup med `$OIDC_CLIENT_ID` inuti podden utan explicita värden.

---

## Problem 6: Cron / admin-varningar

**Symptom:** *Cron senaste körning för X dagar sedan*; `kubectl get cronjob -n family` tom.

**Fix:** `cronjob.enabled: true` i Helm. Verifiera:

```bash
kubectl get cronjob -n family
kubectl exec -n family deploy/nextcloud -- su -s /bin/bash www-data -c \
  "php -f /var/www/html/cron.php -- --verbose"
```

**Mimetype-migration:** Kör manuellt en gång:

```bash
kubectl exec -n family deploy/nextcloud -- su -s /bin/bash www-data -c \
  "php occ maintenance:repair --include-expensive"
```

---

## Problem 7: container not found ("nextcloud")

**Symptom:** `kubectl exec` failar — podden i CrashLoopBackOff.

**Orsak:** Hook eller init failar innan huvudcontainern startar.

**Fix:** `kubectl logs -n family deploy/nextcloud --previous`. Ofta `before-starting`-hook. Vänta på rollout eller fixa hook i Git.

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
