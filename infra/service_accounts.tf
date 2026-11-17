# Cloud Run の実行用サービスアカウント。サービスごとに分け、必要な権限だけを付ける。

resource "google_service_account" "api" {
  account_id   = "plutus-lite-api"
  display_name = "plutus-lite API runtime"

  depends_on = [google_project_service.this]
}

# 画面は GCP の API を呼ばないため、権限を付けない
resource "google_service_account" "web" {
  account_id   = "plutus-lite-web"
  display_name = "plutus-lite web runtime"

  depends_on = [google_project_service.this]
}
