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

Officiell SQL ([Xibo KB](https://account.xibosignage.com/docs/setup/how-do-i-reset-the-xibo-admin-account-password)) — efter körning är lösenordet **`password`** tills du byter det i CMS.

### Vanliga fel → "Error in SQL syntax"

1. **Klistra SQL i PowerShell** — backticks ( \` ) är escape i PowerShell och trasar kommandot. Kör **mysql interaktivt inuti podden** (steg 1–3 nedan).
2. **"Smarta" citattecken** från webb/docs (`‘password’`) — MySQL vill ha **raka apostrofer** ASCII: `'password'`.
3. **Fel databas** — kör `USE cms;` om prompten inte redan visar `Database: cms`.
4. Tabellen heter **`user`** (reserverat ord) — **backticks runt tabellnamnet** måste vara raka: \`user\`.

### Rekommenderat (interaktivt)

```bash
kubectl exec -it -n selfhosted deploy/xibo-cms -c app -- bash
```

Inuti podden (lösenord = `MYSQL_PASSWORD` från 1Password):

```bash
mysql -h xibo-mysql -u cms -p cms
```

Vid prompten `mysql>` — **skriv eller klistra bara här** (inte i PowerShell):

```sql
USE cms;
UPDATE `user` SET UserPassword = MD5('password'), CSPRNG = 0 WHERE UserID = 1 LIMIT 1;
```

Om apostrofer fortfarande strular, prova **dubbelcitattecken** runt ordet password (community-fix):

```sql
UPDATE `user` SET UserPassword = MD5("password"), CSPRNG = 0 WHERE UserID = 1 LIMIT 1;
```

Kontroll:

```sql
SELECT UserID, UserName FROM `user` WHERE UserID = 1;
```

Avsluta med `EXIT;`.

Logga in på webben som **`xibo_admin` / `password`** och byt lösenord direkt.

### SQL lyckades men inloggning fungerar ändå

Xibo 4 sparar lösenord på tre sätt (`CSPRNG` styr vilken):

| CSPRNG | Verifiering |
|--------|-------------|
| **0** | MD5 i kolumnen `UserPassword` (32 tecken hex) |
| **1** | PBKDF2-hash |
| **2** | `password_hash()` / bcrypt (vanligt på nya konton) |

Om `UserPassword` sattes med `MD5(...)` men **`CSPRNG` fortfarande är 1 eller 2** misslyckas login trots “1 row affected”.

**Diagnostik** (vid `mysql>`):

```sql
USE cms;
SELECT UserID, UserName, CSPRNG, retired, LEFT(UserPassword, 40) AS pwd_prefix, CHAR_LENGTH(UserPassword) AS pwd_len
FROM `user`
WHERE UserID = 1 OR UserName = 'xibo_admin';
```

- Användarnamn ska vara exakt **`xibo_admin`** (inte `admin`).
- **`retired`** ska vara **0**.
- För MD5-reset: **`CSPRNG = 0`** och **`pwd_len = 32`**.

**Fix A — legacy MD5 (sätter hash explicit, inget `MD5()` i klienten):**

```sql
UPDATE `user`
SET UserPassword = '5f4dcc3b5aa765d61d8327deb882cf99',
    CSPRNG = 0,
    retired = 0
WHERE UserName = 'xibo_admin'
LIMIT 1;
```

(`5f4dcc3b5aa765d61d8327deb882cf99` = MD5 av ordet `password`.)

**Fix B — rekommenderat för CMS 4.5 (bcrypt, `CSPRNG = 2`):**

Inuti CMS-podden:

```bash
php -r "echo password_hash('password', PASSWORD_DEFAULT), PHP_EOL;"
```

Kopiera hela raden som börjar med `$2y$...`, sedan i `mysql>` (byt ut `<HASH>`):

```sql
UPDATE `user`
SET UserPassword = '<HASH>',
    CSPRNG = 2,
    retired = 0
WHERE UserName = 'xibo_admin'
LIMIT 1;
```

Logga in som **`xibo_admin` / `password`**. Starta om CMS om det fortfarande strular:

```bash
kubectl rollout restart deployment/xibo-cms -n selfhosted
```

**CMS-loggar vid misslyckad login:**

```bash
kubectl logs -n selfhosted deploy/xibo-cms -c app --tail=80
```

Testa **inkognito** så gamla cookies inte stör.

### Ett kommando (körs inuti podden, undviker PowerShell)

Kör först `kubectl exec -it ... bash`, sedan **inuti podden**:

```bash
mysql -h xibo-mysql -u cms -p"$MYSQL_PASSWORD" cms -e "UPDATE \`user\` SET UserPassword=MD5('password'), CSPRNG=0 WHERE UserID=1 LIMIT 1;"
```

(`MYSQL_PASSWORD` finns i miljön i CMS-containern via `xibo-secret`.)

## Spelare (XMR)

- LoadBalancer: `192.168.20.145:9505`
- VLAN 10 → Servers: tillåt TCP 9505 till `.145` (OPNsense)
- CMS-inställning: samma XMR-adress för displays

## Secrets (1Password)

Post **`xibo`**: fält `MYSQL_PASSWORD`, `MYSQL_ROOT_PASSWORD` (alfanumeriskt). ExternalSecret använder `remoteRef` (`xibo/MYSQL_PASSWORD`), inte `extract` — undvik duplicerade fältetiketter i 1Password.
