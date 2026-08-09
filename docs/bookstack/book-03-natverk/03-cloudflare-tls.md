# Cloudflare och TLS

## Extern åtkomst

```
Användare → Cloudflare → Cloudflare Tunnel → envoy-external → HTTPRoute → Pod
```

## Komponenter (namespace `network`)

| App | Roll |
|-----|------|
| **cloudflare-tunnel** | Wildcard `*.engstrom.live` → internal LB |
| **cloudflare-dns** (external-dns) | Skapar DNS-poster för external gateway |
| **cert-manager** | Let's Encrypt via DNS-01 (Cloudflare API) |

## Publika appar (exempel)

- Jellyfin (`jellyfin.engstrom.live`) — internal + external
- Seerr — internal + external, OIDC
- Authentik — internal + external
- echo (test)

De flesta *arr-appar är **endast internal** + forward-auth.

## cert-manager

- ClusterIssuer med Cloudflare DNS-01
- Automatisk förnyelse av wildcard-cert

## Intern DNS

`k8s-gateway` i klustret — in-cluster DNS för `*.engstrom.live` mot gateways.
