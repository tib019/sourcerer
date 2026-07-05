"""WebPageFetcher — URL-Import mit SSRF-Härtung (ADR-009).

Schutzmaßnahmen (jede einzeln getestet):
- nur http/https
- Host wird aufgelöst; private, Loopback-, Link-Local- (inkl. 169.254.169.254),
  Multicast- und reservierte Bereiche sind geblockt — für JEDEN Redirect-Hop erneut
- Timeout 10 s, expliziter User-Agent, Redirects manuell (max. 3) statt blind
- Response-Größe hart gedeckelt (Stream + Abbruch), Content-Type-Whitelist
- Extraktion: BeautifulSoup (script/style/nav/footer raus), Regex-Fallback

Bekannte Restlücke (Demo-Scope, in ADR-009 dokumentiert): zwischen DNS-Check und
Verbindungsaufbau könnte ein Angreifer den DNS-Eintrag umbiegen (Rebinding).
"""

from __future__ import annotations

import ipaddress
import re
import socket
from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit

import httpx

from app.errors import EmptyDocumentError, UrlFetchFailedError, UrlNotAllowedError

USER_AGENT = "Sourcerer/0.1 (+https://github.com/tib019/sourcerer)"
ALLOWED_CONTENT_TYPES = ("text/html", "text/plain")
MAX_REDIRECTS = 3

_TAG = re.compile(r"<[^>]+>")
_DROP_BLOCKS = re.compile(
    r"<(script|style|noscript|nav|header|footer|iframe)\b.*?</\1>",
    re.IGNORECASE | re.DOTALL,
)
_TITLE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)


@dataclass(frozen=True)
class FetchedPage:
    title: str
    text: str
    url: str


def _assert_public_host(url: str) -> None:
    """Wirft UrlNotAllowedError, wenn Schema oder Ziel-Adresse nicht erlaubt sind."""
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https"):
        raise UrlNotAllowedError(f"Nur http/https erlaubt (nicht '{parts.scheme}').")
    host = parts.hostname
    if not host:
        raise UrlNotAllowedError("URL enthält keinen Host.")

    try:
        addresses = [ipaddress.ip_address(host)]
    except ValueError:
        try:
            infos = socket.getaddrinfo(host, None)
        except OSError as exc:
            raise UrlFetchFailedError(f"Host '{host}' nicht auflösbar.") from exc
        addresses = [ipaddress.ip_address(info[4][0]) for info in infos]

    for address in addresses:
        if (
            address.is_private
            or address.is_loopback
            or address.is_link_local
            or address.is_multicast
            or address.is_reserved
            or address.is_unspecified
        ):
            raise UrlNotAllowedError(
                f"Ziel-Adresse {address} liegt in einem internen Bereich — geblockt."
            )


def _extract(html: str) -> tuple[str, str]:
    """(Titel, Text) aus HTML — BeautifulSoup, mit Regex-Fallback."""
    try:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript", "nav", "header", "footer", "iframe"]):
            tag.decompose()
        title = (soup.title.string or "").strip() if soup.title else ""
        return title, soup.get_text(" ", strip=True)
    except ImportError:  # pragma: no cover - bs4 ist installiert; Fallback fuer Notfaelle
        title_match = _TITLE.search(html)
        stripped = _TAG.sub(" ", _DROP_BLOCKS.sub(" ", html))
        return (
            title_match.group(1).strip() if title_match else "",
            " ".join(stripped.split()),
        )


class WebPageFetcher:
    """Holt eine Webseite als Text — mit allen Leitplanken aus ADR-009.

    `transport` ist für Tests injizierbar (httpx.MockTransport) — kein echter
    Netzabruf in der Testsuite.
    """

    def __init__(
        self,
        timeout: float = 10.0,
        max_bytes: int = 5 * 1024 * 1024,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._timeout = timeout
        self._max_bytes = max_bytes
        self._transport = transport

    def fetch(self, url: str) -> FetchedPage:
        with httpx.Client(
            timeout=self._timeout,
            transport=self._transport,
            follow_redirects=False,
            headers={"User-Agent": USER_AGENT},
        ) as client:
            for _ in range(MAX_REDIRECTS + 1):
                _assert_public_host(url)
                with client.stream("GET", url) as response:
                    if response.is_redirect:
                        location = response.headers.get("location")
                        if not location:
                            raise UrlFetchFailedError("Redirect ohne Ziel.")
                        url = urljoin(url, location)
                        continue
                    return self._read(response, url)
            raise UrlFetchFailedError(f"Zu viele Redirects (max. {MAX_REDIRECTS}).")

    def _read(self, response: httpx.Response, url: str) -> FetchedPage:
        if response.status_code >= 400:
            raise UrlFetchFailedError(f"Abruf fehlgeschlagen (HTTP {response.status_code}).")
        content_type = response.headers.get("content-type", "").split(";")[0].strip().lower()
        if content_type not in ALLOWED_CONTENT_TYPES:
            raise UrlFetchFailedError(
                f"Content-Type '{content_type or 'unbekannt'}' wird nicht unterstützt "
                f"(erlaubt: {', '.join(ALLOWED_CONTENT_TYPES)})."
            )

        chunks: list[bytes] = []
        received = 0
        for chunk in response.iter_bytes():
            received += len(chunk)
            if received > self._max_bytes:
                raise UrlFetchFailedError(
                    f"Seite zu groß (> {self._max_bytes // (1024 * 1024)} MB)."
                )
            chunks.append(chunk)
        body = b"".join(chunks).decode(response.charset_encoding or "utf-8", errors="replace")

        if content_type == "text/plain":
            title, text = "", body.strip()
        else:
            title, text = _extract(body)
        if not text.strip():
            raise EmptyDocumentError("Seite enthält keinen extrahierbaren Text.")
        return FetchedPage(title=title or urlsplit(url).hostname or url, text=text, url=url)
