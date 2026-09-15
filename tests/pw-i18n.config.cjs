'use strict';
const path = require('path');
const { defineConfig, devices } = require('@playwright/test');

const rootDir = path.join(__dirname, '..');

module.exports = defineConfig({
  testDir: __dirname,
  testMatch: 'i18n.spec.js',
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
    { name: 'Mobile Chrome', use: { ...devices['Pixel 7'] } },
  ],
  webServer: {
    command: `npx --yes serve ${rootDir} -l 4173`,
    url: 'http://127.0.0.1:4173/',
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
});
