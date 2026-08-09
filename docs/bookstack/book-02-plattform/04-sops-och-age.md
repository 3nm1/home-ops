# SOPS och age

Känsliga värden i Git krypteras med **SOPS** + **age**.

## Filer

| Fil | Innehåll |
|-----|----------|
| `.sops.yaml` | Vilka paths som krypteras |
| `kubernetes/components/sops/cluster-secrets.sops.yaml` | `SECRET_DOMAIN`, `ONEPASSWORD_VAULT` |
| `bootstrap/*.sops.yaml` | Bootstrap-secrets |
| `talos/talsecret.sops.yaml` | Talos-hemligheter |

## Dekryptering

Flux har age-nyckeln och dekrypterar vid apply. Lokalt:

```bash
sops -d kubernetes/components/sops/cluster-secrets.sops.yaml
```

## Regel

**Committa aldrig okrypterade secrets.** App-specifika lösenord ligger i **1Password** och hämtas via External Secrets — inte i SOPS (utom cluster-wide config).
