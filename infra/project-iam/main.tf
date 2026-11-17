# プロジェクト単位の IAM。エージェントには変更権限が無いため、人が自分の権限で apply する。
# 先に infra/ を apply し、サービスアカウントを作ってから実行する。

terraform {
  required_version = ">= 1.14"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 8.11"
    }
  }

  backend "gcs" {
    bucket = "plutus-lite-dev-tfstate"
    prefix = "dev/project-iam"
  }
}

variable "project_id" {
  type    = string
  default = "plutus-lite-dev"
}

provider "google" {
  project = var.project_id
}

# API が BigQuery のクエリを実行するための権限。
# データの読み書きはデータセット単位で別に付けている(infra/bigquery.tf)。
resource "google_project_iam_member" "api_bq_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:plutus-lite-api@${var.project_id}.iam.gserviceaccount.com"
}

# Cloud Build のデプロイ用サービスアカウント(Issue #15)。
# Cloud Run のサービスを更新する権限と、ビルドのログを書く権限
locals {
  build_sa = "serviceAccount:plutus-lite-build@${var.project_id}.iam.gserviceaccount.com"
}

resource "google_project_iam_member" "build_run_developer" {
  project = var.project_id
  role    = "roles/run.developer"
  member  = local.build_sa
}

resource "google_project_iam_member" "build_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = local.build_sa
}

# 許可リスト(ログインを許可するメールアドレス)。値は人が gcloud で登録し、リポジトリには書かない(ADR-002)
resource "google_secret_manager_secret" "allowed_emails" {
  project   = var.project_id
  secret_id = "plutus-lite-allowed-emails"

  # 保存場所は東京の1か所だけにする
  replication {
    user_managed {
      replicas {
        location = "asia-northeast1"
      }
    }
  }
}

# API の実行用アカウントだけが読める
resource "google_secret_manager_secret_iam_member" "api_reads_allowed_emails" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.allowed_emails.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:plutus-lite-api@${var.project_id}.iam.gserviceaccount.com"
}
