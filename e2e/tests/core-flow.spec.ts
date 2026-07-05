import { expect, test } from "@playwright/test";

/**
 * Kern-Flow (CONTEXT.md §4): Upload → Frage stellen → Antwort mit Zitat
 * erscheint → Zitat-Klick zeigt die Original-Textstelle.
 */
test("Upload → Frage → zitierte Antwort → Zitat-Klick zeigt Quelle", async ({
  page,
}) => {
  await page.goto("/");

  // Warten, bis das Notebook geladen ist (Upload erst dann freigeschaltet)
  await expect(page.getByRole("button", { name: "Datei hochladen" })).toBeEnabled();

  // Quelle hochladen (Datei-Input, .txt)
  const factText =
    "Der Mount Everest ist 8849 Meter hoch. " +
    "Er liegt im Himalaya an der Grenze zwischen Nepal und China.";
  await page.getByTestId("file-input").setInputFiles({
    name: "berge.txt",
    mimeType: "text/plain",
    buffer: Buffer.from(factText, "utf-8"),
  });

  // Dokument erscheint im Quellen-Panel
  await expect(page.getByTestId("document-list")).toContainText("berge.txt");

  // Frage stellen
  await page.getByTestId("question-input").fill("Wie hoch ist der Mount Everest?");
  await page.getByRole("button", { name: "Fragen" }).click();

  // Antwort mit Inhalt + Zitat-Badge [1]
  const chat = page.getByTestId("chat-messages");
  await expect(chat).toContainText("8849");
  const badge = chat.getByRole("button", { name: "Zitat 1 anzeigen" });
  await expect(badge).toBeVisible();

  // Zitat-Klick → Original-Textstelle im Quellen-Panel
  await badge.click();
  const detail = page.getByTestId("citation-detail");
  await expect(detail).toBeVisible();
  await expect(detail).toContainText("berge.txt");
  await expect(detail).toContainText("Seite 1");
  await expect(detail).toContainText("Der Mount Everest ist 8849 Meter hoch.");

  // Audio-Overview (Phase 3, im Studio-Panel): Tab → Generieren → Player
  await page.getByTestId("studio-tab-audio").click();
  await page.getByTestId("studio-generate-audio").click();
  const player = page.getByTestId("audio-overview-player");
  await expect(player).toBeVisible();
  await expect(player).toContainText("Mount Everest");
  await expect(player.locator("audio")).toHaveAttribute("src", /^blob:/);
});

test("Frage ohne Quellengrundlage → ehrliches 'steht nicht in den Quellen'", async ({
  page,
}) => {
  await page.goto("/");

  await expect(page.getByRole("button", { name: "Datei hochladen" })).toBeEnabled();

  await page.getByTestId("file-input").setInputFiles({
    name: "kochen.txt",
    mimeType: "text/plain",
    buffer: Buffer.from("Risotto braucht Geduld und guten Reis.", "utf-8"),
  });
  await expect(page.getByTestId("document-list")).toContainText("kochen.txt");

  await page.getByTestId("question-input").fill("Wer gewann die Schachweltmeisterschaft?");
  await page.getByRole("button", { name: "Fragen" }).click();

  await expect(page.getByTestId("chat-messages")).toContainText(
    "Dazu steht nichts in den Quellen.",
  );
});
