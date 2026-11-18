import { expect, test, type Page } from '@playwright/test';

const API = process.env.PATHSNAP_TEST_API ?? 'http://127.0.0.1:8000';
const SHOTS = process.env.PATHSNAP_SHOT_DIR; // when set, save evidence screenshots there

async function shot(page: Page, name: string) {
  if (!SHOTS) return;
  await page.waitForLoadState('networkidle').catch(() => {});
  await page.waitForTimeout(600); // let fitBounds finish and canvases redraw
  await page.screenshot({ path: `${SHOTS}/${name}.png`, fullPage: false });
}

async function openApp(page: Page, api = API) {
  await page.goto(`/?api=${encodeURIComponent(api)}`);
}

test.describe('live API (real development pipeline)', () => {
  test('select a trip, reconstruct, inspect; request ID shown', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await openApp(page);
    await expect(page.getByText('Connected, ready')).toBeVisible();
    await expect(page.getByText('Development data')).toBeVisible();
    const radios = page.getByRole('radio');
    await expect(radios).toHaveCount(10);
    await shot(page, '01-initial-1440');
    await page.getByRole('radio', { name: '00000052' }).check();
    await page.getByRole('button', { name: 'Reconstruct route' }).click();
    await expect(page.getByRole('heading', { name: /Trip 00000052/ })).toBeVisible();
    await expect(page.getByText(/matched of 262/)).toBeVisible();
    await expect(page.getByText(/Request ID [0-9a-f]{32}/)).toBeVisible();
    await shot(page, '02-result-1440');
  });

  for (const [w, h, tag] of [[1366, 768, '1366'], [390, 844, '390']] as const) {
    test(`layout at ${w}x${h} keeps map and action usable`, async ({ page }) => {
      await page.setViewportSize({ width: w, height: h });
      await openApp(page);
      await page.getByRole('radio', { name: '00000056' }).check();
      await page.getByRole('button', { name: 'Reconstruct route' }).click();
      await expect(page.getByRole('heading', { name: /Trip 00000056/ })).toBeVisible({ timeout: 30_000 });
      const map = await page.locator('.map').boundingBox();
      expect(map!.width).toBeGreaterThan(w < 500 ? 350 : 900);
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
      expect(overflow).toBeLessThanOrEqual(0);
      await shot(page, `03-result-${tag}`);
    });
  }

  test('keyboard only: choose trip and reconstruct', async ({ page }) => {
    await openApp(page);
    await expect(page.getByText('Connected, ready')).toBeVisible();
    await page.getByRole('radio', { name: '00000000' }).focus();
    await page.keyboard.press('ArrowRight');
    await expect(page.getByRole('radio', { name: '00000007' })).toBeChecked();
    await page.keyboard.press('Tab');
    await expect(page.getByRole('button', { name: 'Reconstruct route' })).toBeFocused();
    await page.keyboard.press('Enter');
    await expect(page.getByRole('heading', { name: /Trip 00000007/ })).toBeVisible();
  });

  test('works when crypto.randomUUID is unavailable (plain-HTTP LAN origin)', async ({ page }) => {
    await page.addInitScript(() => {
      Object.defineProperty(globalThis.crypto, 'randomUUID', { value: undefined, configurable: true });
    });
    await openApp(page);
    await expect(page.getByText('Connected, ready')).toBeVisible();
    await page.getByRole('radio', { name: '00000052' }).check();
    await page.getByRole('button', { name: 'Reconstruct route' }).click();
    await expect(page.getByText(/Request ID [0-9a-f]{32}/)).toBeVisible();
  });

  test('layer toggles are real checkboxes', async ({ page }) => {
    await openApp(page);
    const route = page.getByRole('checkbox', { name: 'Predicted route' });
    await expect(route).toBeChecked();
    await route.uncheck();
    await expect(route).not.toBeChecked();
  });
});

test.describe('error and edge states (mocked responses)', () => {
  test('unreachable server shows actionable message and retry', async ({ page }) => {
    await openApp(page, 'http://127.0.0.1:9');
    await expect(page.getByText("Can't reach the PathSnap server")).toBeVisible();
    await expect(page.getByRole('button', { name: 'Retry connection' })).toBeVisible();
    await shot(page, '10-unreachable');
  });

  test('evaluator data not configured is explicit and offers no substitute trips', async ({ page }) => {
    await page.route('**/health', (r) =>
      r.fulfill({ json: { schema_version: '0.1.0', service: 'pathsnap-api', api_version: '0.1.0', status: 'degraded', ready: false, mode: 'evaluator', data_configured: false, model: null, not_ready_reasons: ['data_not_configured'] } }),
    );
    await page.route('**/trips', (r) =>
      r.fulfill({ status: 503, json: { schema_version: '0.1.0', request_id: 'mocked-0000', error: { code: 'data_not_configured', message: 'Reserved evaluation trips are not configured on the server.', retryable: false } } }),
    );
    await openApp(page, 'http://mock.api');
    await expect(page.getByText('Reserved evaluation trips are not configured on the server.')).toBeVisible();
    await expect(page.getByRole('radio')).toHaveCount(0);
    await shot(page, '11-evaluator-unconfigured');
  });

  test('stale response for an earlier trip never replaces the newer selection', async ({ page }) => {
    await openApp(page);
    await expect(page.getByText('Connected, ready')).toBeVisible();
    let first = true;
    await page.route('**/predict', async (route) => {
      if (first) {
        first = false;
        await new Promise((r) => setTimeout(r, 2500)); // slow, earlier request
      }
      await route.continue().catch(() => {}); // the earlier request may already be aborted
    });
    await page.getByRole('radio', { name: '00000077' }).check();
    await page.getByRole('button', { name: 'Reconstruct route' }).click();
    await page.getByRole('radio', { name: '00000052' }).check();
    await page.getByRole('button', { name: 'Reconstruct route' }).click();
    await expect(page.getByRole('heading', { name: /Trip 00000052/ })).toBeVisible();
    await page.waitForTimeout(3500);
    await expect(page.getByRole('heading', { name: /Trip 00000052/ })).toBeVisible();
    await expect(page.getByRole('heading', { name: /Trip 00000077/ })).toHaveCount(0);
  });

  test('server error shows message, request ID and retry', async ({ page }) => {
    await openApp(page);
    await expect(page.getByText('Connected, ready')).toBeVisible();
    await page.route('**/predict', (r) =>
      r.fulfill({ status: 500, headers: { 'X-Request-ID': 'mockedrequestid0001' }, json: { schema_version: '0.1.0', request_id: 'mockedrequestid0001', error: { code: 'prediction_failed', message: 'The prediction pipeline failed for this trip.', retryable: false } } }),
    );
    await page.getByRole('radio', { name: '00000052' }).check();
    await page.getByRole('button', { name: 'Reconstruct route' }).click();
    await expect(page.getByText('The prediction pipeline failed for this trip.')).toBeVisible();
    await expect(page.getByText('mockedrequestid0001')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Try again' })).toBeVisible();
    await shot(page, '12-predict-failed');
  });
});

test('changing server mid-request drops the old server context', async ({ page }) => {
  await openApp(page);
  await expect(page.getByText('Connected, ready')).toBeVisible();
  await page.route('**/predict', async (route) => {
    await new Promise((r) => setTimeout(r, 2500));
    await route.continue().catch(() => {});
  });
  await page.getByRole('radio', { name: '00000077' }).check();
  await page.getByRole('button', { name: 'Reconstruct route' }).click();
  // switch to a "second server" that offers a disjoint trip list
  await page.route('http://other.api/health', (r) =>
    r.fulfill({ json: { schema_version: '0.1.0', service: 'pathsnap-api', api_version: '0.1.0', status: 'ok', ready: true, mode: 'evaluator', data_configured: true, model: { version: 'm', kind: 'trained', family: 'f', decoder: 'hmm_viterbi', run_id: 'r' }, not_ready_reasons: [] } }),
  );
  await page.route('http://other.api/trips', (r) =>
    r.fulfill({ json: { schema_version: '0.1.0', mode: 'evaluator', partition_label: 'Reserved evaluation trips', trip_ids: ['E0000001'], count: 1 } }),
  );
  await page.getByText('Server address').click();
  await page.getByLabel('API URL').fill('http://other.api');
  await page.getByRole('button', { name: 'Connect' }).click();
  await expect(page.getByRole('radio', { name: 'E0000001' })).toBeVisible();
  await page.waitForTimeout(3500);
  await expect(page.getByRole('heading', { name: /Trip 00000077/ })).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Select a trip' })).toBeDisabled();
});

test('route playback runs, pauses and resets without fake progress', async ({ page }) => {
  await openApp(page);
  await page.getByRole('radio', { name: '00000052' }).check();
  await page.getByRole('button', { name: 'Reconstruct route' }).click();
  await expect(page.getByRole('heading', { name: /Trip 00000052/ })).toBeVisible();
  await page.getByRole('combobox', { name: 'Playback speed' }).selectOption('240');
  await page.getByRole('button', { name: 'Play route' }).click();
  await expect(page.getByText(/point #\d+/)).toBeVisible();
  await page.waitForTimeout(600);
  await page.getByRole('button', { name: 'Pause' }).click();
  const paused = await page.locator('.play-status').textContent();
  await page.waitForTimeout(500);
  await expect(page.locator('.play-status')).toHaveText(paused!);
  await page.getByRole('button', { name: 'Reset' }).click();
  await expect(page.locator('.play-status')).toHaveCount(0);
  // a new prediction starts with a fresh playback state
  await page.getByRole('button', { name: 'Play route' }).click();
  await page.getByRole('radio', { name: '00000091' }).check();
  await page.getByRole('button', { name: 'Reconstruct route' }).click();
  await expect(page.getByRole('heading', { name: /Trip 00000091/ })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Play route' })).toBeVisible();
});

test('observations can be inspected without a pointer', async ({ page }) => {
  await openApp(page);
  await page.getByRole('radio', { name: '00000052' }).check();
  await page.getByRole('button', { name: 'Reconstruct route' }).click();
  await expect(page.getByRole('heading', { name: /Trip 00000052/ })).toBeVisible();
  await page.getByLabel('Inspect observation').fill('10');
  await page.getByLabel('Inspect observation').press('Enter');
  await expect(page.getByRole('heading', { name: 'Observation #10' })).toBeVisible();
  await page.getByRole('button', { name: 'Next observation' }).click();
  await expect(page.getByRole('heading', { name: 'Observation #11' })).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(page.getByRole('heading', { name: /Observation #/ })).toHaveCount(0);
});
