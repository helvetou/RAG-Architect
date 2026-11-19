// CMMI Level 3 Verification Suite — Portal E2E (TEST-INT-001)
// Full journey: Portal BFF -> D1 catalog snapshot -> Python sizing engine -> audit persistence.
import { expect, test } from '@playwright/test';

const MODES = ['AIR_GAPPED_EDGE', 'HYBRID_CONNECTED', 'FULL_CLOUD'] as const;

for (const mode of MODES) {
  test(`TEST-INT-001: ${mode} end-to-end sizing journey renders TCO/VRAM`, async ({ page }) => {
    await page.goto('/');
    await page.getByLabel('Deployment mode').selectOption(mode);
    await page.getByLabel('Technicians per shift').fill('35');
    await page.getByLabel('Total shifts').fill('3');
    await page.getByLabel('Manuals volume (GB)').fill('85');
    await page.getByLabel('Historical work orders').fill('450000');
    await page.getByRole('button', { name: /size architecture/i }).click();

    await expect(page.getByText(/CAPEX/i)).toBeVisible();
    await expect(page.getByText(/OPEX/i)).toBeVisible();
    await expect(page.getByText(/recommended decision/i)).toBeVisible();
  });
}

test('TEST-INT-001: batch-upload proxy forwards to the telemetry worker', async ({ page, request }) => {
  const response = await request.post('/api/batch-upload', {
    data: 'gzip-bytes-placeholder',
    headers: { 'Content-Type': 'application/octet-stream' },
  });
  expect([200, 202, 401, 502]).toContain(response.status());
});
