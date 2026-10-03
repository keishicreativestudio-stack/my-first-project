// 実行: node --test reds-calc/test/calc.test.js
// 期待値は元ページ（page-calc-common.js）のロジックで算出した値
const test = require('node:test');
const assert = require('node:assert/strict');
const { calcBrokerageFee } = require('../calc.js');

const cases = [
  // [万円, 種別, 上限設定, 税抜, 税込, 法定上限(税込), 差額, 料率, 上限表示, 割引率]
  [100, '購入', 'あり', 20000, 22000, 55000, 33000, '3', '', 60],
  [300, '購入', 'あり', 110000, 121000, 154000, 33000, '3', '', 21.4],
  [800, '購入', 'あり', 270000, 297000, 330000, 33000, '3', '', 10],
  [1000, '購入', 'あり', 300000, 330000, 396000, 66000, '2.7', '', 16.6],
  [3000, '購入', 'あり', 660000, 726000, 1056000, 330000, '2.1', '', 31.2],
  [4999, '購入', 'あり', 779991, 857990, 1715670, 857680, 1.5, '857,990円', 49.9],
  [5000, '購入', 'あり', 780000, 858000, 1716000, 858000, '1.5', '', 50],
  [20000, '売却', 'あり', 1530000, 1683000, 6666000, 4983000, '1.5', '', 74.7],
  [20000, '売却', 'なし', 3030000, 3333000, 6666000, 3333000, '1.5', '', 50],
  [20000, '購入', 'あり', 3030000, 3333000, 6666000, 3333000, '1.5', '', 50],
];

for (const [man, kind, feeLimit, fee, feeAndTax, legal, diff, rate, limitStr, discount] of cases) {
  test(`${man}万円 ${kind} 上限${feeLimit}`, () => {
    const r = calcBrokerageFee({ price: man * 10000, kind, feeLimit });
    assert.equal(r.fee, fee);
    assert.equal(r.feeAndTax, feeAndTax);
    assert.equal(r.tax, feeAndTax - fee);
    assert.equal(r.legalFeeAndTax, legal);
    assert.equal(r.diffOfFee, diff);
    assert.equal(r.rate, rate);
    assert.equal(r.limitStr, limitStr);
    assert.equal(r.discountRate, discount);
  });
}
