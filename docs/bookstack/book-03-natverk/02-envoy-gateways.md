# Envoy Gateway

Ingress i klustret hanteras av **Envoy Gateway** (Gateway API).

## Gateways

| Gateway | LoadBalancer IP | DNS | Användning |
|---------|-----------------|-----|------------|
| `envoy-internal` | 192.168.20.140 | `internal.engstrom.live` | LAN-tjänster |
| `envoy-external` | 192.168.20.142 | `external.engstrom.live` | Publikt via Cloudflare |

Namespace: `network`

## HTTPRoute-mönster

De flesta appar:

```yaml
httpRoute:
  enabled: true
  hostnames:
    - sonarr.${SECRET_DOMAIN}
  parentRefs:
    - name: envoy-internal
      namespace: network
      sectionName: https
```

## TLS

Wildcard-certifikat från cert-manager:

- Secret: `engstrom-live-production-tls`
- Domäner: `engstrom.live`, `*.engstrom.live`

## Policies

- HTTPS redirect (ClientTrafficPolicy)
- BackendTrafficPolicy för timeouts
- **SecurityPolicy** för Authentik forward-auth (media *arr)

## Trusted proxies (Nextcloud)

Nextcloud litar på privata nät (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`) i `proxy.config.php`.
