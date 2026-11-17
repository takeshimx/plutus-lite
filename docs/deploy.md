# デプロイの準備と手順(Issue #15)

main にマージされると、Cloud Build が API と画面をビルドし、plutus-lite-dev の Cloud Run にデプロイする(`cloudbuild.yaml`)。

## 担当

| # | 作業 | 担当 | 理由 |
| --- | --- | --- | --- |
| 1 | `infra/` の apply(Cloud Build 用サービスアカウント) | エージェント | G4 で plan を承認後 |
| 2 | Firebase の設定 | 人 | コンソールでしか操作できない |
| 3 | Cloud Build と GitHub の接続 | 人 | GitHub での認証が必要 |
| 4 | `infra/project-iam/` の apply と、許可リストの登録 | 人 | IAM の変更のため。許可リストはメールアドレスを含むため |
| 5 | トリガーの作成 | エージェント | |
| 6 | 初回のデプロイと動作確認 | エージェント → 人 | |

## 2. Firebase の設定(人)

1. https://console.firebase.google.com を開き、「プロジェクトを追加」→「既存の Google Cloud プロジェクトに Firebase を追加」で `plutus-lite-dev` を選ぶ。Google アナリティクスは不要
2. 左のメニュー「Authentication」→「始める」→「Sign-in method」→「Google」を有効にして保存する
3. 「Authentication」→「設定」→「承認済みドメイン」→「ドメインの追加」で、次を追加する
   `plutus-lite-web-e2dwrztzrq-an.a.run.app`
4. 歯車(プロジェクトの設定)→「マイアプリ」→ ウェブ(`</>`)のアイコン → アプリ名 `plutus-lite-web` で登録する。Firebase Hosting は不要

## 3. Cloud Build と GitHub の接続(人)

1. https://console.cloud.google.com/cloud-build/repositories/2nd-gen?project=plutus-lite-dev を開く
2. 「ホスト接続を作成」→ プロバイダ「GitHub」、リージョン `asia-northeast1`、名前 `github` → 接続
3. GitHub の画面で認証し、Cloud Build の GitHub アプリを `takeshimx/plutus-lite` だけにインストールする
4. 戻った画面で「リポジトリをリンク」→ `takeshimx/plutus-lite` を選ぶ

## 4. `infra/project-iam/` の apply と、許可リストの登録(人)

1 が終わってから実行する。Git Bash で:

    cd ~/Desktop/Projects_2026/plutus-lite/infra/project-iam && export TF_DISABLE_PLUGIN_TLS=1 GOOGLE_OAUTH_ACCESS_TOKEN=$(gcloud auth print-access-token) && terraform init -input=false && terraform apply

内容を確かめてから `yes` と入力する。作られるもの:

- Cloud Build 用アカウントの `roles/run.developer`、`roles/logging.logWriter`
- シークレット `plutus-lite-allowed-emails`(保存場所は asia-northeast1 のみ)と、API 用アカウントの読み取り権限

続けて、許可するメールアドレスを登録する(複数ならカンマ区切り):

    printf '%s' 'メールアドレス' | gcloud secrets versions add plutus-lite-allowed-emails --project=plutus-lite-dev --data-file=-

許可リストを変えるときは、このコマンドで新しい版を登録し、API を再デプロイする(Cloud Run は起動時に最新の版を読む)。

## 5. トリガー(エージェントが作成)

トリガーには、`_FIREBASE_API_KEY`(Firebase のウェブアプリの `apiKey`)だけを設定する。秘密情報ではないが、リポジトリには書かない。許可リストはトリガーに書かない。

## Terraform が管理しないもの

- Firebase の設定とトリガー: コンソールまたは gcloud で作成する(上の手順)
- 許可リストの値: Secret Manager に人が登録する
- Cloud Run のイメージと環境変数: Cloud Build がデプロイのたびに設定する
