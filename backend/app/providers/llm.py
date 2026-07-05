"""LLMProvider — ABC + OpenAI-Chat und deterministischer Fake (ADR-006).

Der Fake beantwortet Fragen per Wort-Überlappung mit den nummerierten Quellen-Blöcken
aus dem Prompt — inkl. [n]-Zitat und ehrlichem "steht nicht in den Quellen".
Damit laufen der komplette Chat-Flow, die Eval-Tests und E2E offline.
"""

from __future__ import annotations

import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.providers.text_utils import content_words

logger = logging.getLogger("sourcerer.providers")

NO_ANSWER = "Dazu steht nichts in den Quellen."


@dataclass(frozen=True)
class LLMResponse:
    text: str
    prompt_tokens: int = 0
    completion_tokens: int = 0


class LLMProvider(ABC):
    @abstractmethod
    def complete(self, messages: list[dict[str, str]]) -> LLMResponse: ...


class OpenAIChat(LLMProvider):
    """GPT-4o, niedrige Temperatur (Grounding > Kreativität), Token-Logging pro Call."""

    MODEL = "gpt-4o"
    _USD_PER_1M_INPUT = 2.50
    _USD_PER_1M_OUTPUT = 10.00

    def __init__(self, api_key: str, temperature: float = 0.1) -> None:
        from openai import OpenAI

        self._client = OpenAI(api_key=api_key)
        self._temperature = temperature

    def complete(self, messages: list[dict[str, str]]) -> LLMResponse:
        response = self._client.chat.completions.create(
            model=self.MODEL, messages=messages, temperature=self._temperature
        )
        usage = response.usage
        cost = (
            usage.prompt_tokens / 1_000_000 * self._USD_PER_1M_INPUT
            + usage.completion_tokens / 1_000_000 * self._USD_PER_1M_OUTPUT
        )
        logger.info(
            "chat: %d prompt + %d completion Tokens (~$%.6f)",
            usage.prompt_tokens, usage.completion_tokens, cost,
        )
        return LLMResponse(
            text=response.choices[0].message.content or "",
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
        )


_SOURCE_BLOCK = re.compile(r"\[(\d+)\][^\n]*\n<<<\n(.*?)\n>>>", re.DOTALL)
_QUESTION_LINE = re.compile(r"^Frage:\s*(.+)$", re.MULTILINE)

_content_words = content_words


def _studio_json(task: str, sources: list[tuple[str, str]]) -> str:
    """Deterministische Studio-Outputs aus den Quellen-Blöcken (Fake-Modus).

    Kein Sprachmodell: erste Sätze der Quellen werden zu Fragen/Karten/Quiz
    verarbeitet — genug, um JSON-Schema, Zitat-Validierung und UI end-to-end
    zu testen. Fragen enthalten Wörter der Quelle, damit ein Klick auf einen
    Startfragen-Chip im Fake-Chat auch eine belegte Antwort findet.
    """
    import json as _json

    sentences: list[tuple[int, str]] = []  # (quellen_nummer, satz)
    for number, text in sources:
        for sentence in re.split(r"(?<=[.!?])\s+", text):
            sentence = sentence.strip()
            if sentence:
                sentences.append((int(number), sentence))

    def cycle(count: int) -> list[tuple[int, str]]:
        return [sentences[i % len(sentences)] for i in range(count)]

    if task == "suggested_questions":
        questions = [
            f"Worum geht es bei: {' '.join(s.split()[:4])}?" for _, s in cycle(3)
        ]
        return _json.dumps({"questions": questions})

    if task == "report":
        seen: dict[int, str] = {}
        for n, s in sentences:
            seen.setdefault(n, s)
        result_sections = [
            {"heading": f"Abschnitt {n}", "content": s, "citations": [n]}
            for n, s in list(seen.items())[:6]
        ]
        return _json.dumps({"title": "Bericht über die Quellen", "sections": result_sections})

    if task == "flashcards":
        cards = [
            {"front": f"Karte {i + 1}: Was besagt Quelle [{n}]?", "back": s, "citation": n}
            for i, (n, s) in enumerate(cycle(8))
        ]
        return _json.dumps({"cards": cards})

    if task == "quiz":
        questions = [
            {
                "question": f"Welche Aussage stammt aus Quelle [{n}]?",
                "options": [s, "Erfundene Aussage A.", "Erfundene Aussage B.",
                            "Erfundene Aussage C."],
                "answer_index": 0,
                "citation": n,
            }
            for n, s in cycle(4)
        ]
        return _json.dumps({"questions": questions})

    return _json.dumps({})


class FakeLLM(LLMProvider):
    """Deterministische Antwort aus den Quellen-Blöcken des Prompts.

    Kein Sprachmodell — bewusst simpel: bester Quellen-Block per Wort-Überlappung
    mit der Frage; der Satz mit den meisten Treffern wird zitiert. Ohne Treffer:
    NO_ANSWER. Das reicht, um Pipeline, Zitat-Mapping und UI end-to-end zu testen.
    """

    def complete(self, messages: list[dict[str, str]]) -> LLMResponse:
        system = next((m["content"] for m in messages if m["role"] == "system"), "")
        user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        question_match = _QUESTION_LINE.search(user)
        sources = _SOURCE_BLOCK.findall(user)

        task_match = re.match(r"AUFGABE:\s*(\w+)", system)
        if task_match and sources:
            return LLMResponse(text=_studio_json(task_match.group(1), sources))

        if sources and not question_match:
            # Summary-Modus (Audio-Overview): erster Satz jeder Quelle, max. 3.
            openers = [
                re.split(r"(?<=[.!?])\s+", text)[0].strip() for _, text in sources[:3]
            ]
            return LLMResponse(text=" ".join(openers))
        if not question_match or not sources:
            return LLMResponse(text=NO_ANSWER)

        question_words = _content_words(question_match.group(1))
        best_n, best_text, best_score = 0, "", 0
        for number, text in sources:
            score = len(question_words & _content_words(text))
            if score > best_score:
                best_n, best_text, best_score = int(number), text, score

        if best_score == 0:
            return LLMResponse(text=NO_ANSWER)

        sentences = re.split(r"(?<=[.!?])\s+", best_text)
        sentence = max(sentences, key=lambda s: len(question_words & _content_words(s)))
        return LLMResponse(text=f"{sentence.strip()} [{best_n}]")
