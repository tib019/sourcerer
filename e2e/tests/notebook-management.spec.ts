import { expect, test, type Page } from "@playwright/test";

async function uploadSource(page: Page, name: string, text: string) {
  await page.getByTestId("file-input").setInputFiles({
    name,
    mimeType: "text/plain",
    buffer: Buffer.from(text, "utf-8"),
  });
  await expect(page.getByTestId("document-list")).toContainText(name);
}

async function ready(page: Page) {
  await page.goto("/");
  await expect(page.getByRole("button", { name: "Datei hochladen" })).toBeEnabled();
}

test("Quelle löschen: nur die eine weg (auch nach Reload), andere bleibt zitierbar", async ({
  page,
}) => {
  await ready(page);

  // Eigenes Notebook — das Default-Notebook teilen sich parallele Specs.
  page.once("dialog", (dialog) => dialog.accept("Löschen-Test"));
  await page.getByTestId("notebook-create").click();
  await expect(page.getByTestId("notebook-select")).toContainText("Löschen-Test");

  await uploadSource(page, "planeten.txt", "Der Mars hat zwei Monde: Phobos und Deimos.");
  await uploadSource(page, "fluesse.txt", "Die Donau fliesst durch zehn Laender.");

  // Loeschen mit Bestaetigung
  page.once("dialog", (dialog) => dialog.accept());
  await page.getByRole("button", { name: "Quelle planeten.txt löschen" }).click();
  await expect(page.getByTestId("document-list")).not.toContainText("planeten.txt");
  await expect(page.getByTestId("document-list")).toContainText("fluesse.txt");

  // Reload: Loeschung ist persistent (nach Reload unser Notebook wieder waehlen —
  // die App aktiviert sonst das erste der Liste)
  await ready(page);
  await page.getByTestId("notebook-select").selectOption({ label: "Löschen-Test" });
  await expect(page.getByTestId("document-list")).not.toContainText("planeten.txt");
  await expect(page.getByTestId("document-list")).toContainText("fluesse.txt");

  // Andere Quelle bleibt zitierbar …
  await page.getByTestId("question-input").fill("Durch wie viele Laender fliesst die Donau?");
  await page.getByRole("button", { name: "Fragen" }).click();
  const chat = page.getByTestId("chat-messages");
  await expect(chat).toContainText("zehn");
  await expect(chat.getByRole("button", { name: "Zitat 1 anzeigen" })).toBeVisible();

  // … die geloeschte nicht mehr (Frage nach Mars-Monden -> ehrliches NO_ANSWER)
  await page.getByTestId("question-input").fill("Welche Monde hat der Mars?");
  await page.getByRole("button", { name: "Fragen" }).click();
  await expect(chat).toContainText("Dazu steht nichts in den Quellen.");
});

test("Neues Notebook ist isoliert: Quellen aus A tauchen in B nicht auf", async ({
  page,
}) => {
  await ready(page);
  await uploadSource(page, "inseln.txt", "Island liegt am Polarkreis und hat Geysire.");

  // Neues Notebook anlegen (Prompt-Dialog)
  page.once("dialog", (dialog) => dialog.accept("Notebook B"));
  await page.getByTestId("notebook-create").click();
  await expect(page.getByTestId("notebook-select")).toHaveValue(/.+/);
  await expect(page.getByTestId("notebook-select")).toContainText("Notebook B");

  // B ist leer — keine Quellen aus A
  await expect(page.getByTestId("document-list")).not.toContainText("inseln.txt");
  await expect(page.getByTestId("document-list")).toContainText("Noch keine Quellen");
  await expect(page.getByTestId("question-input")).toBeDisabled();

  // Eigene Quelle in B, Frage nach A-Inhalt -> nichts in den Quellen
  await uploadSource(page, "wuesten.txt", "Die Sahara ist die groesste heisse Wueste.");
  await page.getByTestId("question-input").fill("Wo liegt Island?");
  await page.getByRole("button", { name: "Fragen" }).click();
  await expect(page.getByTestId("chat-messages")).toContainText(
    "Dazu steht nichts in den Quellen.",
  );
});

test("Notebook-Reset leert Quellen, Notebook bleibt", async ({ page }) => {
  await ready(page);

  // Eigenes Notebook fuer diesen Test (Isolation von anderen Specs)
  page.once("dialog", (dialog) => dialog.accept("Reset-Test"));
  await page.getByTestId("notebook-create").click();
  await expect(page.getByTestId("notebook-select")).toContainText("Reset-Test");

  await uploadSource(page, "temp.txt", "Kurzer Inhalt zum Zuruecksetzen.");
  page.once("dialog", (dialog) => dialog.accept());
  await page.getByTestId("notebook-reset").click();

  await expect(page.getByTestId("document-list")).toContainText("Noch keine Quellen");
  await expect(page.getByTestId("notebook-select")).toContainText("Reset-Test");
});
