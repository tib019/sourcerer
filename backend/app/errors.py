"""Domain-Fehler — main.py mappt sie auf HTTP-Statuscodes."""


class SourcererError(Exception):
    """Basisklasse aller Domain-Fehler."""


class UnsupportedFileTypeError(SourcererError):
    """Dateityp nicht in der Whitelist (PDF, Plaintext)."""


class FileTooLargeError(SourcererError):
    """Upload überschreitet das Größenlimit."""


class EmptyDocumentError(SourcererError):
    """Dokument enthält keinen extrahierbaren Text (z. B. Scan-PDF)."""


class NotebookNotFoundError(SourcererError):
    """Unbekannte Notebook-ID."""


class DocumentNotFoundError(SourcererError):
    """Unbekannte Dokument-ID (oder Dokument gehört zu einem anderen Notebook)."""
