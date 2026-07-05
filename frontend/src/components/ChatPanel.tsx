"use client";

import { useEffect, useRef, useState } from "react";
import type { ChatMessage, Citation } from "@/lib/types";
import { AnswerText } from "./AnswerText";

export function ChatPanel({
  messages,
  onAsk,
  onCitationClick,
  activeCitation,
  busy,
  hasSources,
  suggestedQuestions,
}: {
  messages: ChatMessage[];
  onAsk: (question: string) => void;
  onCitationClick: (citation: Citation) => void;
  activeCitation: Citation | null;
  busy: boolean;
  hasSources: boolean;
  suggestedQuestions: string[];
}) {
  const [question, setQuestion] = useState("");
  const bottom = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy]);

  return (
    <section className="flex h-full flex-1 flex-col">
      <div className="flex-1 space-y-4 overflow-y-auto p-6" data-testid="chat-messages">
        {messages.length === 0 && (
          <div className="mt-16 text-center text-slate-400">
            <p className="text-4xl">🧙‍♂️</p>
            <p className="mt-2 font-medium">
              Der Sourcerer zaubert nicht — er belegt.
            </p>
            <p className="text-sm">
              {hasSources
                ? "Stell eine Frage zu deinen Quellen."
                : "Lade zuerst eine Quelle hoch, dann stell deine Frage."}
            </p>
          </div>
        )}
        {messages.map((message, i) => (
          <div
            key={i}
            className={message.role === "user" ? "flex justify-end" : "flex"}
          >
            <div
              className={`max-w-2xl rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                message.role === "user"
                  ? "bg-indigo-600 text-white"
                  : "border border-slate-200 bg-white text-slate-800 shadow-sm"
              }`}
            >
              {message.role === "assistant" ? (
                <AnswerText
                  text={message.text}
                  citations={message.citations}
                  onCitationClick={onCitationClick}
                  activeCitation={activeCitation}
                />
              ) : (
                message.text
              )}
            </div>
          </div>
        ))}
        {busy && (
          <div className="flex">
            <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-400 shadow-sm">
              Sucht in den Quellen…
            </div>
          </div>
        )}
        <div ref={bottom} />
      </div>

      {hasSources && messages.length === 0 && suggestedQuestions.length > 0 && (
        <div
          className="flex flex-wrap gap-2 border-t border-slate-100 bg-white px-4 pt-3"
          data-testid="suggested-questions"
        >
          {suggestedQuestions.map((question, i) => (
            <button
              key={i}
              onClick={() => onAsk(question)}
              disabled={busy}
              className="rounded-full border border-indigo-200 bg-indigo-50 px-3 py-1.5
                text-xs text-indigo-800 hover:bg-indigo-100 disabled:opacity-50"
            >
              {question}
            </button>
          ))}
        </div>
      )}

      <form
        className="border-t border-slate-200 bg-white p-4"
        onSubmit={(e) => {
          e.preventDefault();
          const q = question.trim();
          if (!q || busy) return;
          onAsk(q);
          setQuestion("");
        }}
      >
        <div className="flex gap-2">
          <input
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder={
              hasSources ? "Frage zu deinen Quellen…" : "Erst eine Quelle hochladen…"
            }
            disabled={!hasSources || busy}
            data-testid="question-input"
            className="flex-1 rounded-xl border border-slate-300 px-4 py-3 text-sm
              focus:border-indigo-500 focus:outline-none disabled:bg-slate-50"
          />
          <button
            type="submit"
            disabled={!hasSources || busy || !question.trim()}
            className="rounded-xl bg-indigo-600 px-5 py-3 text-sm font-medium text-white
              hover:bg-indigo-700 disabled:opacity-50"
          >
            Fragen
          </button>
        </div>
      </form>
    </section>
  );
}
