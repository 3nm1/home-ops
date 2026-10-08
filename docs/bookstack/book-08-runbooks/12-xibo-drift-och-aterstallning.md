# Xibo — drift och återställning

Stack: `kubernetes/apps/selfhosted/xibo/` — baserad på [xibosignage/xibo-docker](https://github.com/xibosignage/xibo-docker).

## Image-versioner (ska matcha upstream)

| Komponent | Image | Tag |
|-----------|--------|-----|
| CMS | `ghcr.io/xibosignage/xibo-cms` | `release-4.5.3` |
| MySQL | `docker.io/library/mysql` | **`8.4`** |
| XMR | `ghcr.io/xibosignage/xibo-xmr` | `1.3` |
| QuickChart | `docker.io/ianw/quickchart` | `v1.8.1` |

**Renovate** uppdaterar inte Xibo-containers automatiskt (se `.renovaterc.json5`). Bumps görs manuellt när `xibo-docker` release uppdateras.

## Fel MySQL-tag (t.ex. `26.7`)

Renovate kan föreslå ogiltiga MySQL-taggar. Xibo CMS 4.5 kräver **MySQL 8.4** — inte MariaDB, inte MySQL 9.x utan verifiering.

Efter att Git är rättat:

```bash
flux reconcile kustomization xibo -n selfhosted --with-source
flux reconcile helmrelease xibo-mysql -n selfhosted --force
```

Om MySQL startat med fel image mot befintlig Longhorn-volym och CMS inte loggar in: se Xibo KB [reset xibo_admin](https://account.xibosignage.com/docs/setup/how-do-i-reset-the-xibo-admin-account-password) eller återställ från backup.

## Admin-lösenord glömt

Från CMS-podden:

```bash
kubectl exec -it -n selfhosted deploy/xibo-cms -c app -- bash
mysql -h xibo-mysql -u cms -p cms
```

```sql
UPDATE `user` SET `UserPassword` = MD5('password'), `CSPRNG` = 0 WHERE `UserID` = 1 LIMIT 1;
```

Logga in som `xibo_admin` / `password` och byt lösenord direkt.

## Spelare (XMR)

- LoadBalancer: `192.168.20.145:9505`
- VLAN 10 → Servers: tillåt TCP 9505 till `.145` (OPNsense)
- CMS-inställning: samma XMR-adress för displays

## Secrets (1Password)

Post **`xibo`**: fält `MYSQL_PASSWORD`, `MYSQL_ROOT_PASSWORD` (alfanumeriskt). ExternalSecret använder `remoteRef` (`xibo/MYSQL_PASSWORD`), inte `extract` — undvik duplicerade fältetiketter i 1Password.
