# P0 準備: GCP の設定手順と確認リスト(関門G0)

この手順は人が実行する。G0 の合格基準は「予算アラートと上限が設定済み。エージェントに渡す権限が検証環境のみ」。

## 前提

| 項目 | 値 |
| --- | --- |
| GCP プロジェクト | `plutus-lite-dev`(plutus-lite 専用の検証環境。新規作成) |
| 予算 | 月500円 |
| 本番環境 | P9 で決める。既存の本番プロジェクトは**使わない** |

経緯(2026-11-11): 当初は既存の本番プロジェクトで手順を進め、エージェント用の権限をプロジェクト全体に付けてしまった。そのため、専用プロジェクトに切り替えた。本番プロジェクトに加えた変更は元に戻した。

## 0. 変数

以降のコマンドはすべて、この変数を使う。**`P` が本番プロジェクトを指していないことを、毎回確かめる。**

請求先アカウントIDと本番プロジェクトIDは、このリポジトリ(public)に書かない。実行するときにだけ、手元で変数に入れる。

    P=plutus-lite-dev
    SA=plutus-lite-agent@$P.iam.gserviceaccount.com
    gcloud billing accounts list          # 表示されたIDを次の行に入れる
    BILLING=<請求先アカウントID>
    PROD_P=<既存の本番プロジェクトID>     # 最後の確認でだけ使う
    echo $P $BILLING $PROD_P

## 1. プロジェクトを作る

    gcloud projects create $P --name="plutus-lite dev"

プロジェクトIDは世界で一意。「already exists」や「in use」と出たら、**既存のプロジェクトを使わず**、別のIDにする(例: `plutus-lite-dev-2611`)。

## 2. 空であることを確かめる

    gcloud storage buckets list --project=$P
    gcloud run services list --project=$P --region=asia-northeast1 2>/dev/null
    gcloud iam service-accounts list --project=$P

新規作成直後なら、バケットと Cloud Run は何も表示されない。サービスアカウントは、GCPが自動で作るものだけが表示される。**自分が作った覚えのないものがあれば止まる。**

## 3. 請求先アカウントの紐付け

    gcloud billing projects link $P --billing-account=$BILLING
    gcloud billing projects describe $P

`billingEnabled: true` であること。

## 4. 予算アラート

    gcloud billing budgets create \
      --billing-account=$BILLING \
      --display-name="plutus-lite-dev monthly" \
      --budget-amount=500JPY \
      --filter-projects=projects/$P \
      --threshold-rule=percent=0.5 \
      --threshold-rule=percent=0.9 \
      --threshold-rule=percent=1.0 \
      --threshold-rule=percent=1.0,basis=forecasted-spend

- 請求先アカウントの通貨が円でない場合は、その通貨で指定する(例: `3USD`)
- **予算アラートは通知するだけで、課金は止まらない**

## 5. API の有効化

新規プロジェクトなので、有効にしても既存のサービスには影響しない。

    gcloud services enable \
      run.googleapis.com \
      bigquery.googleapis.com \
      artifactregistry.googleapis.com \
      cloudbuild.googleapis.com \
      iam.googleapis.com \
      iamcredentials.googleapis.com \
      cloudresourcemanager.googleapis.com \
      serviceusage.googleapis.com \
      identitytoolkit.googleapis.com \
      firebase.googleapis.com \
      --project=$P

## 6. Terraform の state 置き場(GCS バケット)

    gcloud storage buckets create gs://$P-tfstate \
      --project=$P \
      --location=asia-northeast1 \
      --uniform-bucket-level-access \
      --public-access-prevention

**409 エラー(already own it / already exists)が出たら、そこで止まる。** 既存のバケットであり、使ってはいけない。成功したら、バージョン管理を有効にする。

    gcloud storage buckets update gs://$P-tfstate --versioning

## 7. エージェント用のサービスアカウント

鍵ファイルは作らない。あなたの `gcloud` ログインから、このサービスアカウントになりすまして(impersonation)使う。

    gcloud iam service-accounts create plutus-lite-agent \
      --project=$P \
      --display-name="plutus-lite agent (Terraform, dev only)"

    for ROLE in \
      roles/run.admin \
      roles/bigquery.admin \
      roles/artifactregistry.admin \
      roles/iam.serviceAccountAdmin \
      roles/iam.serviceAccountUser \
      roles/serviceusage.serviceUsageAdmin \
      roles/firebaseauth.admin; do
      gcloud projects add-iam-policy-binding $P \
        --member="serviceAccount:$SA" --role="$ROLE" --condition=None
    done

    gcloud storage buckets add-iam-policy-binding gs://$P-tfstate \
      --member="serviceAccount:$SA" --role=roles/storage.objectAdmin

    gcloud iam service-accounts add-iam-policy-binding $SA \
      --project=$P \
      --member="user:$(gcloud config get-value account)" \
      --role=roles/iam.serviceAccountTokenCreator

与えない権限

- `roles/owner`、`roles/editor`: 広すぎる
- `roles/resourcemanager.projectIamAdmin`: エージェントが自分に任意の権限を付けられる。Terraform のうちプロジェクトの IAM を変更する部分は、人の権限で apply する

## 確認

まとめて実行し、出力をエージェントに渡す。出力には請求先アカウントIDは出ない。

    echo "== project";  gcloud projects describe $P --format="value(projectId,lifecycleState)"
    echo "== billing";  gcloud billing projects describe $P --format="value(billingEnabled)"
    echo "== budget";   gcloud billing budgets list --billing-account=$BILLING --format="table(displayName,amount.specifiedAmount)" | grep -i plutus
    echo "== apis";     gcloud services list --enabled --project=$P --format="value(config.name)" | sort
    echo "== bucket";   gcloud storage buckets describe gs://$P-tfstate --format="yaml(location,uniform_bucket_level_access,public_access_prevention,versioning_enabled)"
    echo "== sa roles"; gcloud projects get-iam-policy $P --flatten="bindings[].members" --filter="bindings.members:serviceAccount:$SA" --format="value(bindings.role)"
    echo "== keys (should be empty)"; gcloud iam service-accounts keys list --iam-account=$SA --managed-by=user
    echo "== not in prod (should be empty)"; gcloud projects get-iam-policy $PROD_P --flatten="bindings[].members" --filter="bindings.members:plutus-lite-agent" --format="value(bindings.role)"

## 確認リスト(G0)

- [x] `plutus-lite-dev` が新規作成され、作成時点で空だった
- [x] 請求先アカウントが紐付いている
- [x] 予算アラート(月500円)が `plutus-lite-dev` を対象に作成されている
- [x] 必要な API が有効になっている
- [x] state バケットが新規作成され、バージョン管理と公開防止が有効になっている
- [x] エージェント用サービスアカウントが `plutus-lite-dev` にだけ権限を持つ
- [x] サービスアカウントの鍵ファイルが存在しない
- [x] 本番プロジェクトに plutus-lite 関連の権限が残っていない

## 確認結果

2026-11-11、Takeshi が確認コマンドを実行し、Claude Code が判定した。G0 合格。

- プロジェクト: `plutus-lite-dev` ACTIVE。作成直後のバケットは0件
- 請求: 有効。予算アラート `plutus-lite-dev monthly` 500 JPY
- API: 指定した10件が有効。BigQuery などに付随する API も自動で有効になっている
- state バケット: ASIA-NORTHEAST1、公開防止 enforced、均一アクセス true、バージョン管理 true
- サービスアカウントの権限: 指定した7ロールのみ。owner、editor、projectIamAdmin は無し
- 鍵ファイル: 0件
- 本番プロジェクトの残存権限: 無し

途中の問題: 請求先アカウントに紐付けられるプロジェクト数の上限に達していたため、使っていないプロジェクト1件の請求先の紐付けを外した。作成直後のサービスアカウントは反映に時間がかかり、権限の付与が一度失敗したため、再試行した。
