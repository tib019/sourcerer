# ADR-008: Audio-Overview — TTS hinter Provider-Interface

**Status:** akzeptiert

## Kontext
Stretch-Feature aus CONTEXT.md §2: kurze gesprochene Zusammenfassung der Notebook-Quellen
(NotebookLM-„Audio Overview"-Analogie). Es braucht Text-to-Speech — eine weitere externe
Abhängigkeit, die in CI/Tests nicht verfügbar sein darf.

## Entscheidung
Gleiche Architektur wie bei LLM/Embeddings (ADR-006): `TTSProvider` als ABC,
`OpenAITTS` (tts-1, ein API-Call) produktiv, `FakeTTS` für Tests/CI/Offline-Demo.
Der Fake erzeugt ein **echtes, abspielbares WAV** (generierter Sinuston) statt eines
Byte-Dummys — Player, API-Vertrag und E2E laufen damit vollständig offline.
Die Zusammenfassung selbst kommt aus dem vorhandenen `LLMProvider`
(`AudioOverviewService` = Repository → Summary-Prompt → TTS, per DI komponiert).

## Alternativen
- **Browser-SpeechSynthesis (client-seitig):** keine Server-Kosten, aber Qualität und
  Stimmen inkonsistent; Summary bräuchte trotzdem einen LLM-Call.
- **Audio-Fixture im Repo für Tests:** totes Binärartefakt; generiertes WAV ist
  deterministisch und dokumentiert sich im Code.
- **Eigener TTS-Stack (Coqui etc.):** Betriebsaufwand, widerspricht „ein API-Call,
  kein neues System" (CONTEXT §3).

## Konsequenzen
- Audio-Overview funktioniert im fake-Modus komplett offline (Ton ist ein Sinuston —
  der Vertrag, nicht die Stimme, wird getestet).
- Kostendeckel: max. 12 Chunks gehen in den Summary-Prompt (`MAX_SUMMARY_CHUNKS`).
- Antwortformat: JSON mit base64-Audio + media_type — das Frontend baut eine Blob-URL;
  kein Audio-Hosting, kein Storage nötig.
