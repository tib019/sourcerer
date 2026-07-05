# ADR-009: URL-Import mit SSRF-Härtung

**Status:** akzeptiert

## Kontext
Nutzer sollen Webseiten als Quelle importieren können. Ein Server, der beliebige URLs
abruft, ist ein klassisches SSRF-Einfallstor: interne Dienste (Cloud-Metadata unter
169.254.169.254, Datenbanken, Admin-Panels) wären über den Backend-Server erreichbar.

## Entscheidung
Eigener `WebPageFetcher` (DI-fähig) mit Defense-in-Depth, jede Maßnahme einzeln getestet:

1. **Schema-Whitelist:** nur `http`/`https`.
2. **Adress-Blockliste nach DNS-Auflösung:** private (10/8, 172.16/12, 192.168/16,
   fc00::/7), Loopback (127/8, ::1), Link-Local (169.254/16 inkl. Metadata-Endpoint),
   Multicast, reservierte und unspezifizierte Bereiche → `UrlNotAllowedError` (400).
3. **Redirects manuell** (max. 3) statt `follow_redirects` — **jeder Hop** durchläuft
   die Adress-Prüfung erneut (Redirect auf internes Ziel wird geblockt).
4. **Timeout 10 s**, expliziter User-Agent.
5. **Größen-Deckel 5 MB** im Stream (Abbruch, kein Vollpuffer) → 422.
6. **Content-Type-Whitelist** `text/html`/`text/plain` → sonst 422.
7. **Extraktion** (BeautifulSoup, Boilerplate raus) — leerer Text → 422, kein leerer
   Ingest. Erfolgreicher Text läuft durch den **normalen** Ingest-Pfad, die URL wird
   als Herkunfts-Metadatum gespeichert.

## Alternativen
- **Kein URL-Import:** sicherste Option, aber ein Kern-Feature des Vorbilds.
- **Fetch im Frontend/Browser:** CORS macht das praktisch unmöglich; zudem wäre der
  Inhalt clientseitig manipulierbar.
- **Externer Fetch-Dienst (z. B. Jina Reader):** verlagert das Problem, neue
  Abhängigkeit + Datenabfluss.

## Konsequenzen
- Tests komplett ohne Netz (httpx.MockTransport, DNS gemockt) — 20 Testfälle
  inkl. aller Block-Kategorien.
- **Bekannte Restlücke (Demo-Scope):** DNS-Rebinding — zwischen Prüfung und
  Verbindungsaufbau könnte ein Angreifer den DNS-Eintrag umbiegen. Produktion:
  Auflösung pinnen (Connect auf geprüfte IP + Host-Header) oder Egress-Proxy.
- Importierte Seiten sind untrusted Input wie alle Quellen — die
  Prompt-Injection-Maßnahmen (delimitierte Blöcke, Daten-nicht-Anweisungen) greifen
  unverändert (NOTES §5).
