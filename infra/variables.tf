variable "project_id" {
  description = "検証環境の GCP プロジェクト"
  type        = string
  default     = "plutus-lite-dev"
}

variable "region" {
  description = "リソースを置くリージョン"
  type        = string
  default     = "asia-northeast1"
}

variable "allow_destroy" {
  description = "true のときだけ、データを持つリソース(BigQuery)と Cloud Run を destroy できる。A7 の再作成テストでのみ true にする"
  type        = bool
  default     = false
}

variable "placeholder_image" {
  description = "アプリのイメージができるまで Cloud Run に置く仮のイメージ。以後のイメージ更新は Cloud Build が行い、Terraform は追従しない"
  type        = string
  default     = "us-docker.pkg.dev/cloudrun/container/hello"
}
