import { defineConfig, devices } from '@playwright/test';

// Live tests expect the API on PATHSNAP_TEST_API (default http://127.0.0.1:8000), started separately.
export default defineConfig({
  testDir: './tests',
  timeout: 60_000,
  retries: 0,
  reporter: [['list']],
  use: { baseURL: 'http://127.0.0.1:5173', trace: 'retain-on-failure' },
  outputDir: 'test-results',
  webServer: { command: 'npx vite --host 127.0.0.1 --port 5173 --strictPort', url: 'http://127.0.0.1:5173', reuseExistingServer: true },
  projects: [{ name: 'chrome', use: { ...devices['Desktop Chrome'], channel: process.env.PW_CHANNEL ?? 'chrome' } }],
});
