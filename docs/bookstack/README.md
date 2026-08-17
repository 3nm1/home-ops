# BookStack-dokumentation — Home Lab

Markdown-källor för [BookStack](https://bookstack.engstrom.live) (`selfhosted`-namespace).

Innehållet speglar **BookStacks hierarki**: Hylla → Bok → Kapitel → Sida. Varje `.md`-fil motsvarar en **sida**; mappnamn motsvarar böcker/kapitel.

## Markdown-konvention

Varje sidfil börjar med en **H1-rubrik** (`# Sidtitel`). Den används på två sätt:

| Var | H1 |
|-----|-----|
| **Git / Cursor** | Synlig filrubrik — bra vid läsning i repot |
| **BookStack (ZIP-import)** | Blir sidans **namn**; strippas från sidinnehållet av `build-portable-zip.py` |

Innehållet under H1 börjar med `##` (eller brödtext). Då undviks dubbla rubriker i BookStack (sidnamn + samma rubrik i body).

Exempel:

```markdown
# Authentik — MFA och recovery

Dokumenterat aug 2026 …

## Översikt

…
```

**Manuell klistra-in:** hoppa över första `#`-raden i BookStack — använd bara texten från `##` och nedåt (eller kör ZIP-import).

**Valfritt i BookStack UI:** om något sidnamn fortfarande känns dubbelt, se CSS under *Inställningar → Customization → Custom HTML head content* (dölj `h1.break-text`).

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

Efter ändringar i Git: bygg om ZIP och importera på nytt — befintliga sidor uppdateras inte automatiskt i BookStack.

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
