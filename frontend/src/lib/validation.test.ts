import { describe, expect, it } from "vitest";
import { MAX_PASTE_CHARS, validatePastedText } from "./validation";

describe("validatePastedText", () => {
  it("akzeptiert gültige Eingaben", () => {
    expect(validatePastedText("Notizen", "Etwas Inhalt.")).toBeNull();
  });

  it("lehnt fehlenden Namen ab", () => {
    expect(validatePastedText("   ", "Inhalt")).toMatch(/Namen/);
  });

  it("lehnt leeren Text ab (auch nur Whitespace)", () => {
    expect(validatePastedText("Notizen", "  \n\t ")).toMatch(/leer/);
  });

  it("lehnt zu langen Text mit klarer Meldung ab", () => {
    const error = validatePastedText("Notizen", "x".repeat(MAX_PASTE_CHARS + 1));
    expect(error).toMatch(/zu lang/);
    expect(error).toMatch(/100\.000/);
  });

  it("akzeptiert Text exakt an der Obergrenze", () => {
    expect(validatePastedText("Notizen", "x".repeat(MAX_PASTE_CHARS))).toBeNull();
  });

  it("lehnt überlangen Namen ab", () => {
    expect(validatePastedText("n".repeat(201), "Inhalt")).toMatch(/Name zu lang/);
  });
});
