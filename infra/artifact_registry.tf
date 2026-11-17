resource "google_artifact_registry_repository" "app" {
  repository_id = "plutus-lite"
  location      = var.region
  format        = "DOCKER"
  description   = "plutus-lite の API と画面のコンテナイメージ"

  # 保存料を抑えるため、古いイメージを消す。各イメージの新しい5件は残す
  cleanup_policy_dry_run = false

  cleanup_policies {
    id     = "keep-recent"
    action = "KEEP"
    most_recent_versions {
      keep_count = 5
    }
  }

  cleanup_policies {
    id     = "delete-old"
    action = "DELETE"
    condition {
      older_than = "604800s" # 7日
    }
  }

  depends_on = [google_project_service.this]
}
