# BookStack-dokumentation — Home Lab

Markdown-källor för [BookStack](https://bookstack.engstrom.live) (`selfhosted`-namespace).

Innehållet speglar **BookStacks hierarki**: Hylla → Bok → Kapitel → Sida. Varje `.md`-fil motsvarar en **sida**; mappnamn motsvarar böcker/kapitel.

## Importera till BookStack

### Automatiskt (Portable ZIP)

BookStack stödjer [Portable ZIP-formatet](https://github.com/BookStackApp/BookStack/blob/development/dev/docs/portable-zip-file-format.md). Bygg en ZIP per bok från markdown i repot:

```bash
python docs/bookstack/build-portable-zip.py
# eller en bok i taget:
python docs/bookstack/build-portable-zip.py --book book-06-familj
```

ZIP-filer skapas i `docs/bookstack/dist/`. Importera i BookStack:

1. Logga in på `https://bookstack.engstrom.live` (Authentik OIDC).
2. Skapa hyllan **Engström Home Lab** (om den inte finns).
3. **Inställningar → Import** → ladda upp t.ex. `book-02-plattform.zip`.
4. Upprepa för övriga böcker (en ZIP = en bok med kapitel och sidor).

Strukturen styrs av `manifest.json` (speglar `STRUCTURE.md`). När du lägger till nya sidor: uppdatera manifest, kör scriptet igen, importera om boken (eller bara nya sidor manuellt).

### Manuellt (klistra in markdown)

1. Skapa bok/kapitel enligt `STRUCTURE.md`.
2. Öppna varje sida → **Redigera** → klistra in markdown.

> **Tips:** Börja med *Familjetjänster* och *Runbooks* — det är det du mest sannolikt behöver om ett halvår.

## Källkod vs BookStack

| Plats | Innehåll |
|-------|----------|
| `docs/bookstack/` (detta repo) | Levande markdown, versionshanterad |
| BookStack PVC / MariaDB | Det du faktiskt läser i webben |
| `README.md`, `ARCHITECTURE.md`, `NETWORK.md` (repo root) | Tidiga översikter — kan länkas hit |

Uppdatera gärna **Git först**, kör `build-portable-zip.py`, importera ZIP till BookStack.

## Snabbreferens

| Bok | Syfte |
|-----|--------|
| 01 Översikt | Varför, hardware, resan hittills |
| 02 Plattform | Talos, Flux, secrets, storage, **SMTP-relay** |
| 03 Nätverk | VLAN, Envoy, Cloudflare, TLS |
| 04 Identitet | Authentik, OIDC, forward-auth |
| 05 Media | *arr, Jellyfin, automation |
| 06 Familj | Nextcloud m.m. |
| 07 Self-hosted | Homarr, BookStack, verktyg |
| 08 Runbooks | Drift, felsökning, återställning |

Se `STRUCTURE.md` för exakt sidträd. Samma hierarki finns i `manifest.json` (används av `build-portable-zip.py`).
