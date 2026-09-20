import type {
  Answers,
  Area,
  BudgetResult,
  PropertyKind,
  RecommendedPropertyCondition,
} from "@/types/domain";

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

function effectivePersonCount(answers: Answers): number {
  const defaults: Record<string, number> = {
    single: 1,
    couple: 2,
    couple_with_children: 3,
    single_parent: 2,
    with_parents: 4,
    other: 2,
  };
  let persons = answers.familyMemberCount ?? defaults[answers.familyType ?? "other"] ?? 2;

  if (answers.futureFamilyPlan === "one_child" && persons < 3) persons = 3;
  if (answers.futureFamilyPlan === "two_or_more_children" && persons < 4) persons = 4;
  if (answers.futureFamilyPlan === "living_with_parents") persons += 1;

  return clamp(persons, 1, 6);
}

function floorAreaRangeForPersons(persons: number): { min: number; max: number } {
  const min = clamp(20 + persons * 13, 25, 110);
  const max = clamp(min + 18, 30, 130);
  return { min, max };
}

function layoutForPersons(persons: number): string {
  if (persons <= 1) return "1K〜1LDK";
  if (persons === 2) return "1LDK〜2LDK";
  if (persons === 3) return "2LDK〜3LDK";
  if (persons === 4) return "3LDK";
  return "3LDK〜4LDK";
}

export function estimateStationWalkMinutes(answers: Answers): number {
  let walk = 10;
  if (answers.carStatus === "own" || answers.carStatus === "planning") walk += 3;
  if (answers.assetPriority === "asset_value_first") walk -= 2;
  if (answers.mustConditions?.includes("station_distance")) walk = Math.min(walk, 7);
  return clamp(walk, 3, 20);
}

export function estimateBuildingAgeYears(answers: Answers): number {
  let age = 20;
  if (answers.newOrUsed === "new") age = 0;
  if (answers.assetPriority === "asset_value_first") age = Math.min(age, 15);
  if (answers.mustConditions?.includes("building_age")) age = Math.min(age, 10);
  return clamp(age, 0, 30);
}

export function resolvePropertyKind(area: Area, answers: Answers): PropertyKind {
  if (answers.propertyKind && answers.propertyKind !== "undecided") {
    return answers.propertyKind;
  }
  return area.representativePropertyKinds[0] ?? "used_apartment";
}

export function priceRangeForArea(
  area: Area,
  budget: BudgetResult
): { min: number; max: number } {
  const budgetRange = budget.comfortablePurchaseRangeManYen;
  const min = Math.max(area.priceRange.minManYen, budgetRange.min);
  const max = Math.min(area.priceRange.maxManYen, budgetRange.max);
  if (min <= max) return { min: Math.round(min), max: Math.round(max) };

  // 予算とエリア相場が重ならない場合は、エリア相場を基準にしつつ予算上限で頭打ちにする
  const fallbackMax = Math.max(area.priceRange.minManYen, budgetRange.max);
  return { min: Math.round(area.priceRange.minManYen), max: Math.round(fallbackMax) };
}

export function buildRecommendedCondition(
  area: Area,
  answers: Answers,
  budget: BudgetResult
): RecommendedPropertyCondition {
  const persons = effectivePersonCount(answers);
  const floorArea = floorAreaRangeForPersons(persons);
  const layout = layoutForPersons(persons);
  const stationWalkMinutes = estimateStationWalkMinutes(answers);
  const buildingAgeYears = estimateBuildingAgeYears(answers);
  const propertyKind = resolvePropertyKind(area, answers);
  const priceRangeManYen = priceRangeForArea(area, budget);

  const reasonParts: string[] = [];
  reasonParts.push(
    `世帯構成(${persons}人目安)と将来の家族計画から、専有面積の目安を${floorArea.min}〜${floorArea.max}㎡としています。`
  );
  reasonParts.push(
    `算出した購入予算(${budget.comfortablePurchaseRangeManYen.min}〜${budget.comfortablePurchaseRangeManYen.max}万円)と${area.representativeStation}エリアの相場から価格帯を設定しました。`
  );
  if (answers.mustConditions?.includes("station_distance")) {
    reasonParts.push("駅徒歩を譲れない条件として選択されたため、駅近の物件を優先しています。");
  }
  if (answers.carStatus === "own" || answers.carStatus === "planning") {
    reasonParts.push("車を利用する前提のため、駅距離よりも駐車場確保のしやすさを優先しています。");
  }

  return {
    areaLabel: `${area.city}・${area.representativeStation}周辺`,
    priceRangeManYen,
    propertyKind,
    floorAreaSqm: floorArea,
    layout,
    stationWalkMinutes,
    buildingAgeYears,
    reason: reasonParts.join(""),
  };
}

export { effectivePersonCount, floorAreaRangeForPersons, layoutForPersons };
