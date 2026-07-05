/** Validierung für die Text-Quelle (Paste) — klare Meldungen statt Backend-Roundtrip. */

export const MAX_PASTE_CHARS = 100_000;
export const MAX_NAME_CHARS = 200;

/** Liefert eine Fehlermeldung oder null, wenn die Eingabe gültig ist. */
export function validatePastedText(name: string, text: string): string | null {
  if (!name.trim()) return "Bitte gib der Quelle einen Namen.";
  if (name.trim().length > MAX_NAME_CHARS)
    return `Name zu lang (max. ${MAX_NAME_CHARS} Zeichen).`;
  if (!text.trim()) return "Der Text ist leer.";
  if (text.length > MAX_PASTE_CHARS)
    return `Text zu lang: ${text.length.toLocaleString("de-DE")} Zeichen (max. ${MAX_PASTE_CHARS.toLocaleString("de-DE")}).`;
  return null;
}
