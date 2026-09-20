import type { Answers, BudgetResult, PurchasePlan, ScoredArea } from "@/types/domain";
import {
  buildRecommendedCondition,
  estimateBuildingAgeYears,
  estimateStationWalkMinutes,
} from "./propertyCondition";

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

function pickCandidates(scoredAreas: ScoredArea[]): ScoredArea[] {
  const valid = scoredAreas.filter((s) => !s.violatesMust);
  const pool = valid.length > 0 ? valid : scoredAreas;
  return pool.slice(0, Math.min(8, pool.length));
}

export function buildPurchasePlans(
  scoredAreas: ScoredArea[],
  answers: Answers,
  budget: BudgetResult
): PurchasePlan[] {
  const candidates = pickCandidates(scoredAreas);
  if (candidates.length === 0) return [];

  const balanceCandidate = candidates[0];

  const commuteCandidate =
    [...candidates].sort((a, b) => b.breakdown.commuteFit - a.breakdown.commuteFit)[0] ??
    balanceCandidate;

  const spaceCandidate =
    [...candidates].sort(
      (a, b) => a.area.priceRange.minManYen - b.area.priceRange.minManYen
    )[0] ?? balanceCandidate;

  const plans: PurchasePlan[] = [];

  // ---- バランスプラン ----
  const balanceCondition = buildRecommendedCondition(balanceCandidate.area, answers, budget);
  plans.push({
    key: "balance",
    title: "バランスプラン",
    area: balanceCondition.areaLabel,
    priceRangeManYen: balanceCondition.priceRangeManYen,
    floorAreaSqm: balanceCondition.floorAreaSqm,
    layout: balanceCondition.layout,
    stationWalkMinutes: balanceCondition.stationWalkMinutes,
    buildingAgeYears: balanceCondition.buildingAgeYears,
    suitableReason: "価格・広さ・駅距離のバランスを重視する方に向いています。総合スコアが最も高いエリアを採用しています。",
    tradeOffPoint: "特定の条件を最優先するプランと比べると、それぞれの項目は「ほどほど」の水準になります。",
  });

  // ---- 通勤・利便性重視プラン ----
  const commuteCondition = buildRecommendedCondition(commuteCandidate.area, answers, budget);
  const commuteWalk = clamp(estimateStationWalkMinutes(answers) - 4, 3, 20);
  const commuteFloorArea = {
    min: Math.round(commuteCondition.floorAreaSqm.min * 0.9),
    max: Math.round(commuteCondition.floorAreaSqm.max * 0.9),
  };
  plans.push({
    key: "commute_priority",
    title: "通勤・利便性重視プラン",
    area: commuteCondition.areaLabel,
    priceRangeManYen: {
      min: Math.round(commuteCondition.priceRangeManYen.min * 1.03),
      max: Math.round(commuteCondition.priceRangeManYen.max * 1.08),
    },
    floorAreaSqm: commuteFloorArea,
    layout: commuteCondition.layout,
    stationWalkMinutes: commuteWalk,
    buildingAgeYears: commuteCondition.buildingAgeYears,
    suitableReason: "駅近・都心アクセスを最優先したい方に向いています。通勤時間の希望との適合度が最も高いエリアを採用しています。",
    tradeOffPoint: "駅からの近さを優先する分、専有面積はバランスプランよりやや控えめになる傾向があります。",
  });

  // ---- 広さ・住環境重視プラン ----
  const spaceCondition = buildRecommendedCondition(spaceCandidate.area, answers, budget);
  const spaceWalk = estimateStationWalkMinutes(answers) + 6;
  const spaceFloorArea = {
    min: Math.round(spaceCondition.floorAreaSqm.min * 1.15),
    max: Math.round(spaceCondition.floorAreaSqm.max * 1.2),
  };
  plans.push({
    key: "space_priority",
    title: "広さ・住環境重視プラン",
    area: spaceCondition.areaLabel,
    priceRangeManYen: spaceCondition.priceRangeManYen,
    floorAreaSqm: spaceFloorArea,
    layout: spaceCondition.layout,
    stationWalkMinutes: spaceWalk,
    buildingAgeYears: clamp(
      estimateBuildingAgeYears(answers) + 5,
      0,
      30
    ),
    suitableReason: "駅距離や都心へのアクセスより、広さ・住環境を優先したい方に向いています。相場が抑えめのエリアを採用しています。",
    tradeOffPoint: "駅からの距離がやや遠くなる、または最寄り駅までのアクセス利便性が下がる可能性があります。",
  });

  return plans;
}
