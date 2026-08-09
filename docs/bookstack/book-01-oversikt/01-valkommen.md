# Välkommen och syfte

Det här är dokumentationen för **Engström Home Lab** — ett Talos/Kubernetes-baserat hemmanätverk som drivs med GitOps.

## Varför finns detta?

- **Komma ihåg** vad vi byggt och varför (om ett halvår har man glömt halva kontexten).
- **Onboarda** framtida mig (eller familj) utan att gräva i YAML.
- **Felsöka** snabbare med runbooks och kända problem dokumenterade.

## Källkod

| Resurs | Plats |
|--------|--------|
| GitOps-repo | `github.com/3nm1/home-ops` |
| Kluster-API | `lab.engstrom.live` / VIP `192.168.20.150` |
| Publikt domän | `engstrom.live` |
| Dokumentation (markdown) | `docs/bookstack/` i repot |
| Dokumentation (webb) | `bookstack.engstrom.live` |

## Tre principer

1. **Automatisera allt** — Flux ska vara source of truth, inte manuella `kubectl`-ändringar.
2. **Dokumentera allt** — inklusive misstag (de är oftast mest värdefulla).
3. **Kunna bygga om** — om klustret dör ska Git räcka för att återskapa det.

## Baserat på

Projektet utgår från [onedr0p/cluster-template](https://github.com/onedr0p/cluster-template) — Talos + Flux + SOPS + app-struktur med `ks.yaml` per app.

## Status (aug 2026)

- Plattformen är stabil och produktionslik för hemma bruk.
- Media stack är i stort sett komplett med *arr, Jellyfin, automation.
- **Familjetjänster** har startat med **Nextcloud** (milestone 1, utan Collabora).
- Profilarr har (tillfälligt) ersatt Recyclarr för TRaSH-profiler.
