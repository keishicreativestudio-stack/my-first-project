"""REDS 仲介手数料計算（消費税10%）。reds-calc/calc.js の Python 移植。

元: https://www.reds.co.jp/calc10_2/ （page-calc-common.js の calc_brokerage_fee）
"""
import math

TAX_RATE = 1.1

# (上限価格(未満), 表示料率, 料率, 税込上限額)  … 1,000万円以上5,000万円未満
BANDS = [
    (12500000, '2.7', 0.027, 393930),
    (15000000, '2.625', 0.02625, 453740),
    (17500000, '2.55', 0.0255, 509430),
    (20000000, '2.475', 0.02475, 560990),
    (22500000, '2.4', 0.024, 608430),
    (25000000, '2.325', 0.02325, 651740),
    (27500000, '2.25', 0.0225, 690930),
    (30000000, '2.175', 0.02175, 725990),
    (32500000, '2.1', 0.021, 756930),
    (35000000, '2.025', 0.02025, 783740),
    (37500000, '1.95', 0.0195, 806430),
    (40000000, '1.875', 0.01875, 824990),
    (42500000, '1.8', 0.018, 839430),
    (45000000, '1.725', 0.01725, 849740),
    (47500000, '1.65', 0.0165, 855930),
    (50000000, '1.575', 0.01575, 857990),
]


def legal_fee(price):
    """法定上限（税抜）"""
    if price <= 2000000:
        return math.floor(price * 0.05)
    if price <= 4000000:
        return math.floor(100000 + (price - 2000000) * 0.04)
    return math.floor(price * 0.03 + 60000)


def _rate_over_limit(fee, price):
    rate = (1.0 * fee - 30000) / price
    return math.floor(rate * 100000) / 1000


def reds_fee(price, kind='購入', fee_limit='あり'):
    """REDS 仲介手数料。戻り値は calc.js の calcBrokerageFee と同じ項目の dict。"""
    lf = legal_fee(price)
    rate, limit, limit_str = '3', 329990, ''

    def apply_limit(fee, fee_and_tax, rate):
        if fee_and_tax > limit:
            fee = math.ceil(limit / TAX_RATE)
            return fee, limit, _rate_over_limit(fee, price), f'{limit:,}円'
        return fee, fee_and_tax, rate, ''

    if price <= 2000000:
        fee = math.floor(price * 0.05 - 30000)
        fee_and_tax = math.floor(fee * TAX_RATE)
    elif price <= 4000000:
        fee = math.floor(price * 0.04 - 10000)
        fee_and_tax = math.floor(fee * TAX_RATE)
    elif price < 10000000:
        fee = lf - 30000
        fee_and_tax = math.floor(fee * TAX_RATE)
        fee, fee_and_tax, rate, limit_str = apply_limit(fee, fee_and_tax, rate)
    elif price < 50000000:
        _, rate, mult, limit = next(b for b in BANDS if price < b[0])
        fee = math.floor(price * mult + 30000)
        fee_and_tax = math.floor(fee * TAX_RATE)
        fee, fee_and_tax, rate, limit_str = apply_limit(fee, fee_and_tax, rate)
    else:
        rate = '1.5'
        if price > 100000000 and kind == '売却' and fee_limit == 'あり':
            fee_and_tax = 1683000
            fee = math.ceil(fee_and_tax / TAX_RATE)
        else:
            fee = math.floor(price * 0.015 + 30000)
            fee_and_tax = math.floor(fee * TAX_RATE)

    legal_fee_and_tax = math.floor(lf * TAX_RATE)
    diff = legal_fee_and_tax - fee_and_tax
    return {
        'fee': fee,
        'fee_and_tax': fee_and_tax,
        'tax': fee_and_tax - fee,
        'legal_fee_and_tax': legal_fee_and_tax,
        'diff_of_fee': diff,
        'rate': rate,
        'limit_str': limit_str,
        'discount_rate': math.floor((1.0 * diff / legal_fee_and_tax) * 100 * 10) / 10,
    }
