'use strict';
const { defineConfig, devices } = require('@playwright/test');

module.exports = defineConfig({
  testDir: 'tests',
  testMatch: '**/mobile-compat.spec.js',
  timeout: 120000,
  expect: { timeout: 45000 },
  fullyParallel: false,
  workers: 1,
  reporter: 'list',
  use: {
    baseURL: 'http://127.0.0.1:4173',
    locale: 'he-IL',
  },
  projects: [
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 7'] },
    },
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 12'] },
    },
  ],
  webServer: {
    command: 'npx --yes serve . -l 4173',
    url: 'http://127.0.0.1:4173/game.html',
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
});
