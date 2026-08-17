# Vanliga kommandon

## Kubernetes

```bash
kubectl get pods -n <namespace>
kubectl logs -n <namespace> deploy/<name> -f
kubectl describe pod -n <namespace> <pod>
kubectl exec -it -n <namespace> deploy/<name> -- bash
kubectl rollout restart deployment/<name> -n <namespace>
kubectl get pvc -n <namespace>
kubectl get httproute -n <namespace>
```

## Talos

```bash
talosctl --nodes 192.168.20.150 health
talosctl --nodes 192.168.20.151 logs kubelet
talosctl --nodes 192.168.20.150 dashboard
```

## Flux

```bash
flux get all -A
flux logs --all-namespaces --follow
flux reconcile kustomization cluster-apps -n flux-system --with-source
```

## Nextcloud (occ)

Kör alltid som **www-data**:

```bash
kubectl exec -n family deploy/nextcloud -- su -s /bin/bash www-data -c "php occ status"
kubectl exec -n family deploy/nextcloud -- su -s /bin/bash www-data -c "php occ app:list"
kubectl exec -n family deploy/nextcloud -- su -s /bin/bash www-data -c "php occ user:list"
kubectl exec -n family deploy/nextcloud -- su -s /bin/bash www-data -c "php occ group:list Familj"
kubectl get cronjob -n family
```

## Authentik

```bash
kubectl exec -n authentik deploy/authentik-server -- ls -la /data/media
kubectl exec -n authentik deploy/authentik-server -- ak test_email mottagare@example.com
flux reconcile externalsecret nextcloud -n family --force
```

MFA/recovery (UI): [Authentik — MFA och recovery](../book-04-identitet/05-authentik-mfa-och-recovery.md).

| Admin-uppgift | Var |
|---------------|-----|
| Tappad MFA-enhet | Directory → Users → MFA Authenticators → Delete |
| Lösenordsåterställning | Email recovery link / Forgot password |

## Secrets (base64-dekod)

```bash
kubectl get secret -n family nextcloud-secret -o jsonpath='{.data.nextcloud-password}' | base64 -d; echo
```

## DNS från pod

```bash
kubectl exec -n family deploy/nextcloud -- getent hosts nextcloud-postgresql
```

## Port-forward (debug)

```bash
kubectl port-forward -n family svc/nextcloud 8080:80
```

## Repo (lokal)

```bash
cd ~/Dokument/home-ops
git pull
# .venv om python-verktyg behövs
```
