# Plutus Lite

すべてのコーディングエージェント(Claude Code、Codex、Copilot など)が従う規約。関門G3で承認済み(2026-11-07)。

## プロジェクト概要

- 目的: 日々の支出と収入を記録し、月ごと、カテゴリごとの金額を確認する家計簿アプリ。あわせて、新規開発編フライホイールの手順書を検証するパイロットを兼ねる
- 利用者: 本人1名(Googleアカウントのメール許可リストで制限)
- 一次資料(実装の根拠はここに置く。食い違いを見つけたら実装せず質問する)
  - 要件と受入条件 A1〜A7: [docs/requirements.md.md](docs/requirements.md.md)
  - 設計、API仕様、ADR-001〜003: [docs/design.md.md](docs/design.md.md)
  - 開発手順: [docs/flywheel_greenfield.md](docs/flywheel_greenfield.md)

## 技術構成

| 層 | 技術 |
| --- | --- |
| 画面 | Next.js(TypeScript) |
| API | FastAPI(Python 3.12) |
| 保存 | BigQuery(ADR-001) |
| 認証 | Firebase Authentication の IDトークン + メール許可リスト(ADR-002) |
| 実行環境 | Cloud Run |
| IaC | Terraform |
| CI/CD | CI は GitHub Actions、デプロイは Cloud Build |

## リポジトリ構成

    frontend/            Next.js
    api/
      app/auth/          トークン検証と許可リスト            (High)
      app/repository/    BigQuery アクセスと user_id 条件     (High)
      app/routers/       エンドポイント
      app/schemas/       入出力の型と検証
      tests/
    infra/               Terraform                           (High)
    eval/                golden set と評価スクリプト(P5)
    docs/                要件、設計、ADR(docs/adr/)

## 開発コマンド

パッケージ管理は、Python が uv、画面が npm。具体的なスクリプト名はP3の雛形作成時に確定し、ここを更新する。

    # API
    cd api && uv sync
    uv run pytest
    uv run ruff check . && uv run ruff format --check .
    uv run mypy app

    # 画面
    cd frontend && npm ci
    npm test
    npm run lint && npm run typecheck
    npx playwright test              # E2E

    # インフラ(検証環境のみ)
    cd infra && terraform fmt -check && terraform validate
    terraform plan                   # apply は人の承認後

    # 評価ゲート(P5で整備)
    【未定】

## 必ず守る設計上の決まり

次の決まりは受入条件とADRから来ている。破る変更は、テストが通っても受け入れない。

1. **user_id はサーバーが確定する。** 検証済みのIDトークンから取り出した UID だけを使う。リクエストの本文、クエリ、パスから user_id を受け取らない(A3、ADR-002)
2. **すべての読み書きに user_id 条件を付ける。** 条件を付ける処理は `api/app/repository/` の共通処理1か所に置き、各エンドポイントから迂回できないようにする。SQLを直接書くエンドポイントを作らない(A3)
3. **他人の取引は 404 を返す。** 存在を漏らさないため、403 にしない(A3)
4. **認証の応答を区別する。** トークンが無い・無効なら 401、有効だが許可リスト外なら 403(A1)
5. **金額は整数円。** `amount_jpy` は整数で、負数を許す。小数、文字列、範囲外は 400。浮動小数点で金額を扱わない(A5)
6. **集計はAPI側で行う。** 合計と内訳はSQLで計算し、画面は受け取った値を表示するだけにする。画面で再計算しない(A6、ADR-003)
7. **一覧とサマリーで同じ絞り込み関数を使う。** 両者の合計が一致することを保証するため(A4、ADR-003)
8. **SQLはパラメータ化する。** 文字列連結や f-string で値を埋め込まない
9. **秘匿情報をコミットしない。** サービスアカウント鍵、`.env`、トークンはリポジトリに置かない。許可リストは環境変数で渡す

## PRのルール

- 1PRは1つの受入条件、または1つのIssueに対応する。PR本文に対応する受入条件のID(A1〜A7)を書く
- 変更理由と確認方法をPR本文に書く(テンプレート: `.github/pull_request_template.md`)
- テストは実装と同じPRで追加する。テストは実装に合わせて書かず、受入条件から書く
- PR本文にリスク区分(Low / Medium / High)を書く。区分は次の表で決める
- 完了条件: CIと評価ゲートが通過していること
- main への直接pushはしない
- PRをマージしない。マージは人が行う。ルールの迂回(`gh pr merge --admin` など)は使わない
- PR、Issue、ADR は英語で書く。ADR の冒頭の TL;DR だけは英語と日本語を併記する(テンプレート: `docs/adr/0000-template.md`)

| 区分 | このリポジトリでの対象 |
| --- | --- |
| Low | `docs/`、UIの文言、テストのみの追加 |
| Medium | 業務ロジック、画面、依存関係の更新 |
| High | 次節「人の承認が必要な領域」に当たるもの |

## 人の承認が必要な領域

次の領域は変更してよいが、PRのリスク区分を High とし、人が差分を読むまでマージしない。CODEOWNERS で強制する。

- 認証と許可リスト: `api/app/auth/`
- データアクセスと user_id 条件: `api/app/repository/`
- テーブル定義とスキーマ変更
- レート制限の設定
- IaC: `infra/`
- CI/CDとリポジトリ設定: `.github/`、`cloudbuild*.yaml`、`CODEOWNERS`
- この規約自体: `AGENTS.md`、`CLAUDE.md`
- 評価ゲートの合格基準と golden set の正解ラベル: `eval/`

次の操作はエージェントが行わない。

- 本番環境への `terraform apply`、デプロイ、データ変更
- 予算、請求、IAM の権限付与の変更
- 評価ゲートやテストの基準を緩めて通すこと(skip、閾値の変更、テストの削除)

## コーディング規約

- Python: 型ヒントを必須にする。入出力の検証は Pydantic で行う。ruff と mypy の警告を残さない
- TypeScript: `strict` を有効にする。`any` を使わない
- 命名: APIとDBの項目名は snake_case。設計書の列名(`transaction_id`、`amount_jpy` など)をそのまま使う
- エラー処理: 不正な値は書き込まずに処理を止め、エラーを返す。黙って補正しない
- ログ: リクエストIDと UID を記録する。メールアドレス、トークン、取引のメモはログに出さない

## スコープ外

次の機能は作らない。必要に見えても実装せず、Issueで提案する。

投資、資産管理、外貨、按分、予算、AIによるカテゴリ予測、Slack連携、Text2SQL、Gmail取込、照合エージェント、CSV取込、複数ユーザー対応

## 判断に迷ったとき

実装を止めて、Issueにコメントで質問する。特に次の場合は推測で進めない。

- 要件定義書、設計書、この規約の間に食い違いがある
- 受入条件だけでは期待する動作が決まらない
- 「人の承認が必要な領域」に触れないと実装できない
