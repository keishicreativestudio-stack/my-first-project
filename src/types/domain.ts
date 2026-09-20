/**
 * 住まいコンシェルジュAI - ドメイン型定義
 *
 * 「決定論的な計算」(budget/scoring)と「AIによる提案」(説明文生成)を
 * 分離できるように、回答(Answers)・エリア(Area)・診断結果(DiagnosisResult)
 * を独立した型として定義する。
 */

// ---------- 基本選択肢 ----------

export type FamilyType =
  | "single"
  | "couple"
  | "couple_with_children"
  | "single_parent"
  | "with_parents"
  | "other";

export type FutureFamilyPlan =
  | "same_as_now"
  | "one_child"
  | "two_or_more_children"
  | "living_with_parents"
  | "children_independence"
  | "unknown";

export type AgeBand = "20s" | "30s" | "40s" | "50s" | "60s_plus";

export type OtherLoanType = "none" | "car" | "card" | "education" | "other";

export type MonthlyHousingBudgetOption =
  | "100000"
  | "150000"
  | "200000"
  | "250000"
  | "300000"
  | "350000_plus"
  | "unknown";

export type CommutePriority = "equal" | "self" | "partner";

export type LeisureActivity =
  | "cafe_dining"
  | "shopping"
  | "park_nature"
  | "play_with_kids"
  | "sports"
  | "relax_at_home"
  | "drive"
  | "drinks_with_friends"
  | "hobby_culture";

export type ChildcarePriority =
  | "childcare_facility"
  | "school"
  | "park"
  | "safety"
  | "medical"
  | "shopping"
  | "home_size"
  | "access_to_parents_home";

export type CarStatus = "own" | "planning" | "considering" | "not_needed";

export type PropertyKind =
  | "new_apartment"
  | "used_apartment"
  | "new_house"
  | "used_house"
  | "land_and_house"
  | "undecided";

export type NewOrUsed = "new" | "used" | "either" | "unknown";

export type AssetPriority =
  | "comfort_first"
  | "balance"
  | "asset_value_first";

export type FutureOwnershipPlan =
  | "live_long_term"
  | "sell_10_20_years"
  | "may_rent_out"
  | "may_relocate"
  | "unknown";

export type MustCondition =
  | "price"
  | "commute_time"
  | "station_distance"
  | "floor_area"
  | "layout"
  | "building_age"
  | "town_atmosphere"
  | "childcare_environment"
  | "asset_value"
  | "apartment_or_house"
  | "other";

// ---------- 通勤情報 ----------

export interface CommuteTarget {
  stationName: string;
  maxMinutes: number;
}

// ---------- 街の好みスライダー (1〜5, 内部数値化) ----------

export interface TownPreferenceSliders {
  /** 1: 静かな住宅街 〜 5: 賑やかな街 */
  quietVsLively: number;
  /** 1: 自然が多い 〜 5: 都会的 */
  natureVsUrban: number;
  /** 1: 昔ながら 〜 5: 新しく整備された街 */
  traditionalVsModern: number;
  /** 1: 大型商業施設が便利 〜 5: 個性的な個人店が多い */
  chainVsIndependent: number;
  /** 1: 落ち着き 〜 5: 刺激・利便性 */
  calmVsExciting: number;
}

// ---------- 回答全体 ----------

export interface Answers {
  // Q1
  familyType?: FamilyType;
  familyMemberCount?: number;

  // Q2
  futureFamilyPlan?: FutureFamilyPlan;

  // Q3
  ageBand?: AgeBand;
  exactAge?: number;

  // Q4 世帯年収 (万円)
  incomeSelf?: number;
  incomePartner?: number;

  // Q5 自己資金 (万円)
  ownFunds?: number;
  fundsToKeep?: number;

  // Q6 その他借入
  otherLoanTypes?: OtherLoanType[];
  otherLoanMonthlyPayment?: number;

  // Q7 月々の住宅費
  monthlyHousingBudget?: MonthlyHousingBudgetOption;
  monthlyHousingBudgetCustom?: number;

  // Q8 通勤
  commuteSelf?: CommuteTarget;
  commutePartner?: CommuteTarget;
  commutePriority?: CommutePriority;

  // Q9 休日
  leisureActivities?: LeisureActivity[];

  // Q10 街の好み
  townPreferences?: TownPreferenceSliders;

  // Q11 子育て(条件付き)
  childcarePriorities?: ChildcarePriority[];

  // Q12 車
  carStatus?: CarStatus;

  // Q13 住宅タイプ
  propertyKind?: PropertyKind;
  newOrUsed?: NewOrUsed;

  // Q14 資産性
  assetPriority?: AssetPriority;

  // Q15 将来
  futureOwnershipPlan?: FutureOwnershipPlan;

  // Q16 絶対条件 (最大3つ)
  mustConditions?: MustCondition[];
}

// ---------- エリアデータ (fixture / mock) ----------

export type Prefecture = "東京都" | "神奈川県" | "埼玉県" | "千葉県";

export interface AreaScores {
  /** 静かさ 1(賑やか)〜5(静か) ※スライダーと軸を合わせるため逆向きに注意 */
  quietness: number;
  /** 都会度 1(自然)〜5(都会的) */
  urbanness: number;
  /** 自然の豊かさ 1〜5 */
  nature: number;
  /** 街並み 1(昔ながら)〜5(新しく整備された街) */
  traditionalVsModern: number;
  /** 商業利便性 1〜5 */
  commercialConvenience: number;
  /** 子育てのしやすさ 1〜5 */
  childcare: number;
  /** 車との相性 1〜5 */
  carCompatibility: number;
  /** 資産性参考指標 1〜5 (mock) */
  assetValue: number;
  /** マンション向き度 1〜5 */
  apartmentFit: number;
  /** 戸建向き度 1〜5 */
  houseFit: number;
}

export interface AreaPriceRange {
  /** 万円単位のおおよその価格帯 (中古マンション70㎡換算の目安) */
  minManYen: number;
  maxManYen: number;
}

export interface Area {
  id: string;
  prefecture: Prefecture;
  city: string;
  representativeStation: string;
  lines: string[];
  /** 主要ターミナル駅ごとの所要時間目安(分)。V1ではmock値。 */
  terminalAccessMinutes: Record<string, number>;
  priceRange: AreaPriceRange;
  scores: AreaScores;
  representativePropertyKinds: PropertyKind[];
  notes: string;
  /** V1のスコアはfixtureであることを明示するフラグ */
  isMockData: true;
}

// ---------- 診断ロジック出力 ----------

export interface BudgetCalculationAssumptions {
  interestRatePercent: number;
  loanTermYears: number;
  maxDebtToIncomeRatioPercent: number;
  comfortableDebtToIncomeRatioPercent: number;
}

export interface BudgetResult {
  /** 借入可能額の参考目安 (万円) */
  maxLoanAmountManYen: number;
  /** 無理のない購入予算レンジ (万円) */
  comfortablePurchaseRangeManYen: { min: number; max: number };
  /** 毎月返済参考額 (万円) */
  monthlyRepaymentManYen: number;
  /** 自己資金のうち購入に充当できる額 */
  usableOwnFundsManYen: number;
  assumptions: BudgetCalculationAssumptions;
  /** 計算に利用した世帯年収合計 */
  totalHouseholdIncomeManYen: number;
}

export interface AreaScoreBreakdown {
  commuteFit: number;
  budgetFit: number;
  townPreferenceFit: number;
  familyChildcareFit: number;
  propertyTypeFit: number;
  assetFit: number;
  carAndOtherFit: number;
}

export interface AreaScoreWeights {
  commuteFit: number;
  budgetFit: number;
  townPreferenceFit: number;
  familyChildcareFit: number;
  propertyTypeFit: number;
  assetFit: number;
  carAndOtherFit: number;
}

export interface ScoredArea {
  area: Area;
  totalScore: number;
  breakdown: AreaScoreBreakdown;
  weights: AreaScoreWeights;
  reasons: string[];
  violatesMust: boolean;
}

export interface RecommendedPropertyCondition {
  areaLabel: string;
  priceRangeManYen: { min: number; max: number };
  propertyKind: PropertyKind;
  floorAreaSqm: { min: number; max: number };
  layout: string;
  stationWalkMinutes: number;
  buildingAgeYears: number;
  reason: string;
}

export interface RelaxationSuggestion {
  conditionLabel: string;
  originalValue: string;
  suggestedValue: string;
  explanation: string;
  /** true の場合、ユーザーのMust条件を変更する「もしここだけ緩められるなら」案 */
  isMustOverride: boolean;
}

export type PlanKey = "balance" | "commute_priority" | "space_priority";

export interface PurchasePlan {
  key: PlanKey;
  title: string;
  area: string;
  priceRangeManYen: { min: number; max: number };
  floorAreaSqm: { min: number; max: number };
  layout: string;
  stationWalkMinutes: number;
  buildingAgeYears: number;
  suitableReason: string;
  tradeOffPoint: string;
}

export interface BuyerProfile {
  title: string;
  description: string;
}

export interface DiagnosisResult {
  buyerProfile: BuyerProfile;
  budget: BudgetResult;
  topAreas: ScoredArea[];
  recommendedCondition: RecommendedPropertyCondition;
  relaxationSuggestions: RelaxationSuggestion[];
  plans: PurchasePlan[];
  mustConditions: MustCondition[];
  wantConditions: MustCondition[];
  generatedAt: string;
}

// ---------- 問い合わせ ----------

export type ContactMethod = "phone" | "email" | "either";
export type ContactTimeSlot =
  | "morning"
  | "daytime"
  | "evening"
  | "night"
  | "anytime";

export interface ContactFormInput {
  name: string;
  phone: string;
  email: string;
  preferredContactMethod: ContactMethod;
  preferredContactTime: ContactTimeSlot;
  freeText?: string;
}

export interface ContactSubmission {
  id: string;
  submittedAt: string;
  contact: ContactFormInput;
  answers: Answers;
  result: DiagnosisResult;
}
