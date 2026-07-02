import { defineConfig } from "@playwright/test";

/**
 * E2E gegen den echten Stack: FastAPI (Fake-Provider, offline) + Next.js.
 * Beide Server werden von Playwright selbst gestartet — ein Befehl, auch in CI.
 */
export default defineConfig({
  testDir: "./tests",
  timeout: 60_000,
  retries: process.env.CI ? 1 : 0,
  use: {
    baseURL: "http://localhost:3000",
    trace: "retain-on-failure",
  },
  webServer: [
    {
      command:
        process.platform === "win32"
          ? "..\\backend\\.venv\\Scripts\\python -m uvicorn app.main:app --port 8000"
          : "../backend/.venv/bin/python -m uvicorn app.main:app --port 8000",
      cwd: "../backend",
      url: "http://localhost:8000/health",
      reuseExistingServer: !process.env.CI,
      env: { SOURCERER_PROVIDERS: "fake" },
    },
    {
      command: "npm run dev",
      cwd: "../frontend",
      url: "http://localhost:3000",
      reuseExistingServer: !process.env.CI,
      env: { NEXT_PUBLIC_API_URL: "http://localhost:8000" },
    },
  ],
});
