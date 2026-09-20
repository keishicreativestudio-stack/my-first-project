/**
 * 4つの架空ペルソナで診断ロジックを実行し、結果が破綻していないか確認するスクリプト。
 * 実行: npx tsx scripts/test-scenarios.ts
 */
import { runDiagnosis } from "../src/lib/logic/diagnosis";
import type { Answers } from "../src/types/domain";

const caseA: Answers = {
  familyType: "single",
  familyMemberCount: 1,
  futureFamilyPlan: "same_as_now",
  ageBand: "30s",
  incomeSelf: 600,
  ownFunds: 300,
  fundsToKeep: 100,
  otherLoanTypes: ["none"],
  monthlyHousingBudget: "150000",
  commuteSelf: { stationName: "新宿", maxMinutes: 30 },
  commutePriority: "self",
  leisureActivities: ["cafe_dining", "drinks_with_friends", "hobby_culture"],
  townPreferences: {
    quietVsLively: 4,
    natureVsUrban: 5,
    traditionalVsModern: 4,
    chainVsIndependent: 3,
    calmVsExciting: 4,
  },
  carStatus: "not_needed",
  propertyKind: "used_apartment",
  newOrUsed: "either",
  assetPriority: "asset_value_first",
  futureOwnershipPlan: "may_relocate",
  mustConditions: ["commute_time", "asset_value"],
};

const caseB: Answers = {
  familyType: "couple",
  familyMemberCount: 2,
  futureFamilyPlan: "two_or_more_children",
  ageBand: "30s",
  incomeSelf: 650,
  incomePartner: 450,
  ownFunds: 600,
  fundsToKeep: 150,
  otherLoanTypes: ["none"],
  monthlyHousingBudget: "250000",
  commuteSelf: { stationName: "新宿", maxMinutes: 40 },
  commutePartner: { stationName: "東京", maxMinutes: 45 },
  commutePriority: "equal",
  leisureActivities: ["park_nature", "play_with_kids", "relax_at_home"],
  townPreferences: {
    quietVsLively: 2,
    natureVsUrban: 2,
    traditionalVsModern: 3,
    chainVsIndependent: 3,
    calmVsExciting: 2,
  },
  childcarePriorities: ["childcare_facility", "park", "safety"],
  carStatus: "not_needed",
  propertyKind: "undecided",
  newOrUsed: "unknown",
  assetPriority: "balance",
  futureOwnershipPlan: "live_long_term",
  mustConditions: ["childcare_environment", "floor_area"],
};

const caseC: Answers = {
  familyType: "couple_with_children",
  familyMemberCount: 4,
  futureFamilyPlan: "same_as_now",
  ageBand: "40s",
  incomeSelf: 600,
  incomePartner: 300,
  ownFunds: 800,
  fundsToKeep: 200,
  otherLoanTypes: ["car"],
  otherLoanMonthlyPayment: 2,
  monthlyHousingBudget: "250000",
  commuteSelf: { stationName: "東京", maxMinutes: 50 },
  commutePriority: "self",
  leisureActivities: ["drive", "park_nature", "play_with_kids"],
  townPreferences: {
    quietVsLively: 2,
    natureVsUrban: 2,
    traditionalVsModern: 2,
    chainVsIndependent: 2,
    calmVsExciting: 2,
  },
  childcarePriorities: ["home_size", "park", "school"],
  carStatus: "own",
  propertyKind: "used_house",
  newOrUsed: "used",
  assetPriority: "comfort_first",
  futureOwnershipPlan: "live_long_term",
  mustConditions: ["floor_area", "apartment_or_house"],
};

const caseD: Answers = {
  familyType: "couple",
  familyMemberCount: 2,
  futureFamilyPlan: "children_independence",
  ageBand: "50s",
  incomeSelf: 800,
  incomePartner: 200,
  ownFunds: 2500,
  fundsToKeep: 500,
  otherLoanTypes: ["none"],
  monthlyHousingBudget: "unknown",
  commuteSelf: { stationName: "横浜", maxMinutes: 60 },
  commutePriority: "self",
  leisureActivities: ["relax_at_home", "hobby_culture"],
  townPreferences: {
    quietVsLively: 1,
    natureVsUrban: 2,
    traditionalVsModern: 2,
    chainVsIndependent: 4,
    calmVsExciting: 1,
  },
  carStatus: "considering",
  propertyKind: "used_house",
  newOrUsed: "used",
  assetPriority: "asset_value_first",
  futureOwnershipPlan: "sell_10_20_years",
  mustConditions: ["town_atmosphere"],
};

const cases: { name: string; answers: Answers }[] = [
  { name: "ケースA: 30代単身・都会的・資産性重視", answers: caseA },
  { name: "ケースB: 30代夫婦・将来子2人・自然/子育て重視", answers: caseB },
  { name: "ケースC: 40代夫婦+子2人・車あり・広さ/戸建重視", answers: caseC },
  { name: "ケースD: 50代夫婦・自己資金多め・静かな街・売却可能性", answers: caseD },
];

let hasError = false;

for (const c of cases) {
  console.log(`\n===== ${c.name} =====`);
  try {
    const result = runDiagnosis(c.answers);
    console.log("買い手タイプ:", result.buyerProfile.title);
    console.log(
      "予算レンジ(万円):",
      result.budget.comfortablePurchaseRangeManYen.min,
      "〜",
      result.budget.comfortablePurchaseRangeManYen.max,
      " / 借入可能額目安:",
      result.budget.maxLoanAmountManYen
    );
    console.log(
      "上位エリア:",
      result.topAreas
        .map((a) => `${a.area.representativeStation}(${Math.round(a.totalScore)}%)`)
        .join(", ")
    );
    console.log(
      "おすすめ条件:",
      result.recommendedCondition.areaLabel,
      result.recommendedCondition.priceRangeManYen,
      result.recommendedCondition.floorAreaSqm,
      result.recommendedCondition.layout,
      `駅徒歩${result.recommendedCondition.stationWalkMinutes}分`
    );
    console.log(
      "緩和提案件数:",
      result.relaxationSuggestions.length,
      result.relaxationSuggestions.map((r) => r.conditionLabel)
    );
    console.log("プラン数:", result.plans.length);

    // ---- 簡易な妥当性チェック ----
    if (result.topAreas.length !== 5) {
      throw new Error(`上位エリアが5件ではありません: ${result.topAreas.length}`);
    }
    if (result.plans.length !== 3) {
      throw new Error(`プラン数が3件ではありません: ${result.plans.length}`);
    }
    if (result.budget.comfortablePurchaseRangeManYen.min < 0) {
      throw new Error("予算レンジが負値です");
    }
    if (result.budget.comfortablePurchaseRangeManYen.max < result.budget.comfortablePurchaseRangeManYen.min) {
      throw new Error("予算レンジのmaxがminを下回っています");
    }
    if (result.recommendedCondition.floorAreaSqm.min <= 0) {
      throw new Error("推奨面積が不正です");
    }
    console.log("✅ 妥当性チェックOK");
  } catch (e) {
    hasError = true;
    console.error("❌ エラー:", e);
  }
}

if (hasError) {
  console.error("\n一部のケースでエラーが発生しました。");
  process.exit(1);
} else {
  console.log("\n全ケースで診断ロジックが正常に完了しました。");
}
