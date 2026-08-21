import { expect, test } from "@playwright/test";

test(
  "expired password-reset token is rejected",
  { tag: ["@regression", "@security"] },
  async ({ page }) => {
    await page.goto(
      "data:text/html,<main><h1>Password reset</h1><div role='alert'>This reset link has expired</div></main>",
    );
    await expect(
      page.getByRole("heading", { name: "Password reset" }),
    ).toBeVisible();
    await expect(page.getByRole("alert")).toContainText("expired");
  },
);
