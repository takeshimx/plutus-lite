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
| Bypass list | Repository admin、モードは For pull requests only(下の「人が作るPRの迂回」を参照) |
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

## 人が作るPRの迂回

コードオーナーは `takeshimx` だけのため、人が自分で作ったPRは、承認できる人がいない。そこで、Repository admin に限って、PR経由でのみルールの迂回を許す。

決定(2026-11-11): 迂回を許す。設定は1つのルールセットのまま。

- 直接 push は、admin も含めて拒否される
- 自分のPRは、マージ画面の「Merge without waiting for requirements to be met (bypass rules)」でマージできる
- bot は Write 権限のため迂回できない。bot のPRは人の承認が必要
- 注意: 迂回はルールセット全体に効くため、承認だけでなく必須チェック `ci-ok` も飛ばせる。**迂回マージは `ci-ok` が成功しているときだけ行う**(運用で守る)。CIも強制したくなったら、CIとレビューを別のルールセットに分け、レビューの方だけ迂回を許す

## 完了条件の確認(P3)

- [x] 空のPRを作り、`ci-ok` が実行されて成功する
- [x] main への直接 push が拒否される
- [x] `infra/` などの高リスクパスを変更したPRで、コードオーナーのレビュー依頼が自動で付く
- [x] CIが失敗するPRがマージできない

## 確認結果

| 日付 | 確認した人 | 条件 | 結果 |
| --- | --- | --- | --- |
| 2026-11-07 | Claude Code | `ci-ok` が成功する | PR #1 で全ジョブ成功 |
| 2026-11-07 | Claude Code | コードオーナーのレビュー依頼 | Dependabot の PR #6(`.github/` を変更)に `takeshimx` のレビュー依頼が自動で付き、承認待ちで BLOCKED |
| 2026-11-11 | Claude Code | 直接 push の拒否 | main への空コミットの push が拒否された(`Changes must be made through a pull request.` `Required status check "ci-ok" is expected.`)。main は変化なし |
| 2026-11-11 | Claude Code | CI失敗時のマージ不可 | PR #7(lockfile の無い `api/pyproject.toml` を追加)で `ci-ok` が失敗。必須チェックが FAILURE で BLOCKED、マージは拒否された。ルールセットの迂回は `current_user_can_bypass: never`。PR #7 はマージせず閉じた |

注: PR #7 はレビュー承認も未取得だったため、BLOCKED の理由は CI 失敗と承認待ちの両方を含む。CI 失敗が必須条件であることは、必須チェック `ci-ok` が FAILURE であることで確認した。
