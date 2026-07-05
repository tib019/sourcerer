/**
 * Mermaid-Rendering mit hartem Fallback (ADR-010): ein Parse-/Render-Fehler
 * darf NIE die Seite crashen — dann zeigt die UI den Rohtext als Liste.
 * mermaid wird lazy importiert (eigener Chunk, lädt erst im Mindmap-Tab).
 */

export type MermaidRenderResult = { ok: true; svg: string } | { ok: false };

export async function renderMermaid(id: string, text: string): Promise<MermaidRenderResult> {
  try {
    const mermaid = (await import("mermaid")).default;
    mermaid.initialize({ startOnLoad: false, securityLevel: "strict", theme: "neutral" });
    const { svg } = await mermaid.render(id, text);
    return { ok: true, svg };
  } catch {
    return { ok: false };
  }
}

/** Rohtext-Fallback: Mermaid-Zeilen als eingerückte Listenpunkte. */
export function mermaidToList(text: string): string[] {
  return text
    .split("\n")
    .slice(1) // "mindmap"-Kopfzeile
    .map((line) => line.replace(/root\(\((.*)\)\)/, "$1").trim())
    .filter(Boolean);
}
