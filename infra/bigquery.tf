# データモデルは docs/design.md.md の「2. データモデル案」に従う。

resource "google_bigquery_dataset" "main" {
  dataset_id = "plutus_lite"
  location   = var.region

  # allow_destroy が false の間は、中身のあるデータセットを destroy できない
  delete_contents_on_destroy = var.allow_destroy

  depends_on = [google_project_service.this]
}

resource "google_bigquery_table" "transactions" {
  dataset_id          = google_bigquery_dataset.main.dataset_id
  table_id            = "transactions"
  deletion_protection = !var.allow_destroy

  # 件数が少ないためパーティションは付けず、user_id でクラスタ化する
  clustering = ["user_id"]

  schema = jsonencode([
    { name = "transaction_id", type = "STRING", mode = "REQUIRED", description = "サーバーが発行する UUID" },
    { name = "user_id", type = "STRING", mode = "REQUIRED", description = "検証済み IDトークンの UID。画面からは受け取らない" },
    { name = "date", type = "DATE", mode = "REQUIRED", description = "取引日" },
    { name = "type", type = "STRING", mode = "REQUIRED", description = "income または expense" },
    { name = "amount_jpy", type = "INT64", mode = "REQUIRED", description = "円の整数。負数を許す" },
    { name = "category", type = "STRING", mode = "REQUIRED", description = "自由入力の分類" },
    { name = "note", type = "STRING", mode = "NULLABLE", description = "メモ。最大200文字" },
    { name = "created_at", type = "TIMESTAMP", mode = "REQUIRED", description = "登録時刻。サーバーが付ける" },
  ])
}

# API はこのデータセットだけを読み書きできる
resource "google_bigquery_dataset_iam_member" "api_data_editor" {
  dataset_id = google_bigquery_dataset.main.dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${google_service_account.api.email}"
}
