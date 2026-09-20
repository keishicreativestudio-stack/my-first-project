import type {
  Answers,
  AssetPriority,
  CarStatus,
  ChildcarePriority,
  FamilyType,
  FutureFamilyPlan,
  FutureOwnershipPlan,
  LeisureActivity,
  MonthlyHousingBudgetOption,
  MustCondition,
  NewOrUsed,
  OtherLoanType,
  PropertyKind,
} from "@/types/domain";

export type StepId =
  | "family_type"
  | "future_family"
  | "age"
  | "income"
  | "funds"
  | "other_loans"
  | "monthly_budget"
  | "commute"
  | "leisure"
  | "town_preference"
  | "childcare"
  | "car"
  | "property_kind"
  | "asset_priority"
  | "future_ownership"
  | "must_conditions";

export interface SelectOption<T extends string> {
  value: T;
  label: string;
  description?: string;
}

export interface StepDefinition {
  id: StepId;
  title: string;
  subtitle?: string;
  isVisible: (answers: Answers) => boolean;
}

/** 子どもがいる、または将来子どもを考えているか */
export function hasOrWantsChildren(answers: Answers): boolean {
  if (
    answers.familyType === "couple_with_children" ||
    answers.familyType === "single_parent"
  ) {
    return true;
  }
  if (
    answers.futureFamilyPlan === "one_child" ||
    answers.futureFamilyPlan === "two_or_more_children"
  ) {
    return true;
  }
  return false;
}

/** 配偶者・パートナーがいるか (通勤・年収を2人分聞くかどうかの判定に使用) */
export function hasPartner(answers: Answers): boolean {
  return (
    answers.familyType === "couple" || answers.familyType === "couple_with_children"
  );
}

export const STEPS: StepDefinition[] = [
  {
    id: "family_type",
    title: "この家には、どなたと住む予定ですか？",
    isVisible: () => true,
  },
  {
    id: "future_family",
    title: "5〜10年後の暮らしについて、一番近いものを教えてください。",
    subtitle: "将来必要になりそうな広さ・間取りの参考にします。",
    isVisible: () => true,
  },
  {
    id: "age",
    title: "年代を教えてください。",
    subtitle: "住宅ローンの返済期間の目安に利用します。",
    isVisible: () => true,
  },
  {
    id: "income",
    title: "世帯年収を教えてください。",
    subtitle: "購入可能な予算の参考目安を計算します。",
    isVisible: () => true,
  },
  {
    id: "funds",
    title: "住宅購入に使える自己資金を教えてください。",
    subtitle: "購入後も手元に残しておきたい金額もあわせてお聞きします。",
    isVisible: () => true,
  },
  {
    id: "other_loans",
    title: "現在、住宅ローン以外の借入はありますか？",
    isVisible: () => true,
  },
  {
    id: "monthly_budget",
    title: "毎月の住宅費は、いくらくらいまでなら無理なく支払えそうですか？",
    subtitle: "分からない場合は「分からない」を選んで大丈夫です。",
    isVisible: () => true,
  },
  {
    id: "commute",
    title: "通勤先や希望の通勤時間を教えてください。",
    subtitle: "モックの目安時間です。実際の所要時間は今後より正確に対応予定です。",
    isVisible: () => true,
  },
  {
    id: "leisure",
    title: "休日はどのように過ごすことが多いですか？",
    subtitle: "あてはまるものをいくつでも選んでください。",
    isVisible: () => true,
  },
  {
    id: "town_preference",
    title: "理想の街の雰囲気を教えてください。",
    subtitle: "スライダーを動かして、あなたの好みに近い位置に合わせてください。",
    isVisible: () => true,
  },
  {
    id: "childcare",
    title: "子育てで特に重視したいものを選んでください。",
    subtitle: "重要だと思う順に、最大3つまで選んでください。",
    isVisible: hasOrWantsChildren,
  },
  {
    id: "car",
    title: "車についてお聞かせください。",
    isVisible: () => true,
  },
  {
    id: "property_kind",
    title: "現在イメージしている住宅タイプはありますか？",
    isVisible: () => true,
  },
  {
    id: "asset_priority",
    title: "住み心地と将来の資産性、どちらを重視しますか？",
    subtitle: "将来の売却しやすさを考慮したエリア選びに反映します。",
    isVisible: () => true,
  },
  {
    id: "future_ownership",
    title: "購入した住宅を将来どうする可能性がありますか？",
    isVisible: () => true,
  },
  {
    id: "must_conditions",
    title: "家選びで、どうしても譲れないものを教えてください。",
    subtitle: "最大3つまで選べます。それ以外は「できれば叶えたい条件」として扱います。",
    isVisible: () => true,
  },
];

export function getVisibleSteps(answers: Answers): StepDefinition[] {
  return STEPS.filter((s) => s.isVisible(answers));
}

// ---------- 選択肢定義 ----------

export const FAMILY_TYPE_OPTIONS: SelectOption<FamilyType>[] = [
  { value: "single", label: "一人" },
  { value: "couple", label: "夫婦・パートナー" },
  { value: "couple_with_children", label: "夫婦・パートナー＋子ども" },
  { value: "single_parent", label: "ひとり親＋子ども" },
  { value: "with_parents", label: "親との同居" },
  { value: "other", label: "その他" },
];

export const FUTURE_FAMILY_OPTIONS: SelectOption<FutureFamilyPlan>[] = [
  { value: "same_as_now", label: "今と大きく変わらない予定" },
  { value: "one_child", label: "子ども1人を考えている" },
  { value: "two_or_more_children", label: "子ども2人以上を考えている" },
  { value: "living_with_parents", label: "親との同居の可能性がある" },
  { value: "children_independence", label: "子どもの独立を想定している" },
  { value: "unknown", label: "まだ分からない" },
];

export const AGE_BAND_OPTIONS = [
  { value: "20s", label: "20代" },
  { value: "30s", label: "30代" },
  { value: "40s", label: "40代" },
  { value: "50s", label: "50代" },
  { value: "60s_plus", label: "60代以上" },
] as const;

export const OTHER_LOAN_OPTIONS: SelectOption<OtherLoanType>[] = [
  { value: "none", label: "なし" },
  { value: "car", label: "車のローン" },
  { value: "card", label: "カードローン" },
  { value: "education", label: "教育ローン" },
  { value: "other", label: "その他" },
];

export const MONTHLY_BUDGET_OPTIONS: SelectOption<MonthlyHousingBudgetOption>[] = [
  { value: "100000", label: "10万円" },
  { value: "150000", label: "15万円" },
  { value: "200000", label: "20万円" },
  { value: "250000", label: "25万円" },
  { value: "300000", label: "30万円" },
  { value: "350000_plus", label: "35万円以上" },
  { value: "unknown", label: "分からない" },
];

export const LEISURE_OPTIONS: SelectOption<LeisureActivity>[] = [
  { value: "cafe_dining", label: "カフェ・外食" },
  { value: "shopping", label: "買い物" },
  { value: "park_nature", label: "公園・自然" },
  { value: "play_with_kids", label: "子どもと遊ぶ" },
  { value: "sports", label: "スポーツ" },
  { value: "relax_at_home", label: "家でゆっくり" },
  { value: "drive", label: "車で出かける" },
  { value: "drinks_with_friends", label: "友人と飲む" },
  { value: "hobby_culture", label: "趣味・カルチャー" },
];

export const CHILDCARE_OPTIONS: SelectOption<ChildcarePriority>[] = [
  { value: "childcare_facility", label: "保育環境" },
  { value: "school", label: "学校" },
  { value: "park", label: "公園" },
  { value: "safety", label: "治安" },
  { value: "medical", label: "医療" },
  { value: "shopping", label: "買い物" },
  { value: "home_size", label: "家の広さ" },
  { value: "access_to_parents_home", label: "実家へのアクセス" },
];

export const CAR_STATUS_OPTIONS: SelectOption<CarStatus>[] = [
  { value: "own", label: "現在所有している" },
  { value: "planning", label: "購入予定" },
  { value: "considering", label: "将来検討している" },
  { value: "not_needed", label: "必要ない" },
];

export const PROPERTY_KIND_OPTIONS: SelectOption<PropertyKind>[] = [
  { value: "new_apartment", label: "新築マンション" },
  { value: "used_apartment", label: "中古マンション" },
  { value: "new_house", label: "新築戸建" },
  { value: "used_house", label: "中古戸建" },
  { value: "land_and_house", label: "土地から探して注文住宅" },
  { value: "undecided", label: "分からないので提案してほしい" },
];

export const NEW_OR_USED_OPTIONS: SelectOption<NewOrUsed>[] = [
  { value: "new", label: "新築" },
  { value: "used", label: "中古" },
  { value: "either", label: "どちらでもいい" },
  { value: "unknown", label: "分からない" },
];

export const ASSET_PRIORITY_OPTIONS: SelectOption<AssetPriority>[] = [
  { value: "comfort_first", label: "住み心地を最優先" },
  { value: "balance", label: "バランス" },
  { value: "asset_value_first", label: "資産性を重視" },
];

export const FUTURE_OWNERSHIP_OPTIONS: SelectOption<FutureOwnershipPlan>[] = [
  { value: "live_long_term", label: "長く住み続けたい" },
  { value: "sell_10_20_years", label: "10〜20年程度で売却する可能性がある" },
  { value: "may_rent_out", label: "将来貸す可能性がある" },
  { value: "may_relocate", label: "住み替えを考えている" },
  { value: "unknown", label: "まだ分からない" },
];

export const MUST_CONDITION_OPTIONS: SelectOption<MustCondition>[] = [
  { value: "price", label: "価格" },
  { value: "commute_time", label: "通勤時間" },
  { value: "station_distance", label: "駅徒歩" },
  { value: "floor_area", label: "広さ" },
  { value: "layout", label: "間取り" },
  { value: "building_age", label: "築年数" },
  { value: "town_atmosphere", label: "街の雰囲気" },
  { value: "childcare_environment", label: "子育て環境" },
  { value: "asset_value", label: "資産性" },
  { value: "apartment_or_house", label: "マンション／戸建" },
  { value: "other", label: "その他" },
];
