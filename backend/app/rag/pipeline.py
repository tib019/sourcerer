"""RAGPipeline — orchestriert Query → Retrieve → Prompt → Answer → Citations (D3)."""

from __future__ import annotations

from app.domain import ChatAnswer
from app.providers.llm import NO_ANSWER, LLMProvider
from app.rag.citations import CitationMapper
from app.rag.prompt_builder import PromptBuilder
from app.rag.retriever import Retriever


class RAGPipeline:
    def __init__(
        self,
        retriever: Retriever,
        prompt_builder: PromptBuilder,
        llm: LLMProvider,
        citation_mapper: CitationMapper,
    ) -> None:
        self._retriever = retriever
        self._prompt_builder = prompt_builder
        self._llm = llm
        self._citation_mapper = citation_mapper

    def answer(self, question: str, notebook_id: str) -> ChatAnswer:
        chunks = self._retriever.retrieve(question, notebook_id)
        if not chunks:
            # Kein relevanter Treffer → gar nicht erst ans LLM (ehrlich + spart Kosten).
            return ChatAnswer(text=NO_ANSWER, citations=[])
        messages = self._prompt_builder.build(question, chunks)
        response = self._llm.complete(messages)
        return self._citation_mapper.map(response.text, chunks)
