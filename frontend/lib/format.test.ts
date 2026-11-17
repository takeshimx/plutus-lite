import { describe, expect, it } from "vitest";

import { currentMonth, formatYen, today } from "./format";

describe("formatYen", () => {
  it("formats integer yen with separators", () => {
    expect(formatYen(1500)).toBe("￥1,500");
    expect(formatYen(-1000)).toBe("-￥1,000");
  });
});

describe("dates", () => {
  it("pads month and day", () => {
    const d = new Date(2026, 0, 5);
    expect(currentMonth(d)).toBe("2026-01");
    expect(today(d)).toBe("2026-01-05");
  });
});
