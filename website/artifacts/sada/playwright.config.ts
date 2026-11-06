import { defineConfig, devices } from '@playwright/test';
import { existsSync } from 'node:fs';

// Replit supplies a Nix-wrapped Chromium with its shared libraries configured.
// Elsewhere use Playwright's installed browser, or an explicit local override.
const executablePath = process.env.SADA_E2E_CHROMIUM_PATH
  || (existsSync('/repl/tools/bin/chromium') ? '/repl/tools/bin/chromium' : undefined);

// The managed SADA workflow serves through the shared preview proxy.
// No second web server or backend connection is needed for this suite.
export default defineConfig({
  testDir: './tests/e2e',
  outputDir: '../../generated-artifacts/sada-e2e',
  reporter: 'list',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: 0,
  use: {
    baseURL: process.env.SADA_E2E_BASE_URL || 'http://localhost:80/',
    acceptDownloads: true,
    launchOptions: { executablePath },
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
});
