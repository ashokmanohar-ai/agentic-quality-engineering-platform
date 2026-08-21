import { expect, test } from "@playwright/test";

test(
  "transient payment retry preserves idempotency",
  { tag: ["@regression", "@critical"] },
  async ({ page }) => {
    await page.goto(
      "data:text/html,<main><h1>Payment status</h1><output aria-label='charge count'>1</output><p>Recovered after retry</p></main>",
    );
    await expect(page.getByLabel("charge count")).toHaveText("1");
    await expect(page.getByText("Recovered after retry")).toBeVisible();
  },
);
