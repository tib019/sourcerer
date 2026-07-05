"use client";

import { useEffect, useState } from "react";
import * as api from "@/lib/api";
import type {
  Citation,
  FlashcardsData,
  MindmapData,
  QuizData,
  ReportData,
  StudioSource,
} from "@/lib/types";
import { CitationBadge } from "./CitationBadge";
import { MindmapView } from "./MindmapView";

type Tab = "report" | "cards" | "quiz" | "mindmap" | "audio";

function toAudioUrl(base64: string, mediaType: string): string {
  const bytes = Uint8Array.from(atob(base64), (c) => c.charCodeAt(0));
  return URL.createObjectURL(new Blob([bytes], { type: mediaType }));
}

function SourceChips({
  numbers,
  sources,
  onCitationClick,
  activeCitation,
}: {
  numbers: number[];
  sources: StudioSource[];
  onCitationClick: (citation: Citation) => void;
  activeCitation: Citation | null;
}) {
  const byNumber = new Map(sources.map((s) => [s.n, s]));
  return (
    <span className="ml-1 inline-flex gap-0.5">
      {numbers.map((n) => {
        const source = byNumber.get(n);
        if (!source) return null;
        return (
          <CitationBadge
            key={n}
            n={n}
            active={activeCitation?.n === n && activeCitation?.document_id === source.document_id}
            onClick={() => onCitationClick(source)}
          />
        );
      })}
    </span>
  );
}

function Spinner({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-2 p-4 text-sm text-slate-400" role="status">
      <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-indigo-300 border-t-transparent" />
      {label}
    </div>
  );
}

export function StudioPanel({
  notebookId,
  hasSources,
  onCitationClick,
  activeCitation,
}: {
  notebookId: string | null;
  hasSources: boolean;
  onCitationClick: (citation: Citation) => void;
  activeCitation: Citation | null;
}) {
  const [tab, setTab] = useState<Tab>("report");
  const [report, setReport] = useState<ReportData | null>(null);
  const [cards, setCards] = useState<FlashcardsData | null>(null);
  const [quiz, setQuiz] = useState<QuizData | null>(null);
  const [mindmap, setMindmap] = useState<MindmapData | null>(null);
  const [audio, setAudio] = useState<{ url: string; summary: string } | null>(null);
  const [flipped, setFlipped] = useState<Set<number>>(new Set());
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [loading, setLoading] = useState<Tab | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Notebook-Wechsel: alles Generierte gehört zum alten Notebook -> leeren.
  useEffect(() => {
    setReport(null);
    setCards(null);
    setQuiz(null);
    setMindmap(null);
    setFlipped(new Set());
    setAnswers({});
    setError(null);
    setAudio((old) => {
      if (old) URL.revokeObjectURL(old.url);
      return null;
    });
  }, [notebookId]);

  const generate = async (which: Tab) => {
    if (!notebookId) return;
    setLoading(which);
    setError(null);
    try {
      if (which === "report") setReport(await api.generateReport(notebookId));
      if (which === "cards") {
        setCards(await api.generateFlashcards(notebookId));
        setFlipped(new Set());
      }
      if (which === "quiz") {
        setQuiz(await api.generateQuiz(notebookId));
        setAnswers({});
      }
      if (which === "mindmap") setMindmap(await api.generateMindmap(notebookId));
      if (which === "audio") {
        const data = await api.createAudioOverview(notebookId);
        setAudio((old) => {
          if (old) URL.revokeObjectURL(old.url);
          return { url: toAudioUrl(data.audio_base64, data.media_type), summary: data.summary };
        });
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Generierung fehlgeschlagen");
    } finally {
      setLoading(null);
    }
  };

  const tabs: { id: Tab; label: string }[] = [
    { id: "report", label: "Bericht" },
    { id: "cards", label: "Karten" },
    { id: "quiz", label: "Quiz" },
    { id: "mindmap", label: "Mindmap" },
    { id: "audio", label: "Audio" },
  ];

  const generateLabel: Record<Tab, string> = {
    report: "Bericht generieren",
    cards: "Karteikarten generieren",
    quiz: "Quiz generieren",
    mindmap: "Mindmap generieren",
    audio: "Audio-Overview erzeugen",
  };

  const hasContent: Record<Tab, boolean> = {
    report: !!report,
    cards: !!cards,
    quiz: !!quiz,
    mindmap: !!mindmap,
    audio: !!audio,
  };

  return (
    <aside
      className="flex h-full w-96 shrink-0 flex-col border-l border-slate-200 bg-white"
      data-testid="studio-panel"
    >
      <div className="border-b border-slate-200 p-4 pb-0">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
          Studio
        </h2>
        <nav className="mt-3 flex gap-1">
          {tabs.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              data-testid={`studio-tab-${t.id}`}
              className={`rounded-t-lg px-3 py-2 text-sm ${
                tab === t.id
                  ? "border border-b-0 border-slate-200 bg-white font-medium text-indigo-700"
                  : "text-slate-500 hover:text-slate-800"
              }`}
            >
              {t.label}
            </button>
          ))}
        </nav>
      </div>

      <div className="flex-1 overflow-y-auto p-4" data-testid={`studio-content-${tab}`}>
        {!hasSources ? (
          <p className="p-4 text-sm text-slate-400">
            Lade zuerst Quellen hoch — das Studio arbeitet ausschließlich mit deinen
            Dokumenten.
          </p>
        ) : loading === tab ? (
          <Spinner label={`${generateLabel[tab]}…`} />
        ) : (
          <>
            {error && (
              <p className="mb-3 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>
            )}
            {!hasContent[tab] && (
              <div className="p-4 text-center">
                <p className="mb-3 text-sm text-slate-400">
                  Noch nichts generiert — alles entsteht belegt aus deinen Quellen.
                </p>
                <button
                  onClick={() => generate(tab)}
                  data-testid={`studio-generate-${tab}`}
                  className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
                >
                  {generateLabel[tab]}
                </button>
              </div>
            )}

            {tab === "report" && report && (
              <article data-testid="studio-report">
                <h3 className="text-base font-bold text-slate-900">{report.title}</h3>
                {report.sections.map((section, i) => (
                  <section key={i} className="mt-4">
                    <h4 className="text-sm font-semibold text-slate-800">
                      {section.heading}
                    </h4>
                    <p className="mt-1 text-sm leading-relaxed text-slate-700">
                      {section.content}
                      <SourceChips
                        numbers={section.citations}
                        sources={report.sources}
                        onCitationClick={onCitationClick}
                        activeCitation={activeCitation}
                      />
                    </p>
                  </section>
                ))}
              </article>
            )}

            {tab === "cards" && cards && (
              <ul className="grid grid-cols-1 gap-3" data-testid="studio-cards">
                {cards.cards.map((card, i) => {
                  const isFlipped = flipped.has(i);
                  return (
                    <li key={i}>
                      <button
                        onClick={() =>
                          setFlipped((old) => {
                            const next = new Set(old);
                            if (next.has(i)) next.delete(i);
                            else next.add(i);
                            return next;
                          })
                        }
                        className={`w-full rounded-xl border p-4 text-left text-sm transition-colors ${
                          isFlipped
                            ? "border-indigo-300 bg-indigo-50"
                            : "border-slate-200 bg-white hover:border-indigo-200"
                        }`}
                      >
                        <p className="text-xs uppercase tracking-wide text-slate-400">
                          {isFlipped ? "Antwort" : `Karte ${i + 1} — klicken zum Umdrehen`}
                        </p>
                        <p className="mt-1 text-slate-800">
                          {isFlipped ? card.back : card.front}
                        </p>
                      </button>
                      {isFlipped && card.citation != null && (
                        <div className="mt-1 pl-1 text-xs text-slate-500">
                          Beleg:
                          <SourceChips
                            numbers={[card.citation]}
                            sources={cards.sources}
                            onCitationClick={onCitationClick}
                            activeCitation={activeCitation}
                          />
                        </div>
                      )}
                    </li>
                  );
                })}
              </ul>
            )}

            {tab === "quiz" && quiz && (
              <ol className="space-y-5" data-testid="studio-quiz">
                {quiz.questions.map((question, qi) => {
                  const chosen = answers[qi];
                  return (
                    <li key={qi}>
                      <p className="text-sm font-medium text-slate-800">
                        {qi + 1}. {question.question}
                      </p>
                      <div className="mt-2 space-y-1.5">
                        {question.options.map((option, oi) => {
                          const isChosen = chosen === oi;
                          const isCorrect = oi === question.answer_index;
                          const revealed = chosen !== undefined;
                          return (
                            <button
                              key={oi}
                              disabled={revealed}
                              onClick={() => setAnswers((a) => ({ ...a, [qi]: oi }))}
                              className={`block w-full rounded-lg border px-3 py-2 text-left text-sm ${
                                revealed && isCorrect
                                  ? "border-green-400 bg-green-50 text-green-900"
                                  : revealed && isChosen
                                    ? "border-red-300 bg-red-50 text-red-800"
                                    : "border-slate-200 hover:border-indigo-300"
                              }`}
                            >
                              {option}
                            </button>
                          );
                        })}
                      </div>
                      {chosen !== undefined && (
                        <p className="mt-1.5 text-xs text-slate-500">
                          {chosen === question.answer_index ? "✅ Richtig." : "❌ Falsch."}
                          {question.citation != null && (
                            <>
                              {" "}
                              Beleg:
                              <SourceChips
                                numbers={[question.citation]}
                                sources={quiz.sources}
                                onCitationClick={onCitationClick}
                                activeCitation={activeCitation}
                              />
                            </>
                          )}
                        </p>
                      )}
                    </li>
                  );
                })}
              </ol>
            )}

            {tab === "mindmap" && mindmap && (
              <div data-testid="studio-mindmap">
                <MindmapView mermaid={mindmap.mermaid} />
              </div>
            )}

            {tab === "audio" && audio && (
              <div data-testid="audio-overview-player">
                <audio controls src={audio.url} className="w-full" />
                <p className="mt-2 text-sm leading-relaxed text-slate-700">
                  {audio.summary}
                </p>
              </div>
            )}

            {hasContent[tab] && (
              <div className="mt-4 border-t border-slate-100 pt-3 text-right">
                <button
                  onClick={() => generate(tab)}
                  className="text-xs text-indigo-600 hover:text-indigo-800"
                >
                  Neu generieren
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </aside>
  );
}
