# Nextcloud — användare, grupper och skeleton

Dokumenterat aug 2026 efter OIDC, group folders och skeleton var på plats.

## Identitetsmodell

| Vad | Var sköts det |
|-----|----------------|
| Inloggning (SSO) | **Authentik** (lösenord + **MFA**) |
| Lösenordsåterställning | **Authentik** recovery flow |
| Användarkonto i Nextcloud | Skapas automatiskt vid första OIDC-login (JIT) |
| Gruppmedlemskap `Familj` | **Authentik** → group provisioning → Nextcloud |
| Delade mappar (group folders) | **Nextcloud** (kopplas till gruppen `Familj`) |
| Personlig startstruktur | **Skeleton directory** |

**Authentik är källan** för vem som får logga in och vilken grupp de tillhör. Nextcloud sköter filer och delning.

---

## OIDC — group provisioning

### Authentik

1. Skapa grupp **`Familj`** under Directory → Groups
2. Lägg familjemedlemmar i gruppen
3. (Valfritt) Scope mapping som skickar `groups` i token — se [Authentik Nextcloud-integration](https://docs.goauthentik.io/integrations/services/nextcloud/)

**Client ID och Client Secret** i 1Password (`nextcloud`-item) måste matcha Authentik-providern exakt. Authentik är källan — kopiera värdena därifrån till 1Password, inte tvärtom.

### Nextcloud

Provider konfigureras med group provisioning:

```bash
kubectl exec -n family deploy/nextcloud -- su -s /bin/bash www-data -c \
  "php occ user_oidc:provider authentik \
    --clientid='<CLIENT_ID>' \
    --clientsecret='<CLIENT_SECRET>' \
    --discoveryuri='https://auth.engstrom.live/application/o/nextcloud/.well-known/openid-configuration' \
    --mapping-groups=groups \
    --group-provisioning=1"
```

Hooks i `helmrelease.yaml` (`before-starting`) installerar `user_oidc` och konfigurerar providern vid pod-start.

### Verifiera

```bash
kubectl exec -n family deploy/nextcloud -- su -s /bin/bash www-data -c "php occ user:list"
kubectl exec -n family deploy/nextcloud -- su -s /bin/bash www-data -c "php occ group:list Familj"
```

OIDC-användare får ofta ett **hash-liknande användarnamn** (Authentiks `sub`/UUID). Display name syns i `occ user:list`.

Efter ändrad gruppmedlemskap i Authentik: användaren måste **logga in igen** för att synkas.

---

## Group folders

Appen **Group folders** (`groupfolders`) ger delade mappar kopplade till grupper.

### Rekommenderad struktur

**Personlig skeleton** (per användare):

```
Privat/
Mina dokument/
Mina bilder/
```

**Group folder `Familj`** (delad):

```
Familj/
├── Bilder och videor/
├── Dokument/
├── Planering/
└── Arkiv/
```

### Setup (UI, en gång)

1. `occ app:install groupfolders` (om inte redan installerad)
2. Skapa grupp `Familj` i Nextcloud om den inte redan finns via OIDC
3. Group folders-appen → skapa mapp → koppla till gruppen **`Familj`**

---

## Skeleton directory

Standardmappar kopieras till **nya** användares `files/` vid första login. Befintliga användare påverkas inte.

### Sökväg

| Var | Sökväg |
|-----|--------|
| TrueNAS (NFS) | `/mnt/NFS/family/nextcloud/data/__skeleton/` |
| I podden | `/var/www/html/data/__skeleton/` |

### Skapa mallen

```bash
kubectl exec -n family deploy/nextcloud -- sh -c \
  "mkdir -p '/var/www/html/data/__skeleton/Privat' \
    '/var/www/html/data/__skeleton/Mina dokument' \
    '/var/www/html/data/__skeleton/Mina bilder' && \
   chown -R 33:33 /var/www/html/data/__skeleton"
```

### Peka Nextcloud dit

```bash
kubectl exec -n family deploy/nextcloud -- su -s /bin/bash www-data -c \
  "php occ config:system:set skeletondirectory --value='/var/www/html/data/__skeleton'"
```

Stäng av skeleton helt: sätt värdet till tom sträng `''`.

**GitOps (valfritt):** lägg `skeletondirectory` i `nextcloud.configs` i `helmrelease.yaml`.

---

## Break-glass admin

Lokal `admin` finns kvar från installation. Behåll som nödfall om Authentik/OIDC strular.

Inloggning: `https://cloud.engstrom.live/login?direct=1` (lokal backend).

---

## Checklista — ny familjemedlem

1. Skapa användare i **Authentik** (fyll i **e-post** — krävs för recovery)
2. Lägg i grupp **`Familj`**
3. Ge access till Application **Nextcloud**
4. Användaren loggar in → lösenord → **MFA-setup** (TOTP eller passkey) → JIT-konto + skeleton + grupp `Familj`
5. Verifiera access till group folder **Familj**

Se [Authentik — MFA och recovery](../book-04-identitet/05-authentik-mfa-och-recovery.md) vid tappad telefon eller glömt lösenord.
