"use client";

import { parseAnswer } from "@/lib/citations";
import type { Citation } from "@/lib/types";
import { CitationBadge } from "./CitationBadge";

export function AnswerText({
  text,
  citations,
  onCitationClick,
  activeCitation,
}: {
  text: string;
  citations: Citation[];
  onCitationClick: (citation: Citation) => void;
  activeCitation: Citation | null;
}) {
  const segments = parseAnswer(
    text,
    citations.map((c) => c.n),
  );
  const byNumber = new Map(citations.map((c) => [c.n, c]));

  return (
    <span>
      {segments.map((segment, i) =>
        segment.kind === "text" ? (
          <span key={i}>{segment.text}</span>
        ) : (
          <CitationBadge
            key={i}
            n={segment.n}
            active={activeCitation?.n === segment.n}
            onClick={() => {
              const citation = byNumber.get(segment.n);
              if (citation) onCitationClick(citation);
            }}
          />
        ),
      )}
    </span>
  );
}
