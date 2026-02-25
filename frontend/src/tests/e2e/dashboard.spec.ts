> **Work in Progress** - E2E tests require the full application stack running.
> To be implemented once the application is stable.

Example test structure:

```typescript
import { test, expect } from '@playwright/test'

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:5173')
  })

  test('displays dashboard page', async ({ page }) => {
    await expect(page.locator('h2')).toContainText('Dashboard')
  })

  test('navigates to crawler page', async ({ page }) => {
    await page.click('text=Site Crawler')
    await expect(page.locator('h2')).toContainText('Site Crawler')
  })
})
```