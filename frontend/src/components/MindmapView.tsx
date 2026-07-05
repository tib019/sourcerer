"use client";

import { useEffect, useId, useState } from "react";
import { mermaidToList, renderMermaid } from "@/lib/mermaid";

/** Rendert Mermaid-Text als SVG — bei jedem Fehler Rohtext-Fallback statt Crash. */
export function MindmapView({ mermaid }: { mermaid: string }) {
  const id = useId().replace(/[^a-zA-Z0-9]/g, "");
  const [state, setState] = useState<
    { kind: "loading" } | { kind: "svg"; svg: string } | { kind: "fallback" }
  >({ kind: "loading" });

  useEffect(() => {
    let cancelled = false;
    setState({ kind: "loading" });
    renderMermaid(`mindmap-${id}`, mermaid).then((result) => {
      if (cancelled) return;
      setState(result.ok ? { kind: "svg", svg: result.svg } : { kind: "fallback" });
    });
    return () => {
      cancelled = true;
    };
  }, [mermaid, id]);

  if (state.kind === "loading") {
    return <p className="p-4 text-sm text-slate-400">Rendere Mindmap…</p>;
  }
  if (state.kind === "fallback") {
    return (
      <div data-testid="mindmap-fallback">
        <p className="mb-2 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-800">
          Mindmap konnte nicht gerendert werden — hier die Gliederung als Liste:
        </p>
        <ul className="space-y-1 text-sm text-slate-700">
          {mermaidToList(mermaid).map((line, i) => (
            <li key={i}>• {line}</li>
          ))}
        </ul>
      </div>
    );
  }
  return (
    <div
      data-testid="mindmap-svg"
      className="overflow-x-auto [&_svg]:mx-auto [&_svg]:max-w-full"
      dangerouslySetInnerHTML={{ __html: state.svg }}
    />
  );
}
