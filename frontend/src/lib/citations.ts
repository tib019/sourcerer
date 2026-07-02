/**
 * Zerlegt einen Antworttext mit [n]-Markern in Segmente fürs Rendering:
 * Text-Segmente und klickbare Zitat-Segmente (ADR-005).
 *
 * Nur Marker, die in `validNumbers` vorkommen, werden zu Zitat-Segmenten —
 * alles andere bleibt Text (das Backend hat ungültige bereits entfernt,
 * das Frontend verlässt sich trotzdem nicht darauf).
 */

export type AnswerSegment =
  | { kind: "text"; text: string }
  | { kind: "citation"; n: number };

const MARKER = /\[(\d+)\]/g;

export function parseAnswer(text: string, validNumbers: number[]): AnswerSegment[] {
  const valid = new Set(validNumbers);
  const segments: AnswerSegment[] = [];
  let last = 0;

  for (const match of text.matchAll(MARKER)) {
    const n = Number(match[1]);
    if (!valid.has(n)) continue;
    if (match.index > last) {
      segments.push({ kind: "text", text: text.slice(last, match.index) });
    }
    segments.push({ kind: "citation", n });
    last = match.index + match[0].length;
  }
  if (last < text.length) {
    segments.push({ kind: "text", text: text.slice(last) });
  }
  return segments;
}
