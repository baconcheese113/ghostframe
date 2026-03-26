import { test, expect } from '@playwright/test';

test.describe('GhostFrame dashboard', () => {
  test('summary cards show demo counts', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText('47')).toBeVisible();   // Silent Analyzed
    await expect(page.getByText('14')).toBeVisible();   // Reclassified
  });

  test('pipeline trace is visible', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByTestId('pipeline-trace')).toBeVisible();
  });

  test('pipeline trace completes all 8 steps', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('[data-step-state="complete"]')).toHaveCount(8, {
      timeout: 5000,
    });
  });

  test('sankey chart renders with paths', async ({ page }) => {
    await page.goto('/');
    const svg = page.locator('svg[data-testid="sankey-chart"]');
    await expect(svg).toBeVisible();
    await expect(svg.locator('path')).toHaveCount(4);
  });

  test('variant table shows 14 rows', async ({ page }) => {
    await page.goto('/');
    const rows = page.locator('[data-testid="variant-table"] tbody tr');
    await expect(rows).toHaveCount(14);
  });

  test('first variant is selected by default and shows detail panels', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByTestId('evidence-panel')).toBeVisible();
    await expect(page.getByTestId('neoantigen-panel')).toBeVisible();
    await expect(page.getByTestId('narrative-panel')).toBeVisible();
  });

  test('clicking a different variant row updates detail panels', async ({ page }) => {
    await page.goto('/');
    // Click the second row
    await page.locator('[data-testid="variant-table"] tbody tr').nth(1).click();
    await expect(page.getByTestId('evidence-panel')).toBeVisible();
    await expect(page.getByTestId('neoantigen-panel')).toBeVisible();
    await expect(page.getByTestId('narrative-panel')).toBeVisible();
  });

  test('New Analysis drawer opens on button click', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: /New Analysis/i }).click();
    await expect(page.getByTestId('analysis-drawer')).toBeVisible();
  });

  test('New Analysis drawer shows fake progress on submit', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: /New Analysis/i }).click();
    await expect(page.getByTestId('analysis-drawer')).toBeVisible();
    await page.getByRole('button', { name: /^Analyze$/i }).click();
    await expect(page.getByText(/Scanning/i)).toBeVisible();
  });

  test('mobile layout: helix appears above sankey', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('/');
    const helix = page.getByTestId('helix-explorer');
    const sankey = page.locator('svg[data-testid="sankey-chart"]');
    const helixBox = await helix.boundingBox();
    const sankeyBox = await sankey.boundingBox();
    expect(helixBox!.y).toBeLessThan(sankeyBox!.y);
  });
});
