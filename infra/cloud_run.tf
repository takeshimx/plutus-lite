# API と画面の Cloud Run。イメージは Cloud Build がデプロイするため、Terraform は仮のイメージで作るだけにする。
# 許可リスト(ALLOWED_EMAILS)はメールアドレスを含むため、ここには書かない。デプロイ時に設定する。

resource "google_cloud_run_v2_service" "api" {
  name                = "plutus-lite-api"
  location            = var.region
  ingress             = "INGRESS_TRAFFIC_ALL"
  deletion_protection = !var.allow_destroy

  template {
    service_account = google_service_account.api.email

    scaling {
      min_instance_count = 0
      max_instance_count = 2
    }

    containers {
      image = var.placeholder_image

      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "BQ_DATASET"
        value = google_bigquery_dataset.main.dataset_id
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
        cpu_idle = true # リクエストを処理している間だけ課金
      }
    }
  }

  lifecycle {
    ignore_changes = [
      template[0].containers[0].image,
      template[0].containers[0].env,
      client,
      client_version,
    ]
  }

  depends_on = [google_project_service.this]
}

resource "google_cloud_run_v2_service" "web" {
  name                = "plutus-lite-web"
  location            = var.region
  ingress             = "INGRESS_TRAFFIC_ALL"
  deletion_protection = !var.allow_destroy

  template {
    service_account = google_service_account.web.email

    scaling {
      min_instance_count = 0
      max_instance_count = 2
    }

    containers {
      image = var.placeholder_image

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
        cpu_idle = true
      }
    }
  }

  lifecycle {
    ignore_changes = [
      template[0].containers[0].image,
      template[0].containers[0].env,
      client,
      client_version,
    ]
  }

  depends_on = [google_project_service.this]
}

# 公開範囲: 両サービスともインターネットから呼べるようにする。
# 画面はブラウザから直接開き、API はブラウザから Firebase の IDトークン付きで呼ぶため。
# 認証と許可リストの判定は API のコードで行う(A1)。
resource "google_cloud_run_v2_service_iam_member" "api_public" {
  name     = google_cloud_run_v2_service.api.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_v2_service_iam_member" "web_public" {
  name     = google_cloud_run_v2_service.web.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}
