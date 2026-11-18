import { expect, type Locator, type Page } from "@playwright/test";

/** 模擬版の Google ログイン画面で、指定したメールアドレスのアカウントを作ってログインする */
export async function signIn(page: Page, email: string): Promise<void> {
  await page.goto("/");
  const popupPromise = page.waitForEvent("popup");
  await page.getByRole("button", { name: "Google でログイン" }).click();
  const popup = await popupPromise;
  await popup.waitForLoadState();
  await popup.locator("#add-account-button").click();
  await popup.locator("#email-input").fill(email);
  await popup.locator("#sign-in").click();
  await expect(page.getByText(email)).toBeVisible();
}

/**
 * 実行ごとに重ならない月(YYYY-MM)。模擬版のデータは実行の間で残ることがあるため、
 * 遠い将来の年を実行時刻から決め、テストごとに月を変える
 */
const RUN_YEAR = 3000 + (Math.floor(Date.now() / 1000) % 6000);
export function testMonth(index: number): string {
  return `${RUN_YEAR}-${String(index).padStart(2, "0")}`;
}

export async function openMonth(page: Page, month: string): Promise<void> {
  await page.getByLabel("月:").fill(month);
}

export interface Entry {
  date: string;
  type: "支出" | "収入";
  amount: number;
  category: string;
  note?: string;
}

/** 画面上部の登録フォームから1件登録し、一覧に出るまで待つ */
export async function addEntry(page: Page, entry: Entry): Promise<void> {
  const form = page.locator("form").first();
  await form.getByLabel("日付").fill(entry.date);
  await form.getByLabel("種別").selectOption({ label: entry.type });
  await form.getByLabel("金額").fill(String(entry.amount));
  await form.getByLabel("カテゴリ").fill(entry.category);
  await form.getByLabel("メモ").fill(entry.note ?? "");
  await form.getByRole("button", { name: "登録" }).click();
  await expect(form.getByLabel("金額")).toHaveValue(""); // 登録に成功するとフォームが空になる
}

export function rowsWith(page: Page, text: string): Locator {
  return page.locator("tbody tr").filter({ hasText: text });
}

/** 表示された金額(例: ￥1,234、-￥1,000)を整数に戻す。テスト側の照合にだけ使う */
export function parseYen(text: string): number {
  const negative = text.includes("-") || text.includes("−");
  const digits = Number(text.replace(/[^0-9]/g, ""));
  return negative ? -digits : digits;
}
