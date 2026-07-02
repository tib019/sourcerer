"""Extraktions-Tests: Plaintext (Encodings) + PDF (pypdf, generiertes Fixture)."""

import pytest

from app.errors import EmptyDocumentError
from app.ingest.extractor import PdfExtractor, PlainTextExtractor


def _minimal_pdf(text: str) -> bytes:
    """Erzeugt ein minimales einseitiges PDF mit pypdf + Roh-Content-Stream."""
    import io

    from pypdf import PdfWriter
    from pypdf.generic import DictionaryObject, NameObject, StreamObject

    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)

    content = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode("latin-1")
    stream = StreamObject()
    stream.set_data(content)
    page[NameObject("/Contents")] = writer._add_object(stream)

    font = DictionaryObject()
    font[NameObject("/Type")] = NameObject("/Font")
    font[NameObject("/Subtype")] = NameObject("/Type1")
    font[NameObject("/BaseFont")] = NameObject("/Helvetica")
    fonts = DictionaryObject()
    fonts[NameObject("/F1")] = writer._add_object(font)
    resources = DictionaryObject()
    resources[NameObject("/Font")] = fonts
    page[NameObject("/Resources")] = resources

    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


class TestPlainTextExtractor:
    def test_utf8(self):
        pages = PlainTextExtractor().extract("Straße über Ärger.".encode())
        assert pages == [pages[0]]
        assert pages[0].page == 1
        assert pages[0].text == "Straße über Ärger."

    def test_latin1_fallback(self):
        pages = PlainTextExtractor().extract("Straße".encode("latin-1"))
        assert "Stra" in pages[0].text  # dekodierbar ohne Exception

    def test_empty_raises(self):
        with pytest.raises(EmptyDocumentError):
            PlainTextExtractor().extract(b"   \n ")


class TestPdfExtractor:
    def test_extracts_text_with_page_number(self):
        pdf = _minimal_pdf("Hello Sourcerer PDF")
        pages = PdfExtractor().extract(pdf)
        assert len(pages) == 1
        assert pages[0].page == 1
        assert "Hello Sourcerer PDF" in pages[0].text

    def test_pdf_without_text_raises(self):
        import io

        from pypdf import PdfWriter

        writer = PdfWriter()
        writer.add_blank_page(width=612, height=792)
        buffer = io.BytesIO()
        writer.write(buffer)

        with pytest.raises(EmptyDocumentError):
            PdfExtractor().extract(buffer.getvalue())
