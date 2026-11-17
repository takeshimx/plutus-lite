# Cloud Build のデプロイ用サービスアカウント(Issue #15)。
# ここではリソース単位の権限だけを付ける。プロジェクト単位の権限は infra/project-iam/ で人が付ける。

resource "google_service_account" "build" {
  account_id   = "plutus-lite-build"
  display_name = "plutus-lite Cloud Build deployer"

  depends_on = [google_project_service.this]
}

# イメージの置き場にだけ書き込める
resource "google_artifact_registry_repository_iam_member" "build_writer" {
  location   = google_artifact_registry_repository.app.location
  repository = google_artifact_registry_repository.app.name
  role       = "roles/artifactregistry.writer"
  member     = "serviceAccount:${google_service_account.build.email}"
}

# Cloud Run に、API と画面の実行用サービスアカウントを指定してデプロイできるようにする。
# この2つのサービスアカウント以外にはなれない
resource "google_service_account_iam_member" "build_act_as" {
  for_each = {
    api = google_service_account.api.name
    web = google_service_account.web.name
  }

  service_account_id = each.value
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.build.email}"
}

output "build_service_account" {
  value = google_service_account.build.email
}
