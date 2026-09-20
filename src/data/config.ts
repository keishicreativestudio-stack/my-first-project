/**
 * 資金計画の計算に使う前提値。
 * 金融機関の正式審査結果ではなく、あくまで参考目安の計算に使う設定値。
 * 一元管理し、後から変更できるようにする。
 */
export const BUDGET_ASSUMPTIONS = {
  /** 住宅ローン金利(年率, %) 変動金利の参考目安 */
  interestRatePercent: 1.5,
  /** 返済期間(年) */
  loanTermYears: 35,
  /** 金融機関の審査で用いられがちな返済負担率の上限目安(%) */
  maxDebtToIncomeRatioPercent: 35,
  /** 「無理のない」返済負担率の目安(%)。上限より保守的に設定。 */
  comfortableDebtToIncomeRatioPercent: 25,
} as const;

/** 主要ターミナル駅の初期候補 (V1)。ユーザー入力駅を優先するための参考リスト。 */
export const TERMINAL_STATIONS = [
  "東京",
  "新宿",
  "渋谷",
  "池袋",
  "品川",
  "上野",
  "横浜",
  "大宮",
  "千葉",
] as const;

/** 対象都道府県 */
export const TARGET_PREFECTURES = ["東京都", "神奈川県", "埼玉県", "千葉県"] as const;
