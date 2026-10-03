// REDS 仲介手数料計算（消費税10%）の再現
// 元: https://www.reds.co.jp/calc10_2/ （page-calc-common.js の calc_brokerage_fee）
(function (root) {
  const TAX_RATE = 1.1;

  // 物件価格 1,000万円以上 5,000万円未満の価格帯（下限以上・上限未満）
  // rate: REDS料率(%)、limit: 税込上限額(円)
  const BANDS = [
    { max: 12500000, rate: '2.7', limit: 393930 },
    { max: 15000000, rate: '2.625', limit: 453740 },
    { max: 17500000, rate: '2.55', limit: 509430 },
    { max: 20000000, rate: '2.475', limit: 560990 },
    { max: 22500000, rate: '2.4', limit: 608430 },
    { max: 25000000, rate: '2.325', limit: 651740 },
    { max: 27500000, rate: '2.25', limit: 690930 },
    { max: 30000000, rate: '2.175', limit: 725990 },
    { max: 32500000, rate: '2.1', limit: 756930 },
    { max: 35000000, rate: '2.025', limit: 783740 },
    { max: 37500000, rate: '1.95', limit: 806430 },
    { max: 40000000, rate: '1.875', limit: 824990 },
    { max: 42500000, rate: '1.8', limit: 839430 },
    { max: 45000000, rate: '1.725', limit: 849740 },
    { max: 47500000, rate: '1.65', limit: 855930 },
    { max: 50000000, rate: '1.575', limit: 857990 },
  ];
  // 元コードと同じ浮動小数点演算になるよう、料率は小数で保持する
  const BAND_MULTIPLIER = {
    '2.7': 0.027, '2.625': 0.02625, '2.55': 0.0255, '2.475': 0.02475,
    '2.4': 0.024, '2.325': 0.02325, '2.25': 0.0225, '2.175': 0.02175,
    '2.1': 0.021, '2.025': 0.02025, '1.95': 0.0195, '1.875': 0.01875,
    '1.8': 0.018, '1.725': 0.01725, '1.65': 0.0165, '1.575': 0.01575,
  };

  // 税込上限に張り付いたときの実効料率（%、小数3桁切り捨て）
  const calcRateOverLimit = (fee, price) => {
    const rate = (1.0 * fee - 30000) / price;
    return Math.floor(rate * 100000) / 1000;
  };

  // 法定上限（税抜）: 200万以下5%、400万以下 4%+2万相当、それ超 3%+6万
  const calcLegalFee = (price) => {
    if (price <= 2000000) return Math.floor(price * 0.05);
    if (price <= 4000000) return Math.floor(100000 + (price - 2000000) * 0.04);
    return Math.floor(price * 0.03 + 60000);
  };

  /**
   * @param {object} p
   * @param {number} p.price 物件価格（円）
   * @param {'購入'|'売却'} p.kind 査定種別
   * @param {'あり'|'なし'} p.feeLimit 上限設定（売却・1億円超のみ有効）
   */
  const calcBrokerageFee = ({ price = 0, kind = '購入', feeLimit = 'あり' } = {}) => {
    const legalFee = calcLegalFee(price);
    let fee, feeAndTax;
    let rate = '3';
    let limit = 329990;
    let limitStr = '';

    const applyLimit = () => {
      if (feeAndTax > limit) {
        feeAndTax = limit;
        fee = Math.ceil(limit / TAX_RATE);
        rate = calcRateOverLimit(fee, price);
        limitStr = limit.toLocaleString() + '円';
      }
    };

    if (price <= 2000000) {
      fee = Math.floor(price * 0.05 - 30000);
      feeAndTax = Math.floor(fee * TAX_RATE);
    } else if (price <= 4000000) {
      fee = Math.floor(price * 0.04 - 10000);
      feeAndTax = Math.floor(fee * TAX_RATE);
    } else if (price < 10000000) {
      fee = legalFee - 30000;
      feeAndTax = Math.floor(fee * TAX_RATE);
      applyLimit();
    } else if (price < 50000000) {
      const band = BANDS.find((b) => price < b.max);
      limit = band.limit;
      rate = band.rate;
      fee = Math.floor(price * BAND_MULTIPLIER[band.rate] + 30000);
      feeAndTax = Math.floor(fee * TAX_RATE);
      applyLimit();
    } else {
      rate = '1.5';
      if (price > 100000000 && kind === '売却' && feeLimit === 'あり') {
        feeAndTax = 1683000;
        fee = Math.ceil(feeAndTax / TAX_RATE);
      } else {
        fee = Math.floor(price * 0.015 + 30000);
        feeAndTax = Math.floor(fee * TAX_RATE);
      }
    }

    const tax = feeAndTax - fee;
    const legalFeeAndTax = Math.floor(legalFee * TAX_RATE);
    const diffOfFee = legalFeeAndTax - feeAndTax;
    const discountRate = Math.floor((1.0 * diffOfFee / legalFeeAndTax) * 100 * 10) / 10;

    return { fee, feeAndTax, tax, legalFeeAndTax, diffOfFee, rate, limitStr, discountRate };
  };

  const api = { TAX_RATE, calcBrokerageFee, calcLegalFee, calcRateOverLimit };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.RedsCalc = api;
})(this);
