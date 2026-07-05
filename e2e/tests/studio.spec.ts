import { expect, test, type Page } from "@playwright/test";

async function freshNotebookWithSource(page: Page, notebookName: string) {
  await page.goto("/");
  await expect(page.getByRole("button", { name: "Datei hochladen" })).toBeEnabled();

  // Eigenes Notebook je Test — Isolation vom restlichen Fake-Backend-Zustand
  page.once("dialog", (dialog) => dialog.accept(notebookName));
  await page.getByTestId("notebook-create").click();
  await expect(page.getByTestId("notebook-select")).toContainText(notebookName);

  await page.getByTestId("file-input").setInputFiles({
    name: "vulkane.txt",
    mimeType: "text/plain",
    buffer: Buffer.from(
      "Der Vesuv liegt am Golf von Neapel. Sein Ausbruch verschuettete Pompeji im Jahr 79.",
      "utf-8",
    ),
  });
  await expect(page.getByTestId("document-list")).toContainText("vulkane.txt");
}

test("Studio: Bericht generieren → zitierter Bericht, Chip zeigt Quelle", async ({
  page,
}) => {
  await freshNotebookWithSource(page, "Studio-Test");

  await page.getByTestId("studio-tab-report").click();
  await page.getByTestId("studio-generate-report").click();

  const report = page.getByTestId("studio-report");
  await expect(report).toBeVisible();
  await expect(report).toContainText("Vesuv");

  // Zitat-Chip klickbar wie im Chat → Original-Textstelle im Quellen-Panel
  await report.getByRole("button", { name: "Zitat 1 anzeigen" }).first().click();
  const detail = page.getByTestId("citation-detail");
  await expect(detail).toBeVisible();
  await expect(detail).toContainText("vulkane.txt");
  await expect(detail).toContainText("Der Vesuv liegt am Golf von Neapel.");
});

test("Studio: Karteikarten drehen sich, Quiz zeigt richtig/falsch", async ({ page }) => {
  await freshNotebookWithSource(page, "Karten-Quiz");

  // Karteikarten
  await page.getByTestId("studio-tab-cards").click();
  await page.getByTestId("studio-generate-cards").click();
  const cards = page.getByTestId("studio-cards");
  await expect(cards).toBeVisible();
  const firstCard = cards.locator("li").first().locator("button").first();
  await expect(firstCard).toContainText("Karte 1");
  await firstCard.click(); // umdrehen
  await expect(firstCard).toContainText("Antwort");

  // Quiz
  await page.getByTestId("studio-tab-quiz").click();
  await page.getByTestId("studio-generate-quiz").click();
  const quiz = page.getByTestId("studio-quiz");
  await expect(quiz).toBeVisible();
  const firstQuestion = quiz.locator("li").first();
  await firstQuestion.locator("button").first().click(); // Option 1 = richtig (Fake)
  await expect(firstQuestion).toContainText("✅ Richtig.");
});

test("Startfragen-Chips erscheinen nach Upload, Klick stellt die Frage", async ({
  page,
}) => {
  await freshNotebookWithSource(page, "Chips-Test");

  const chips = page.getByTestId("suggested-questions");
  await expect(chips).toBeVisible();
  const firstChip = chips.locator("button").first();
  const questionText = await firstChip.textContent();
  await firstChip.click();

  const chat = page.getByTestId("chat-messages");
  await expect(chat).toContainText(questionText!.slice(0, 20));
  // Fake-Startfragen enthalten Quellen-Wörter → belegte Antwort mit Zitat
  await expect(chat.getByRole("button", { name: "Zitat 1 anzeigen" })).toBeVisible();
  // Nach der ersten Frage verschwinden die Chips (nur bei leerem Chat)
  await expect(chips).not.toBeVisible();
});

test("Studio: Empty-State ohne Quellen, Buttons erst mit Quellen", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("button", { name: "Datei hochladen" })).toBeEnabled();
  page.once("dialog", (dialog) => dialog.accept("Leeres Studio"));
  await page.getByTestId("notebook-create").click();
  await expect(page.getByTestId("notebook-select")).toContainText("Leeres Studio");

  await expect(page.getByTestId("studio-panel")).toContainText("Lade zuerst Quellen hoch");
  await expect(page.getByTestId("studio-generate-report")).toHaveCount(0);
});
