# infra

検証環境 `plutus-lite-dev` の Terraform。state は `gs://plutus-lite-dev-tfstate` に置く。

| ディレクトリ | 内容 | apply する人 |
| --- | --- | --- |
| `infra/` | API の有効化、BigQuery、Artifact Registry、実行用サービスアカウント、Cloud Run | エージェント(G4 で plan の承認後) |
| `infra/project-iam/` | プロジェクト単位の IAM | 人 |

本番環境はここでは作らない(P9 で決める)。

## 認証

エージェントは鍵ファイルを使わず、`plutus-lite-agent` になりすましたトークンを環境変数で渡す。

    export GOOGLE_OAUTH_ACCESS_TOKEN=$(gcloud auth print-access-token \
      --impersonate-service-account=plutus-lite-agent@plutus-lite-dev.iam.gserviceaccount.com)

人が `infra/project-iam/` を apply するときは、自分のトークンを使う。

    export GOOGLE_OAUTH_ACCESS_TOKEN=$(gcloud auth print-access-token)

トークンの有効期限は1時間。

## 手順

    cd infra
    terraform init
    terraform plan -out=tfplan
    terraform apply tfplan          # G4 で承認された plan だけ

    cd project-iam                  # 人が実行する
    terraform init
    terraform plan -out=tfplan
    terraform apply tfplan

## 再作成テスト(A7)

`allow_destroy` が false の間は、BigQuery のテーブルと Cloud Run を destroy できない。再作成テストのときだけ true にする。

    terraform apply -var=allow_destroy=true      # 保護を外す
    terraform destroy -var=allow_destroy=true
    terraform apply                              # 再作成

    cd project-iam && terraform apply            # 人が実行する

サービスアカウントを作り直すと、GCP は同じ名前でも別物として扱う。そのため、`project-iam` の権限は削除済みのサービスアカウントを指したまま残り、新しいサービスアカウントには付かない。再作成のたびに、人が `project-iam` を apply し直す。

### 実施記録

| 日付 | 結果 |
| --- | --- |
| 2026-11-17 | 破棄 18件(25秒)、再作成 18件(44秒)。再作成後の plan は差分なし。API と画面の URL は 200。`project-iam` を人が再 apply し、`bigquery.jobUser` が新しいサービスアカウントに付いたことを確認。A7 達成 |

## Terraform が管理しないもの

- Cloud Run のイメージと環境変数: Cloud Build がデプロイ時に設定する
- 許可リスト(`ALLOWED_EMAILS`): メールアドレスを含むため、リポジトリに書かない
- Firebase Authentication の Google ログイン設定: 後続のPRで扱う
- 予算アラートと state バケット: P0 で人が作成済み(`docs/p0_setup.md`)
