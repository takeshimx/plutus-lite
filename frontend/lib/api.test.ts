import { describe, expect, it } from "vitest";

import { messageFor } from "./api";

describe("messageFor", () => {
  it("distinguishes 401 from 403 (A1)", () => {
    expect(messageFor(401)).toBe("ログインし直してください");
    expect(messageFor(403)).toBe("このアカウントは利用を許可されていません");
  });

  it("falls back for unknown status", () => {
    expect(messageFor(500)).toBe("エラーが発生しました");
  });
});
