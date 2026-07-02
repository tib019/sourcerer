# ADR-006: Provider-Abstraktion — ein Interface, OpenAI implementiert

**Status:** akzeptiert

## Kontext
LLM-, Embedding- und Vektor-Store-Zugriffe sind externe Abhängigkeiten. Kunden-Szenario
(CorporateLLM-Analogie): „Bring Your Own Model" muss möglich sein, ohne den Kern umzubauen.

## Entscheidung
Drei Abstract Base Classes: `LLMProvider`, `EmbeddingProvider`, `VectorStore`.
Produktiv implementiert: OpenAI (GPT-4o, text-embedding-3-small) und Pinecone.
Zusätzlich deterministische **Fake-Implementierungen** für Tests und Offline-Betrieb
(`SOURCERER_PROVIDERS=fake`). Die Auswahl passiert per Dependency Injection an genau
einer Stelle (Composition Root in `main.py`).

## Alternativen
- **Direkter SDK-Aufruf im Pipeline-Code:** weniger Dateien, aber untestbar ohne echte
  Keys und BYOM = Umbau statt neuer Klasse.
- **Multi-Provider-Framework (LiteLLM):** löst das Problem generisch, widerspricht aber
  ADR-003 (keine unnötigen Frameworks).

## Konsequenzen
- Azure OpenAI / anderer Anbieter = eine neue Klasse, null Änderung an der Pipeline.
- Unit-, Mathe- und E2E-Tests laufen offline, deterministisch, kostenfrei in CI.
- Token-/Kosten-Logging pro Call sitzt einheitlich im Provider (Monitoring-Vorstufe,
  in Produktion: Langfuse).
