---
description: Convert a legacy Selenium test file to Playwright (TypeScript), preserving every assertion and using our project's storageState pattern for auth.
---

# /cf-orchestrate-convert $ARGUMENTS

Convert the test file at `$ARGUMENTS` from Selenium (Python, unittest-based) to Playwright (TypeScript, @playwright/test).

## Steps

1. **Read the source file** at the path in $ARGUMENTS. If not found, stop and ask the user for the right path — don't guess.

2. **Map fixtures.** Our Selenium suites use a `BaseTestCase` that handles login. Replace with Playwright's `storageState` pattern:
   ```ts
   import { test, expect } from '@playwright/test';
   test.use({ storageState: 'auth/admin.json' });
   ```

3. **Translate selectors.**
   - `By.ID('foo')` → `page.locator('#foo')`
   - `By.CSS_SELECTOR('.bar')` → `page.locator('.bar')`
   - `By.XPATH(...)` → prefer `getByRole/getByText/getByTestId`, fall back to `locator('xpath=...')` only if no semantic alternative
   - Selenium's `find_element` is sync; Playwright's `locator` is lazy — wrap actions, not lookups

4. **Translate assertions.**
   - `assertEqual(a, b)` → `expect(a).toBe(b)`
   - `assertTrue(elem.is_displayed())` → `await expect(locator).toBeVisible()`
   - `WebDriverWait(...).until(...)` → built-in Playwright auto-wait (delete the explicit wait)

5. **Place the converted file** at `tests/e2e/<original-name-kebab-cased>.spec.ts`. Keep one test per `test()` block.

6. **Run it.** `npx playwright test tests/e2e/<file>.spec.ts --reporter=list`. If it fails, iterate — but show the user the diff before each retry so they can intervene.

7. **Delete the old file** ONLY after a green run.

## Don'ts

- ❌ Don't bulk-convert multiple files in one invocation — call `/cf-orchestrate-convert` once per file.
- ❌ Don't add `await page.waitForTimeout(...)` — that's the Selenium habit we're escaping.
- ❌ Don't change test logic to "make it pass" — if the test was correct in Selenium, it should be correct in Playwright. If it can't, surface the discrepancy.

## Refs

- `tests/README.md` — our Playwright conventions
- `auth/README.md` — how the storageState files are generated
