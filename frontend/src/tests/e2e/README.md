# End-to-End Tests

E2E tests for OpenSEO using Playwright.

## Setup

```bash
npm install -D @playwright/test
npx playwright install
```

## Running Tests

```bash
# Run all E2E tests
npx playwright test

# Run in headed mode
npx playwright test --headed

# Run specific test
npx playwright test dashboard.spec.ts

# Run with UI
npx playwright test --ui
```

## Test Structure

```
e2e/
├── fixtures/          # Test data
├── pages/             # Page object models
├── tests/             # Test files
└── playwright.config.ts
```

## Example Test

```typescript
import { test, expect } from '@playwright/test'

test('user can start a crawl', async ({ page }) => {
  await page.goto('http://localhost:5173')
  await page.click('text=Site Crawler')
  await page.fill('[name="url"]', 'https://example.com')
  await page.click('text=Start Crawl')
  await expect(page.locator('text=Crawling...')).toBeVisible()
})
```

## CI Integration

E2E tests run in GitHub Actions after unit tests pass.
See `.github/workflows/ci.yml` for configuration.