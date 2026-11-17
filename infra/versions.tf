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
    prefix = "dev/main"
  }
}

# 認証は環境変数 GOOGLE_OAUTH_ACCESS_TOKEN で渡す(README.md を参照)。
# エージェントは plutus-lite-agent になりすましたトークンを使う。
provider "google" {
  project = var.project_id
  region  = var.region
}
