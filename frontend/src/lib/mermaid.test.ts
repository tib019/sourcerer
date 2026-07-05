import { afterEach, describe, expect, it, vi } from "vitest";

afterEach(() => {
  vi.resetModules();
  vi.doUnmock("mermaid");
});

describe("renderMermaid", () => {
  it("liefert SVG bei gültigem Diagramm", async () => {
    vi.doMock("mermaid", () => ({
      default: {
        initialize: vi.fn(),
        render: vi.fn().mockResolvedValue({ svg: "<svg>ok</svg>" }),
      },
    }));
    const { renderMermaid } = await import("./mermaid");
    expect(await renderMermaid("m1", "mindmap\n  root((A))")).toEqual({
      ok: true,
      svg: "<svg>ok</svg>",
    });
  });

  it("fällt bei Parse-Fehler auf ok:false zurück statt zu werfen", async () => {
    vi.doMock("mermaid", () => ({
      default: {
        initialize: vi.fn(),
        render: vi.fn().mockRejectedValue(new Error("Parse error")),
      },
    }));
    const { renderMermaid } = await import("./mermaid");
    await expect(renderMermaid("m2", "((kaputt")).resolves.toEqual({ ok: false });
  });
});

describe("mermaidToList", () => {
  it("macht aus Mermaid-Zeilen lesbare Listenpunkte", async () => {
    const { mermaidToList } = await import("./mermaid");
    expect(mermaidToList("mindmap\n  root((Thema))\n    Zweig\n      Blatt")).toEqual([
      "Thema",
      "Zweig",
      "Blatt",
    ]);
  });
});
