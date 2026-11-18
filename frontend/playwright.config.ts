import { defineConfig, devices } from "@playwright/test";

// E2E は模擬版(Firebase Auth、BigQuery)と API が起動している前提で動かす。
// 起動から実行までは scripts/e2e_run.sh が行う。本物の Google ログインは自動操作できないため使わない
const PORT = 3000;
const API_BASE_URL = process.env.EVAL_BASE_URL ?? "http://127.0.0.1:8080";

export default defineConfig({
  testDir: "./e2e",
  // 模擬版のデータを共有するため、1件ずつ順に実行する
  workers: 1,
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  // BigQuery 模擬版はサマリーの集計に1件あたり約2秒かかり、登録が続くと待ちが重なる。
  // 合否の条件は変えず、表示を待つ時間だけを延ばす
  expect: { timeout: 15_000 },
  timeout: 60_000,
  reporter: "list",
  use: {
    baseURL: `http://127.0.0.1:${PORT}`,
    trace: "retain-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    // デプロイと同じ本番用ビルドで確かめる。NEXT_PUBLIC_* はビルド時に埋め込まれる
    command: `npm run build && npm run start -- --hostname 127.0.0.1 --port ${PORT}`,
    url: `http://127.0.0.1:${PORT}`,
    reuseExistingServer: false,
    timeout: 240_000,
    env: {
      NEXT_PUBLIC_FIREBASE_API_KEY: "demo-key",
      NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN: "demo-plutus-lite.firebaseapp.com",
      NEXT_PUBLIC_FIREBASE_PROJECT_ID: "demo-plutus-lite",
      NEXT_PUBLIC_FIREBASE_AUTH_EMULATOR_HOST: "127.0.0.1:9099",
      NEXT_PUBLIC_API_BASE_URL: API_BASE_URL,
    },
  },
});
