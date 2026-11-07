# Plutus Lite P2 設計成果物(草案)

Nov 6, 2026 · @Tak

P1の要件定義書(Plutus Lite)を元に、AIが作成した設計の草案。関門G2で人が確認し、承認または差し戻す。

## 1. アーキテクチャ

構成は3層。画面(Next.js)、API(FastAPI)、データ保存(BigQuery)を、Firebase Authentication で認証し、Cloud Run に置く。要件定義書の技術構成に従った案Aを基本とし、保存先の別案を2つ比較する。

| 案 | 保存先 | 長所 | 短所 |
| --- | --- | --- | --- |
| A(要件定義書どおり) | BigQuery | 元のPlutusと同じ構成。集計をSQLで書ける。取引数が少ない間は無料枠に収まる見込み | もともと分析向けで、1件ずつの更新と削除が多い用途には向きにくい |
| B | Firestore | 登録、編集、削除が1件単位で扱いやすい | 月次サマリーの集計を自前で書く。元のPlutusと構成が変わる |
| C | Cloud SQL(PostgreSQL) | 登録も集計もSQLで自然に書ける | インスタンスの稼働に応じた課金がある。運用の手間が増える |

A を採る理由は、このパイロットの目的が元のPlutusと同じ構成での構築手順の検証であることと、取引数が少ないことによる。家計簿の用途だけで選ぶなら、B または C が向く。G2での判断をお願いしたい。

## 2. データモデル案

表は1つだけ。取引(transactions)を1行1件で持つ。月次サマリーは表にせず、取引表から問い合わせのたびに集計する。型は案A(BigQuery)で書く。

| 列名 | 型 | 必須 | 説明 |
| --- | --- | --- | --- |
| transaction\_id | STRING | はい | サーバーが発行する一意のID(UUID) |
| user\_id | STRING | はい | Firebase Authentication のユーザーID。リクエストの認証トークンからサーバーが取り出し、画面からは受け取らない |
| date | DATE | はい | 取引日 |
| type | STRING | はい | income(収入)または expense(支出)の2種類のみ |
| amount\_jpy | INT64 | はい | 円の整数。負の値も許す(A5)。小数は400で拒否 |
| category | STRING | はい | 食費、交通費などの分類。自由入力 |
| note | STRING | いいえ | メモ。最大200文字 |
| created\_at | TIMESTAMP | はい | 登録時刻。サーバーが付ける |

決めたこと

- 他人のデータを返さない(A3)ため、読み書きのSQLはすべて user\_id の条件を必ず付ける。条件はAPIの共通処理に1か所だけ置き、各処理から外せないようにする。
- 許可するアカウント(A1)は、取引表には持たず、環境変数のメールアドレス一覧で管理する。人数が数人のため、表を増やさない。
- 分類(category)は別表にしない。パイロットでは自由入力で足りる。
- 件数が少ないため、パーティションは付けない。クラスタ列だけ user\_id にしておく。

月次サマリーの集計案(A4、A6)

```sql
SELECT
  FORMAT_DATE('%Y-%m', date) AS month,
  SUM(IF(type = 'income', amount_jpy, 0)) AS income_total,
  SUM(IF(type = 'expense', amount_jpy, 0)) AS expense_total
FROM transactions
WHERE user_id = @user_id
GROUP BY month
ORDER BY month DESC
```

案B(Firestore)なら、users/{user\_id}/transactions/{transaction\_id} の形に置き、集計はAPI側のPythonで行う。案C(Cloud SQL)なら、上の列をそのまま通常のテーブルにでき、SQLも同じものが使える。

## 3. API仕様

すべてのエンドポイントは、Authorization ヘッダーにFirebaseのIDトークンを付けて呼ぶ(ヘルスチェックを除く)。サーバーはトークンを検証して user\_id を取り出し、許可リストに無いアカウントは拒否する。

| メソッドとパス | 役割 | 主な応答 | 対応する受入条件 |
| --- | --- | --- | --- |
| GET /healthz | 生存確認(認証なし) | 200 | A7 |
| GET /api/transactions?month=YYYY-MM | 取引の一覧(月で絞る。省略時は全件) | 200, 401, 403 | A1, A2, A3 |
| POST /api/transactions | 取引の登録 | 201, 400, 401, 403 | A2, A5 |
| PUT /api/transactions/{id} | 取引の編集 | 200, 400, 404 | A2, A3, A5 |
| DELETE /api/transactions/{id} | 取引の削除 | 204, 404 | A2, A3 |
| GET /api/summary/monthly | 月次サマリー(収入合計、支出合計) | 200, 401, 403 | A4, A6 |

エラーの扱い

- 401: トークンが無い、または無効
- 403: トークンは有効だが、許可リストに無いアカウント(A1)
- 400: 金額が整数でない、type が income と expense 以外、日付が不正、など(A5)
- 404: 対象のIDが無い。他人のIDを指した場合も404を返し、存在することを漏らさない(A3)

OpenAPIの草案(一部を抓粋)

```yaml
openapi: 3.0.3
info:
  title: Plutus Lite API
  version: 0.1.0
security:
  - bearerAuth: []
paths:
  /api/transactions:
    get:
      summary: List transactions
      parameters:
        - name: month
          in: query
          required: false
          schema: { type: string, pattern: '^\d{4}-\d{2}$' }
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items: { $ref: '#/components/schemas/Transaction' }
        '401': { description: Missing or invalid token }
        '403': { description: Account not allowed }
    post:
      summary: Create a transaction
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: '#/components/schemas/TransactionInput' }
      responses:
        '201': { description: Created }
        '400': { description: Invalid value }
  /api/summary/monthly:
    get:
      summary: Monthly totals for the signed-in user
      responses:
        '200':
          content:
            application/json:
              schema:
                type: array
                items:
                  type: object
                  properties:
                    month: { type: string }
                    income_total: { type: integer }
                    expense_total: { type: integer }
components:
  securitySchemes:
    bearerAuth: { type: http, scheme: bearer }
  schemas:
    TransactionInput:
      type: object
      required: [date, type, amount_jpy, category]
      properties:
        date: { type: string, format: date }
        type: { type: string, enum: [income, expense] }
        amount_jpy: { type: integer }
        category: { type: string }
        note: { type: string, maxLength: 200 }
    Transaction:
      allOf:
        - $ref: '#/components/schemas/TransactionInput'
        - type: object
          properties:
            transaction_id: { type: string }
            created_at: { type: string, format: date-time }
```

PUTとDELETEの定義は、上と同じ形で /api/transactions/{id} に追加する(上の表のとおり)。user\_id はリクエストの中身に含めない。

## 4. コスト見積

利用者が数人、取引が月数百件という規模を想定した見積。単価は2026年時点でGoogleの公式ページと引用元を確認したものと、確認できていないものを分けて示す。実際の請求額は、構築後にGCPの課金レポートで確かめる。

| 項目 | 確認した単価と無料枠 | 想定の使用量 | 月額の見込み |
| --- | --- | --- | --- |
| BigQuery クエリ | 1TiBあたり6.25ドル。毎月1TiBまで無料 | 数百MB以下 | 0ドル(無料枠内) |
| BigQuery 保存 | 最初の10GiBは無料。超えた分は1GiBあたり約0.02ドル | 1GiB未満 | 0ドル(無料枠内) |
| Cloud Run(APIと画面) | 毎月 200万リクエスト、180,000 vCPU秒、360,000 GiB秒まで無料(課金アカウント単位) | 1万リクエスト以下 | 0ドル(無料枠内) |
| Firebase Authentication | 確認できていない(利用者が数人の規模で無料枠に収まると見ているが、未確認) | 数人 | 要確認 |
| Artifact Registry、Cloud Build、Cloud Logging | 確認できていない(いずれも小額で無料枠がある見込み) | デプロイ月数回 | 要確認 |

見立て: データが小さい間は、BigQueryとCloud Runが無料枠に収まる見込みで、月額はほぼ0から数百円にとどまると見ている。これは推定であり、確定した金額ではない。

案C(Cloud SQL)を選ぶ場合は、インスタンスの稼働時間で課金され、無料枠では賄えない。この場合の単価は今回確認していないので、比較する前に調べる。案B(Firestore)も同じく未確認。

注意点

- BigQueryのクエリは、列を絞っても読む量の下限があり、データが小さいときも課金対象量が丸められる。無料枠の中なら影響はないが、設計としてはこの形式の使い方が向いているかは別の問題としてADRで扱う。
- Cloud Runを「リクエストを処理している間だけ課金」の設定にすると、アクセスがない時間帯の課金はありません。ただし最初のアクセスは起動の待ちが出る。
- 予算アラート(例: 月500円で通知)をTerraformで入れ、想定外の課金に気づけるようにする。

## 5. ADR草案

ADRは「なぜそう決めたか」の記録。ここでは、3件を草案として置く。状態はどれも「提案」で、G2で人が「承認」または「却下」に変える。

**ADR-001 データ保存先に何を使うか(**状態: 承認**)**

- 背景: 要件定義書はBigQueryを指定しているが、登録、編集、削除を一件ずつ行う用途であり、分析向けのBigQueryは得意な使い方ではない。
- 選択肢: A BigQuery、B Firestore、C Cloud SQL(1節の表を参照)。
- 提案: A。理由は、元のPlutusと同じ構成で構築手順を練習するというパイロットの目的と、データ量が小さいこと。
- 代償: 更新と削除の頑強さやクエリの最小課金といった弱点を受け入れる。家計簿として本格的に使うなら、BまたはCへの切り替えを再検討する。
- G2での決定: Aを採用。理由はアクセス頻度が低いことと、コスト面。レイテンシーが大きくなる点はトレードオフとして受け入れる。

**ADR-002 認証の方式(状態: **承認**)**

- 背景: 他人のデータを返さないこと(A3)と、許可したアカウントだけが使えること(A1)が受入条件。
- 提案: Firebase Authentication のIDトークンをAPIで検証し、サーバーが取り出した user\_id だけを使う。許可リストは環境変数のメールアドレス一覧。
- 代償: 人数が増えると環境変数での管理は難しくなる。そのときは許可リストを表に移す。

**ADR-003 集計をどこで行うか(状態: **承認**)**

- 背景: 月次サマリーの合計と一覧の合計が一致すること(A4)と、集計を画面で行わないこと(A6)が受入条件。
- 提案: API側で、同じデータと同じ条件(user\_idと月)からSQLで集計する。一覧とサマリーで、同じフィルタの関数を共用する。
- 代償: 取引が増えるとクエリが重くなる可能性があるが、この規模では問題にならないと見ている。

G2でご確認いただく点は、ADR-001の保存先の選択、コスト見積の「未確認」の行をどう扱うかの2点です。
