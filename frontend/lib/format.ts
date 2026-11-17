const yen = new Intl.NumberFormat("ja-JP", { style: "currency", currency: "JPY" });

/** 金額の表示用。計算はしない(集計は API が行う。A6) */
export function formatYen(amount: number): string {
  return yen.format(amount);
}

/** YYYY-MM 形式の今月 */
export function currentMonth(now: Date = new Date()): string {
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
}

/** YYYY-MM-DD 形式の今日 */
export function today(now: Date = new Date()): string {
  return `${currentMonth(now)}-${String(now.getDate()).padStart(2, "0")}`;
}
