# 資金計算書（諸費用概算）ジェネレーター

販売図面から読み取った物件情報（JSON）から、資金計算書（概算）の Excel を作ります。
図面の読み取りから送付までの手順は `.claude/skills/shohiyo-gaisan/SKILL.md` を参照。

```bash
pip install openpyxl formulas   # formulas は計算結果をファイルに埋め込むため（スマホのプレビュー用）
python3 shohiyo/make_estimate.py shohiyo/examples/sample_mansion.json 出力.xlsx
```

## JSON の項目

| キー | 必須 | 内容 |
|---|---|---|
| `type` | ○ | `新築戸建` / `中古戸建` / `新築マンション` / `中古マンション` / `土地` |
| `price` | ○ | 物件価格（円） |
| `deal` | | 取引態様 `仲介`（既定）/ `売主` / `代理`。売主・代理は仲介手数料 0 |
| `fee_plan` | | `割引`（既定。REDS calc10_2 で計算）/ `無料` / `半額` |
| `name` `address` `customer` `staff` | | 物件名・所在地・お客様名・担当 |
| `built_year` | | 築年（西暦）。1981年以前は旧耐震の注記を追加 |
| `management_fee` `repair_reserve` | | 管理費・修繕積立金（月額）。マンションの清算金 = 合計 × 2ヶ月 |
| `initial_repair_fund` | | 修繕積立基金（新築マンション） |
| `loan` | | `amount`（既定: 物件価格）、`rate`（既定 0.945）、`years`（既定 35）、`bonus`（既定 0） |
| `overrides` | | `{"登記費用": 480000}` のように概算値を上書き |

## 計算ルール

- 契約書印紙代: 売買価格から（不動産譲渡契約書の軽減税率。2027年3月31日まで）
- 仲介手数料: REDS側は `fee_plan`、他社側は法定上限（税込）。`reds_fee.py` は `reds-calc/calc.js` の移植で、結果が一致することを確認済み
- 事務代行手数料: REDS 0円 / 他社 55,000円
- 融資事務手数料: 融資額 × 2.2%。金消契約印紙: 融資額から
- 登記費用・火災保険・固都税清算・表示登記: 目安額（`make_estimate.py` の `estimate_*`）
- 月々返済: 元利均等（元の Excel と同じ式）
- 青字のセルは入力値。Excel 上で書き換えると再計算されます
