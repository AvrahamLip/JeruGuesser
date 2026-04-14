'use strict';
const { test, expect } = require('@playwright/test');

test.describe('תאימות נייד (מקומי)', () => {
  test('מטא viewport, מסך בית ושטח מפה בתרגול', async ({ page }) => {
    await page.goto('/game.html', { waitUntil: 'domcontentloaded' });

    const viewportMeta = page.locator('meta[name="viewport"]');
    await expect(viewportMeta).toHaveCount(1);
    const vp = await viewportMeta.getAttribute('content');
    expect(vp).toMatch(/width=device-width/i);
    expect(vp).toMatch(/viewport-fit=cover/i);

    await expect(page.locator('#home.screen.active')).toBeVisible();

    const practice = page.getByRole('button', { name: /תרגול חופשי על המפה|תרגול חופשי/i });
    await expect(practice).toBeEnabled({ timeout: 90000 });

    await practice.click();

    await expect(page.locator('#stage0.active')).toBeVisible({ timeout: 90000 });
    await expect(page.locator('#map0')).toBeVisible();

    // Unified rail (layout A): no legacy stacked banner / game-header on map stages
    await expect(page.locator('#stage0 .rail-wrap')).toBeVisible();
    await expect(page.locator('#stage0 .game-header')).toHaveCount(0);
    await expect(page.locator('#stage0 .stage-banner')).toHaveCount(0);
    await expect(page.locator('#stage0 .map-target-chip')).toBeVisible();
    await expect(page.locator('#s0TargetName')).toBeVisible();
    await expect(page.locator('#s0ContextKicker')).not.toHaveText('');
    await expect(page.locator('#s0ContextMain')).not.toHaveText('');
    await expect(page.locator('#s0Back.rail-home')).toBeVisible();
    await expect(page.locator('#stage0 .rail-track-wrap')).toBeAttached();

    // Root cause of duplicate chrome: #globalNav + #globalNavScore sat above the rail; score strip must stay hidden on rail stages.
    await expect(page.locator('body.game-rail-screens')).toHaveCount(1);
    const navScoreDisplay = await page.evaluate(() => {
      const el = document.getElementById('globalNavScore');
      return el ? window.getComputedStyle(el).display : '';
    });
    expect(navScoreDisplay, 'globalNavScore should not duplicate rail score on map stages').toBe('none');

    const mapRatio = await page.evaluate(() => {
      const el = document.querySelector('#stage0 .map-area');
      if (!el) return 0;
      const r = el.getBoundingClientRect();
      return r.height / window.innerHeight;
    });

    expect(
      mapRatio,
      'אזור המפה אמור לתפוס לפחות ~60% מגובה ה-viewport בזמן משחק בנייד'
    ).toBeGreaterThan(0.6);
  });
});
