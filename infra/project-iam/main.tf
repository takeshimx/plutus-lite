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
