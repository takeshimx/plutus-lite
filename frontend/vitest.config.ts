import { configDefaults, defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    // e2e/ は Playwright のテスト。npx playwright test で実行する
    exclude: [...configDefaults.exclude, "e2e/**"],
  },
});
