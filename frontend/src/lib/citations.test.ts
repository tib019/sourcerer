import { describe, expect, it } from "vitest";
import { parseAnswer } from "./citations";

describe("parseAnswer", () => {
  it("zerlegt Text mit einem Zitat in Segmente", () => {
    expect(parseAnswer("Die Antwort [1] steht fest.", [1])).toEqual([
      { kind: "text", text: "Die Antwort " },
      { kind: "citation", n: 1 },
      { kind: "text", text: " steht fest." },
    ]);
  });

  it("behandelt mehrere und aufeinanderfolgende Marker", () => {
    expect(parseAnswer("Fakt [1][2].", [1, 2])).toEqual([
      { kind: "text", text: "Fakt " },
      { kind: "citation", n: 1 },
      { kind: "citation", n: 2 },
      { kind: "text", text: "." },
    ]);
  });

  it("lässt Marker ohne zugehöriges Zitat als Text stehen", () => {
    const segments = parseAnswer("Echt [1], erfunden [99].", [1]);
    expect(segments).toContainEqual({ kind: "citation", n: 1 });
    expect(segments.some((s) => s.kind === "citation" && s.n === 99)).toBe(false);
    // [99] bleibt unangetastet im Text (Backend filtert, Frontend vertraut nicht blind)
    expect(segments.map((s) => (s.kind === "text" ? s.text : "")).join("")).toContain(
      "[99]",
    );
  });

  it("Marker am Anfang und Ende", () => {
    expect(parseAnswer("[1] Anfang, Ende [2]", [1, 2])).toEqual([
      { kind: "citation", n: 1 },
      { kind: "text", text: " Anfang, Ende " },
      { kind: "citation", n: 2 },
    ]);
  });

  it("Text ohne Marker bleibt ein Segment", () => {
    expect(parseAnswer("Nur Text.", [])).toEqual([{ kind: "text", text: "Nur Text." }]);
  });

  it("leerer Text ergibt keine Segmente", () => {
    expect(parseAnswer("", [])).toEqual([]);
  });
});
