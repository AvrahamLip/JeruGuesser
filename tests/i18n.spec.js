'use strict';
const { test, expect } = require('@playwright/test');

/** Helper: clear SW + cache, then load fresh */
async function freshPage(page) {
  await page.goto('/', { waitUntil: 'domcontentloaded' });
  // Unregister any service workers and clear caches
  await page.evaluate(async () => {
    if ('serviceWorker' in navigator) {
      const regs = await navigator.serviceWorker.getRegistrations();
      for (const r of regs) await r.unregister();
    }
    if ('caches' in window) {
      const names = await caches.keys();
      for (const n of names) await caches.delete(n);
    }
  });
  // Reload fresh with no SW interference
  await page.reload({ waitUntil: 'networkidle' });
}

test.describe('i18n – English mode', () => {
  test('switching to English updates all visible UI text', async ({ page }) => {
    await freshPage(page);

    // Wait for home screen
    await expect(page.locator('#home.screen.active')).toBeVisible();

    // Verify default is Hebrew
    const subtitleHe = page.locator('[data-i18n="subtitle"]');
    await expect(subtitleHe).toHaveText('מסע בין רחובות ושכונות ירושלים');

    // Verify button shows "EN" (click to switch to English)
    const langBtn = page.locator('#langToggleBtn');
    await expect(langBtn).toBeVisible();
    await expect(langBtn).toHaveText('EN');

    // Click language toggle to switch to English
    await langBtn.click();

    // Button text should flip to HE (to switch back)
    await expect(langBtn).toHaveText('HE', { timeout: 5000 });

    // Verify English translations on home screen
    await expect(subtitleHe).toHaveText("A journey through Jerusalem's streets and neighborhoods");

    const btnStart = page.locator('[data-i18n="btn-start"]');
    await expect(btnStart).toHaveText('Start JeruGuesser');

    const btnPractice = page.locator('[data-i18n="btn-practice"]');
    await expect(btnPractice).toHaveText('Free Practice');

    const btnLeaderboard = page.locator('[data-i18n="btn-leaderboard"]');
    await expect(btnLeaderboard).toHaveText('Leaderboard');

    // Footer contact link
    const contactLink = page.locator('#contactBtn');
    await expect(contactLink).toContainText('Contact');

    // Verify dir attribute changed to ltr
    const dir = await page.locator('html').getAttribute('dir');
    expect(dir).toBe('ltr');

    const lang = await page.locator('html').getAttribute('lang');
    expect(lang).toBe('en');
  });

  test('contact form labels are in English after switch', async ({ page }) => {
    await freshPage(page);
    await expect(page.locator('#home.screen.active')).toBeVisible();

    // Switch to English
    await page.locator('#langToggleBtn').click();
    await expect(page.locator('#langToggleBtn')).toHaveText('HE', { timeout: 5000 });

    // Open contact form
    await page.locator('#contactBtn').click();
    await expect(page.locator('#contactOverlay')).toHaveClass(/show/);

    // Verify labels are in English
    await expect(page.locator('[data-i18n="contact-title"]')).toHaveText('Contact Us');
    await expect(page.locator('[data-i18n="contact-name"]')).toHaveText('Full Name:');
    await expect(page.locator('[data-i18n="contact-email"]')).toHaveText('Email:');
    await expect(page.locator('[data-i18n="contact-message"]')).toHaveText('Message:');
    await expect(page.locator('[data-i18n="contact-submit"]')).toHaveText('Send Message');

    // Close it
    await page.locator('#contactCloseBtn').click();
    await page.waitForTimeout(400);
  });

  test('toggling back to Hebrew restores all text', async ({ page }) => {
    await freshPage(page);
    await expect(page.locator('#home.screen.active')).toBeVisible();

    const langBtn = page.locator('#langToggleBtn');

    // Switch to English
    await langBtn.click();
    await expect(langBtn).toHaveText('HE', { timeout: 5000 });
    await expect(page.locator('[data-i18n="subtitle"]')).toHaveText("A journey through Jerusalem's streets and neighborhoods");

    // Switch back to Hebrew
    await langBtn.click();
    await expect(langBtn).toHaveText('EN', { timeout: 5000 });
    await expect(page.locator('[data-i18n="subtitle"]')).toHaveText('מסע בין רחובות ושכונות ירושלים');

    const dir = await page.locator('html').getAttribute('dir');
    expect(dir).toBe('rtl');
  });

  test('contact form error message shows in English', async ({ page }) => {
    await freshPage(page);
    await expect(page.locator('#home.screen.active')).toBeVisible();

    // Switch to English
    await page.locator('#langToggleBtn').click();
    await expect(page.locator('#langToggleBtn')).toHaveText('HE', { timeout: 5000 });

    // Open contact form
    await page.locator('#contactBtn').click();
    await expect(page.locator('#contactOverlay')).toHaveClass(/show/);

    // Fill the form
    await page.fill('#contactName', 'Test User');
    await page.fill('#contactEmail', 'test@example.com');
    await page.fill('#contactMessage', 'Test message');

    // Mock fetch to return failure
    await page.evaluate(() => {
      window.fetch = () => Promise.resolve({ ok: false, status: 500 });
    });

    // Submit the form
    await page.locator('#contactForm button[type="submit"]').click();

    // Verify error message is in English
    await expect(page.locator('#contactStatus')).toHaveText('Failed to send message. Please try again.', { timeout: 10000 });
    const color = await page.locator('#contactStatus').evaluate(el => el.style.color);
    expect(color).toBe('rgb(239, 68, 68)'); // #ef4444
  });

  test('contact form success message shows in Hebrew', async ({ page }) => {
    await freshPage(page);
    await expect(page.locator('#home.screen.active')).toBeVisible();

    // Default is Hebrew - don't switch
    await page.locator('#contactBtn').click();
    await expect(page.locator('#contactOverlay')).toHaveClass(/show/);

    // Fill the form
    await page.fill('#contactName', 'Test User');
    await page.fill('#contactEmail', 'test@example.com');
    await page.fill('#contactMessage', 'Test message');

    // Mock fetch to return success
    await page.evaluate(() => {
      window.fetch = () => Promise.resolve({ ok: true, status: 200 });
    });

    // Submit the form
    await page.locator('#contactForm button[type="submit"]').click();

    // Verify success message is in Hebrew
    await expect(page.locator('#contactStatus')).toHaveText('ההודעה נשלחה בהצלחה!', { timeout: 10000 });
    const color = await page.locator('#contactStatus').evaluate(el => el.style.color);
    expect(color).toBe('rgb(16, 185, 129)'); // #10b981
  });
});
