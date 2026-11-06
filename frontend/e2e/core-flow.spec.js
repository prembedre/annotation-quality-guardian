import { test, expect } from '@playwright/test';

test.describe('Annotation Quality Guardian — Core Workflow', () => {
  test.beforeEach(async ({ page }) => {
    // Intercept auth routes
    await page.route('**/auth/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 1,
          email: 'admin@annotationops.io',
          full_name: 'System Admin',
          role: 'admin',
        }),
      });
    });

    await page.route('**/auth/login', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'mock-valid-jwt-token',
          user: {
            id: 1,
            email: 'admin@annotationops.io',
            full_name: 'System Admin',
            role: 'admin',
          },
        }),
      });
    });

    // Intercept project export
    await page.route('**/api/projects/*/export*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'text/csv',
        headers: {
          'Content-Disposition': 'attachment; filename="project_1_review_export.csv"',
        },
        body: 'item_id,label,flagged\n101,SPAM,true\n',
      });
    });

    // Intercept project list
    await page.route('**/api/projects', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 1,
            name: 'Project Alpha',
            description: 'Core benchmark dataset',
            total_items: 50,
            annotators_count: 5,
          },
        ]),
      });
    });

    // Intercept scores summary
    await page.route('**/api/scores/summary*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          project_id: 1,
          kappa: 0.825,
          total_items: 50,
          annotators_count: 5,
          avg_gold_accuracy: 0.94,
          avg_trust_score: 0.88,
        }),
      });
    });

    // Intercept scores compute
    await page.route('**/api/scores/compute*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          message: 'Scored 50 items successfully.',
          result: {
            trust_score_summary: {
              total_items_processed: 50,
            },
          },
        }),
      });
    });

    // Intercept scores list
    await page.route('**/api/scores*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          scores: [
            {
              item_id: 101,
              trust_score: 0.55,
              gold_accuracy: 0.6,
              agreement_score: 0.5,
              computed_at: new Date().toISOString(),
            },
          ],
        }),
      });
    });

    // Intercept dataset upload
    await page.route('**/api/annotations/upload', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          message: 'Dataset uploaded and processed successfully!',
          total_records: 25,
          inserted_records: 25,
          duplicate_records: 0,
          failed_records: 0,
        }),
      });
    });

    // Intercept review resolve
    await page.route('**/api/review/*/resolve', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ message: 'Item resolved successfully' }),
      });
    });

    // Intercept review queue items
    await page.route('**/api/review/queue*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          total: 1,
          page: 1,
          page_size: 10,
          total_pages: 1,
          items: [
            {
              id: 101,
              item_id: 101,
              label: 'SPAM',
              text_content: 'URGENT: Claim reward lottery immediately',
              confidence: 0.55,
              flagged: true,
              annotations: [
                { annotator_id: 1, label: 'SPAM', confidence: 0.55 },
                { annotator_id: 2, label: 'HAM', confidence: 0.8 },
              ],
            },
          ],
        }),
      });
    });

    // Seed localStorage with active project and auth token
    await page.addInitScript(() => {
      window.localStorage.setItem('aqg_active_project_id', '1');
      window.localStorage.setItem('aqg_auth_token', 'mock-valid-jwt-token');
    });
  });

  test('Upload -> Compute Scores -> Review Queue triage -> Resolve -> Export', async ({ page }) => {
    // Step 1: Upload Dataset
    await page.goto('/projects');
    await expect(page.getByRole('heading', { name: 'Data Projects' })).toBeVisible();

    // Click Upload Dataset button
    await page.getByRole('button', { name: /Upload Dataset/i }).first().click();
    await expect(page.getByText('Upload Annotation Dataset')).toBeVisible();

    // Attach mock CSV file
    const fileContent = 'item_id,annotator_id,label,text_content\n101,1,SPAM,"URGENT: Claim reward lottery immediately"';
    await page.setInputFiles('input[type="file"]', {
      name: 'sample_dataset.csv',
      mimeType: 'text/csv',
      buffer: Buffer.from(fileContent),
    });

    // Ingest
    await page.getByRole('button', { name: /Upload & Ingest/i }).click();
    await expect(page.getByText('Ingestion Complete')).toBeVisible();
    await expect(page.getByText('25').first()).toBeVisible(); // 25 rows ingested

    // Close upload modal with Done button
    await page.getByRole('button', { name: 'Done' }).click();

    // Step 2: Compute Scores
    await page.goto('/scores');
    await expect(page.getByRole('heading', { name: 'Quality Scores' })).toBeVisible();
    await page.getByRole('button', { name: /Recompute Scores/i }).click();
    await expect(page.getByText(/Scored 50 items successfully/i)).toBeVisible();

    // Step 3: Review Queue triage
    await page.goto('/review-queue');
    await expect(page.getByRole('heading', { name: 'Review Queue' })).toBeVisible();
    await expect(page.getByText('#101')).toBeVisible();
    await expect(page.getByText('URGENT: Claim reward lottery immediately')).toBeVisible();

    // Click row to open triage details drawer
    await page.getByText('URGENT: Claim reward lottery immediately').click();
    await expect(page.getByText('Annotator Agreement Comparison')).toBeVisible();
    await expect(page.getByText('Annotator #1')).toBeVisible();
    await expect(page.getByText('Annotator #2')).toBeVisible();

    // Close drawer
    await page.getByRole('button', { name: 'Close drawer' }).click();

    // Step 4: Resolve Item
    const confirmButton = page.getByRole('button', { name: /Confirm/i }).first();
    await expect(confirmButton).toBeVisible();
    await confirmButton.click();
    await expect(page.getByText(/Item #101 successfully confirmed!/i)).toBeVisible();

    // Step 5: Export Dataset
    await page.getByRole('button', { name: /Export Dataset/i }).click();
    await expect(page.getByText('Export Dataset Scope & Format')).toBeVisible();

    // Set up download listener before triggering export click
    const downloadPromise = page.waitForEvent('download');
    await page.getByRole('button', { name: /Download CSV/i }).click();

    const download = await downloadPromise;
    expect(download.suggestedFilename()).toContain('project_1_review_export.csv');
  });
});
