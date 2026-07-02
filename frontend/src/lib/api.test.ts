import { afterEach, describe, expect, it, vi } from "vitest";
import { askQuestion, createNotebook, uploadFile } from "./api";

function mockFetch(status: number, body: unknown) {
  const fn = vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(body),
  });
  vi.stubGlobal("fetch", fn);
  return fn;
}

afterEach(() => vi.unstubAllGlobals());

describe("api client", () => {
  it("createNotebook sendet POST mit JSON-Body", async () => {
    const fetchMock = mockFetch(201, { id: "n1", name: "Test" });
    const notebook = await createNotebook("Test");

    expect(notebook.id).toBe("n1");
    const [url, init] = fetchMock.mock.calls[0];
    expect(String(url)).toMatch(/\/notebooks$/);
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body)).toEqual({ name: "Test" });
  });

  it("askQuestion liefert Antwort mit Zitaten", async () => {
    mockFetch(200, {
      answer: "Antwort [1]",
      citations: [
        {
          n: 1,
          document_id: "d1",
          document_name: "doc.txt",
          chunk_index: 0,
          page: 1,
          text: "Beleg",
        },
      ],
    });
    const response = await askQuestion("n1", "Frage?");
    expect(response.citations).toHaveLength(1);
    expect(response.citations[0].document_name).toBe("doc.txt");
  });

  it("uploadFile schickt multipart/form-data ohne Content-Type-Header", async () => {
    const fetchMock = mockFetch(201, {
      id: "d1",
      name: "a.txt",
      media_type: "text/plain",
      page_count: 1,
      chunk_count: 1,
    });
    await uploadFile("n1", new File(["hallo"], "a.txt", { type: "text/plain" }));

    const [, init] = fetchMock.mock.calls[0];
    expect(init.body).toBeInstanceOf(FormData);
    expect(init.headers).toBeUndefined(); // Browser setzt multipart-Boundary selbst
  });

  it("wirft den detail-Text des Backends bei Fehlern", async () => {
    mockFetch(422, { detail: "PDF enthält keinen extrahierbaren Text" });
    await expect(askQuestion("n1", "Frage?")).rejects.toThrow(
      "PDF enthält keinen extrahierbaren Text",
    );
  });

  it("fällt bei Fehlern ohne Body auf HTTP-Status zurück", async () => {
    const fn = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      json: () => Promise.reject(new Error("kein JSON")),
    });
    vi.stubGlobal("fetch", fn);
    await expect(askQuestion("n1", "Frage?")).rejects.toThrow("HTTP 500");
  });
});
