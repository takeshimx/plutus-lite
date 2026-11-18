/**
 * P8 acceptance through the screen (Issue #31).
 * A2: create, edit, delete are reflected in the list.
 * A4: the summary on the screen matches the list for the same month.
 * A1: an account that is not on the allow list sees no data.
 */
import { expect, test } from "@playwright/test";

import { addEntry, openMonth, parseYen, rowsWith, signIn, testMonth } from "./helpers";

const ALLOWED = "user-a@example.com"; // scripts/eval_up.sh の ALLOWED_EMAILS に入っている

test("A2: create, edit, and delete are reflected in the list", async ({ page }) => {
  const month = testMonth(1);
  const category = `e2e-food-${Date.now()}`;
  await signIn(page, ALLOWED);
  await openMonth(page, month);

  // Create
  await addEntry(page, { date: `${month}-15`, type: "支出", amount: 1234, category, note: "lunch" });
  const row = rowsWith(page, category);
  await expect(row).toHaveCount(1);
  await expect(row).toContainText("1,234");
  await expect(row).toContainText("lunch");

  // Saved on the server, not only on the screen
  await page.reload();
  await openMonth(page, month);
  await expect(rowsWith(page, category)).toHaveCount(1);

  // Edit
  await rowsWith(page, category).getByRole("button", { name: "編集" }).click();
  const editForm = page.locator("tbody form");
  await editForm.getByLabel("金額").fill("2000");
  await editForm.getByLabel("メモ").fill("dinner");
  await editForm.getByRole("button", { name: "保存" }).click();
  await expect(page.locator("tbody form")).toHaveCount(0);
  await expect(rowsWith(page, category)).toContainText("2,000");
  await expect(rowsWith(page, category)).toContainText("dinner");

  // Delete (the screen asks for confirmation first)
  page.once("dialog", (dialog) => dialog.accept());
  await rowsWith(page, category).getByRole("button", { name: "削除" }).click();
  await expect(rowsWith(page, category)).toHaveCount(0);

  await page.reload();
  await openMonth(page, month);
  await expect(rowsWith(page, category)).toHaveCount(0);
});

test("A2: a transaction appears only in its own month", async ({ page }) => {
  const month = testMonth(2);
  const other = testMonth(3);
  const category = `e2e-month-${Date.now()}`;
  await signIn(page, ALLOWED);
  await openMonth(page, month);
  await addEntry(page, { date: `${month}-28`, type: "支出", amount: 500, category });
  await expect(rowsWith(page, category)).toHaveCount(1);

  await openMonth(page, other);
  await expect(rowsWith(page, category)).toHaveCount(0);
});

test("A4: summary totals on the screen match the list", async ({ page }) => {
  const month = testMonth(4);
  await signIn(page, ALLOWED);
  await openMonth(page, month);

  // A refund (negative expense) is included, as in the golden set
  await addEntry(page, { date: `${month}-01`, type: "収入", amount: 300000, category: "給与" });
  await addEntry(page, { date: `${month}-05`, type: "支出", amount: 5000, category: "食費" });
  await addEntry(page, { date: `${month}-10`, type: "支出", amount: 3000, category: "交通費" });
  await addEntry(page, { date: `${month}-20`, type: "支出", amount: -1000, category: "交通費" });
  await expect(page.locator("tbody tr")).toHaveCount(4);

  const summary = page.locator("section.summary");
  await expect(summary.locator("dd").nth(0)).toContainText("300,000");
  await expect(summary.locator("dd").nth(1)).toContainText("7,000");
  await expect(summary.locator("li").filter({ hasText: "食費" })).toContainText("5,000");
  await expect(summary.locator("li").filter({ hasText: "交通費" })).toContainText("2,000");

  // The same totals, added up from the list rows
  const rows = await page.locator("tbody tr").all();
  let income = 0;
  let expense = 0;
  for (const row of rows) {
    const cells = row.locator("td");
    const amount = parseYen(await cells.nth(2).innerText());
    if ((await cells.nth(1).innerText()) === "収入") income += amount;
    else expense += amount;
  }
  expect(parseYen(await summary.locator("dd").nth(0).innerText())).toBe(income);
  expect(parseYen(await summary.locator("dd").nth(1).innerText())).toBe(expense);
});

test("A1: an account that is not on the allow list sees no data", async ({ page }) => {
  await signIn(page, `stranger-${Date.now()}@example.com`);
  await expect(page.getByText("このアカウントは利用を許可されていません").first()).toBeVisible();
  await expect(page.locator("tbody tr").filter({ hasText: "e2e-" })).toHaveCount(0);
});
