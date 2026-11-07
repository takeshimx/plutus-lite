# main ブランチの保護設定(関門G3)

人が GitHub の画面で設定する。設定後、完了条件の確認を行い、結果をこのファイルの末尾に記録する。

## 前提

- GitHub Free では、private リポジトリのルールセットとブランチ保護は強制されない
- 決定(2026-11-07): リポジトリを public にする。公開前に、コミットの作者のメールアドレスを GitHub の noreply アドレスに書き換えた。書き換え前のコミットが PR の履歴に残らないよう、リポジトリを作り直した

## 設定(Settings > Rules > Rulesets > New branch ruleset)

| 項目 | 値 |
| --- | --- |
| Ruleset name | main-protection |
| Enforcement status | Active |
| Bypass list | 空(管理者も迂回しない) |
| Target branches | Default branch |
| Restrict deletions | オン |
| Block force pushes | オン |
| Require a pull request before merging | オン |
| Required approvals | 1(下の「承認者の問題」で案Aを採用) |
| Dismiss stale pull request approvals when new commits are pushed | オン |
| Require review from Code Owners | オン |
| Require conversation resolution before merging | オン |
| Require status checks to pass | オン。必須チェックは `ci-ok` のみ |
| Require branches to be up to date before merging | オン |

## 承認者の問題

GitHub では、PRの作成者は自分のPRを承認できない。エージェントが `takeshimx` の権限でPRを作ると、コードオーナーの承認が必須の差分は誰も承認できず、マージできなくなる。

選択肢

| 案 | 内容 | 利点 | 欠点 |
| --- | --- | --- | --- |
| A | エージェントのPRは bot(GitHub App または claude-code-action)名義で作る。承認数 1 | 作成者と承認者が分かれ、手順書の原則どおり | 手元の Claude Code から作るPRにも bot の認証を用意する手間がある |
| B | 承認数 0、コードオーナー承認はオフ。PR経由と必須チェックだけを強制 | 設定が簡単。今すぐ運用できる | 高リスク差分を人が読むことを仕組みで強制できず、運用で守ることになる。CODEOWNERS はレビュー依頼の自動付与にだけ効く |

決定(2026-11-07): 案A。エージェントのPRは bot 名義で作り、人(`takeshimx`)が承認する。

## 完了条件の確認(P3)

- [ ] 空のPRを作り、`ci-ok` が実行されて成功する
- [ ] main への直接 push が拒否される
- [ ] `infra/` などの高リスクパスを変更したPRで、コードオーナーのレビュー依頼が自動で付く
- [ ] CIが失敗するPRがマージできない

## 確認結果

<!-- 日付、確認した人、結果 -->
