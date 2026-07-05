"""URL-Import: SSRF-Härtung + Fehlerpfade + Erfolgsfall — komplett gemockt, kein Netz."""

import socket

import httpx
import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.errors import EmptyDocumentError, UrlFetchFailedError, UrlNotAllowedError
from app.ingest.url_fetcher import WebPageFetcher
from app.main import create_app

PUBLIC_IP = "93.184.216.34"  # beispielhafte oeffentliche Adresse


@pytest.fixture(autouse=True)
def no_real_dns(monkeypatch):
    """DNS immer auf eine oeffentliche Adresse aufloesen — echte Aufloesung waere Netz."""

    def fake_getaddrinfo(host, *args, **kwargs):
        if host == "internal.example":
            return [(socket.AF_INET, None, None, "", ("10.0.0.5", 0))]
        return [(socket.AF_INET, None, None, "", (PUBLIC_IP, 0))]

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)


def _fetcher(handler, **kwargs) -> WebPageFetcher:
    return WebPageFetcher(transport=httpx.MockTransport(handler), **kwargs)


def _html_response(body: str, content_type: str = "text/html") -> httpx.Response:
    return httpx.Response(200, headers={"content-type": content_type}, text=body)


class TestSSRFGuard:
    @pytest.mark.parametrize(
        "url",
        [
            "ftp://example.com/datei",
            "file:///etc/passwd",
            "http://127.0.0.1/admin",
            "http://10.1.2.3/",
            "http://172.16.0.1/",
            "http://192.168.1.1/router",
            "http://169.254.169.254/latest/meta-data/",
            "http://[::1]/",
            "http://[fc00::1]/",
            "http://0.0.0.0/",
        ],
    )
    def test_private_and_nonhttp_urls_are_blocked(self, url):
        fetcher = _fetcher(lambda request: _html_response("<p>nie erreicht</p>"))
        with pytest.raises(UrlNotAllowedError):
            fetcher.fetch(url)

    def test_hostname_resolving_to_private_ip_is_blocked(self):
        fetcher = _fetcher(lambda request: _html_response("<p>nie erreicht</p>"))
        with pytest.raises(UrlNotAllowedError):
            fetcher.fetch("http://internal.example/seite")

    def test_redirect_to_private_target_is_blocked(self):
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.host == "start.example":
                return httpx.Response(302, headers={"location": "http://169.254.169.254/"})
            return _html_response("<p>nie erreicht</p>")

        with pytest.raises(UrlNotAllowedError):
            _fetcher(handler).fetch("http://start.example/")

    def test_too_many_redirects_fail_cleanly(self):
        handler = lambda request: httpx.Response(  # noqa: E731
            302, headers={"location": "http://weiter.example/"}
        )
        with pytest.raises(UrlFetchFailedError, match="Redirects"):
            _fetcher(handler).fetch("http://start.example/")


class TestFetchGuards:
    def test_wrong_content_type_rejected(self):
        fetcher = _fetcher(
            lambda request: httpx.Response(
                200, headers={"content-type": "image/png"}, content=b"\x89PNG"
            )
        )
        with pytest.raises(UrlFetchFailedError, match="Content-Type"):
            fetcher.fetch("https://example.com/bild.png")

    def test_oversized_body_aborts(self):
        fetcher = _fetcher(
            lambda request: _html_response("<p>" + "x" * 500 + "</p>"), max_bytes=100
        )
        with pytest.raises(UrlFetchFailedError, match="zu groß"):
            fetcher.fetch("https://example.com/riesig")

    def test_http_error_status_rejected(self):
        fetcher = _fetcher(lambda request: httpx.Response(404, text="nicht da"))
        with pytest.raises(UrlFetchFailedError, match="404"):
            fetcher.fetch("https://example.com/fehlt")

    def test_empty_extraction_rejected(self):
        fetcher = _fetcher(
            lambda request: _html_response("<html><script>nur();skript();</script></html>")
        )
        with pytest.raises(EmptyDocumentError):
            fetcher.fetch("https://example.com/leer")


class TestSuccess:
    HTML = """<html><head><title>Vulkan-Wissen</title><script>boese()</script></head>
    <body><nav>Menu Menu</nav><p>Der Vesuv liegt am Golf von Neapel.</p>
    <footer>Impressum</footer></body></html>"""

    def test_extracts_title_and_text_without_boilerplate(self):
        fetcher = _fetcher(lambda request: _html_response(self.HTML))
        page = fetcher.fetch("https://example.com/vulkane")
        assert page.title == "Vulkan-Wissen"
        assert "Vesuv" in page.text
        assert "boese" not in page.text and "Menu" not in page.text
        assert "Impressum" not in page.text

    def test_api_flow_url_becomes_citable_source(self):
        fetcher = _fetcher(lambda request: _html_response(self.HTML))
        client = TestClient(create_app(Settings(providers="fake"), url_fetcher=fetcher))
        nb = client.post("/notebooks", json={"name": "NB"}).json()["id"]

        response = client.post(
            f"/notebooks/{nb}/documents/url", json={"url": "https://example.com/vulkane"}
        )
        assert response.status_code == 201
        body = response.json()
        assert body["name"] == "Vulkan-Wissen"
        assert body["source_url"] == "https://example.com/vulkane"

        docs = client.get(f"/notebooks/{nb}/documents").json()
        assert docs[0]["source_url"] == "https://example.com/vulkane"

        chat = client.post(
            f"/notebooks/{nb}/chat", json={"question": "Wo liegt der Vesuv?"}
        ).json()
        assert "Neapel" in chat["answer"]
        assert chat["citations"][0]["document_name"] == "Vulkan-Wissen"

    def test_api_blocked_url_returns_400(self):
        client = TestClient(
            create_app(
                Settings(providers="fake"),
                url_fetcher=_fetcher(lambda request: _html_response("x")),
            )
        )
        nb = client.post("/notebooks", json={"name": "NB"}).json()["id"]
        response = client.post(
            f"/notebooks/{nb}/documents/url", json={"url": "http://127.0.0.1/geheim"}
        )
        assert response.status_code == 400
        assert "geblockt" in response.json()["detail"] or "intern" in response.json()["detail"]
