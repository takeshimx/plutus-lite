# Plutus Lite

@AGENTS.md

## Claude Code 固有の運用

規約の本体は上の AGENTS.md。ここには Claude Code の使い方に関する補足だけを書く。

- 並列で作業するときは、git worktree で作業ディレクトリを Issue ごとに分ける。1つの worktree で複数の Issue を扱わない
- 自分が実装したPRを、同じセッションでレビューしない。レビューは別セッションで行う(作成者と検証者を分ける)
- 長い作業を始める前に、対象の受入条件と変更するファイルの一覧を先に示す
- 検証環境のGCPプロジェクト以外を対象にするコマンド(`gcloud`、`bq`、`terraform`)は実行しない
- PRを作ったら、本文の「Areas needing human review」に、High の領域に触れた差分の場所を具体的に書く
