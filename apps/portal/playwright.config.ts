import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  use: {
    baseURL: 'http://127.0.0.1:4173',
    trace: 'on-first-retry',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    // Panasonic Toughbook G2 (10.1" 1920x1200, landscape + portrait)
    { name: 'toughbook-landscape', use: { viewport: { width: 1920, height: 1200 } } },
    { name: 'toughbook-portrait', use: { viewport: { width: 1200, height: 1920 } } },
  ],
  webServer: {
    command: 'pnpm exec vite dev --port 4173 --strictPort',
    port: 4173,
    reuseExistingServer: !process.env.CI,
  },
});
