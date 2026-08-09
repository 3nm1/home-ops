# BookStack-dokumentation — Home Lab

Markdown-källor för [BookStack](https://bookstack.engstrom.live) (`selfhosted`-namespace).

Innehållet speglar **BookStacks hierarki**: Hylla → Bok → Kapitel → Sida. Varje `.md`-fil motsvarar en **sida**; mappnamn motsvarar böcker/kapitel.

## Importera till BookStack

1. Logga in på `https://bookstack.engstrom.live` (Authentik OIDC).
2. Skapa hyllan **Engström Home Lab** (om den inte finns).
3. För varje undermapp `book-XX-*`:
   - Skapa en **bok** med samma namn som i `STRUCTURE.md`.
   - Skapa **kapitel** enligt filnamnsprefix (t.ex. alla sidor i samma bok kan ligga i ett kapitel per tema).
   - Öppna varje sida → **Redigera** → klistra in markdown (BookStack stödjer markdown i editorn).
4. Alternativ: använd BookStacks **Import** (Inställningar → Import) om du exporterar hela mappen som ZIP enligt [BookStacks importformat](https://www.bookstackapp.com/docs/admin/content-import/).

> **Tips:** Börja med *Familjetjänster → Nextcloud* och *Runbooks* — det är det du mest sannolikt behöver om ett halvår.

## Källkod vs BookStack

| Plats | Innehåll |
|-------|----------|
| `docs/bookstack/` (detta repo) | Levande markdown, versionshanterad |
| BookStack PVC / MariaDB | Det du faktiskt läser i webben |
| `README.md`, `ARCHITECTURE.md`, `NETWORK.md` (repo root) | Tidiga översikter — kan länkas hit |

Uppdatera gärna **Git först**, sedan synka manuellt till BookStack tills vi ev. automatiserar import.

## Snabbreferens

| Bok | Syfte |
|-----|--------|
| 01 Översikt | Varför, hardware, resan hittills |
| 02 Plattform | Talos, Flux, secrets, storage |
| 03 Nätverk | VLAN, Envoy, Cloudflare, TLS |
| 04 Identitet | Authentik, OIDC, forward-auth |
| 05 Media | *arr, Jellyfin, automation |
| 06 Familj | Nextcloud m.m. |
| 07 Self-hosted | Homarr, BookStack, verktyg |
| 08 Runbooks | Drift, felsökning, återställning |

Se `STRUCTURE.md` för exakt sidträd.
