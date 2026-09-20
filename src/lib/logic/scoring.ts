import { TERMINAL_STATIONS } from "@/data/config";
import type {
  Answers,
  Area,
  AreaScoreBreakdown,
  AreaScoreWeights,
  BudgetResult,
  CommuteTarget,
  ScoredArea,
} from "@/types/domain";
import { hasOrWantsChildren, hasPartner } from "@/lib/questions";

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

function normalizeStationName(name: string): string {
  return name.trim().replace(/駅$/u, "");
}

/**
 * ユーザーが入力した通勤先駅から、エリアの代表ターミナルまでの目安時間を求める。
 * V1では実際の経路探索を行わず、入力駅が主要ターミナル駅と一致する場合のみ
 * fixtureの所要時間を採用し、一致しない場合は「未対応駅の概算値」として
 * そのエリアの最短ターミナル時間+15分をフォールバック値に使う。
 * この関数は常にモック/推定値を返すため、呼び出し側で「参考目安」と明示すること。
 */
function estimateMinutesToStation(
  area: Area,
  target: CommuteTarget
): { minutes: number; isEstimate: boolean } {
  const normalized = normalizeStationName(target.stationName);
  const matchedTerminal = TERMINAL_STATIONS.find((t) => t === normalized);
  if (matchedTerminal) {
    return { minutes: area.terminalAccessMinutes[matchedTerminal], isEstimate: false };
  }
  const minKnown = Math.min(...Object.values(area.terminalAccessMinutes));
  return { minutes: minKnown + 15, isEstimate: true };
}

function commuteScoreForTarget(area: Area, target: CommuteTarget): number {
  const { minutes } = estimateMinutesToStation(area, target);
  const ratio = minutes / Math.max(target.maxMinutes, 1);
  if (ratio <= 1) {
    return clamp(100 - ratio * 30, 70, 100);
  }
  const overMinutes = minutes - target.maxMinutes;
  return clamp(70 - overMinutes * 3, 0, 70);
}

function commuteFitScore(area: Area, answers: Answers): number {
  const targets: { target: CommuteTarget; weight: number }[] = [];
  if (answers.commuteSelf) {
    const weight =
      answers.commutePriority === "self" ? 0.7 : answers.commutePriority === "partner" ? 0.3 : 0.5;
    targets.push({ target: answers.commuteSelf, weight });
  }
  if (answers.commutePartner && hasPartner(answers)) {
    const weight =
      answers.commutePriority === "partner" ? 0.7 : answers.commutePriority === "self" ? 0.3 : 0.5;
    targets.push({ target: answers.commutePartner, weight });
  }
  if (targets.length === 0) return 70;
  const totalWeight = targets.reduce((sum, t) => sum + t.weight, 0);
  const weightedScore = targets.reduce(
    (sum, t) => sum + commuteScoreForTarget(area, t.target) * t.weight,
    0
  );
  return weightedScore / totalWeight;
}

function budgetFitScore(area: Area, budget: BudgetResult): number {
  const areaMid = (area.priceRange.minManYen + area.priceRange.maxManYen) / 2;
  const budgetRange = budget.comfortablePurchaseRangeManYen;
  const budgetMid = (budgetRange.min + budgetRange.max) / 2 || 1;

  const overlap =
    Math.min(area.priceRange.maxManYen, budgetRange.max) -
    Math.max(area.priceRange.minManYen, budgetRange.min);
  if (overlap > 0) {
    const diffRatio = Math.abs(areaMid - budgetMid) / budgetMid;
    return clamp(100 - diffRatio * 60, 60, 100);
  }
  const gap =
    area.priceRange.minManYen > budgetRange.max
      ? area.priceRange.minManYen - budgetRange.max
      : budgetRange.min - area.priceRange.maxManYen;
  const gapRatio = gap / budgetMid;
  return clamp(60 - gapRatio * 100, 0, 60);
}

/** 個性的な個人店らしさの簡易プロキシ (大型商業施設の利便性が高いほど個人店色は弱いと仮定) */
function independentShopCharacter(area: Area): number {
  return clamp(6 - area.scores.commercialConvenience, 1, 5);
}

/** 刺激・利便性の簡易プロキシ (都会度と商業利便性の平均) */
function excitementProxy(area: Area): number {
  return clamp(Math.round((area.scores.urbanness + area.scores.commercialConvenience) / 2), 1, 5);
}

function townPreferenceFitScore(area: Area, answers: Answers): number {
  let sliderScore = 75;
  if (answers.townPreferences) {
    const p = answers.townPreferences;
    const diffs = [
      Math.abs(area.scores.quietness - (6 - p.quietVsLively)),
      Math.abs(area.scores.urbanness - p.natureVsUrban),
      Math.abs(area.scores.traditionalVsModern - p.traditionalVsModern),
      Math.abs(independentShopCharacter(area) - p.chainVsIndependent),
      Math.abs(excitementProxy(area) - p.calmVsExciting),
    ];
    const sumDiff = diffs.reduce((a, b) => a + b, 0);
    sliderScore = clamp(100 - (sumDiff / 20) * 100, 0, 100);
  }

  let leisureScore = 75;
  if (answers.leisureActivities && answers.leisureActivities.length > 0) {
    const scores: number[] = [];
    for (const activity of answers.leisureActivities) {
      switch (activity) {
        case "park_nature":
        case "play_with_kids":
          scores.push(area.scores.nature * 20);
          break;
        case "shopping":
        case "cafe_dining":
          scores.push(area.scores.commercialConvenience * 20);
          break;
        case "drinks_with_friends":
        case "hobby_culture":
          scores.push(area.scores.urbanness * 20);
          break;
        case "relax_at_home":
          scores.push(area.scores.quietness * 20);
          break;
        case "drive":
          scores.push(area.scores.carCompatibility * 20);
          break;
        case "sports":
          scores.push((area.scores.nature * 20 + area.scores.commercialConvenience * 20) / 2);
          break;
        default:
          break;
      }
    }
    if (scores.length > 0) {
      leisureScore = scores.reduce((a, b) => a + b, 0) / scores.length;
    }
  }

  return sliderScore * 0.65 + leisureScore * 0.35;
}

function familyChildcareFitScore(area: Area, answers: Answers): number {
  const needsChildcare = hasOrWantsChildren(answers);
  if (!needsChildcare) {
    // 子どもを想定しない場合は、家族人数に応じた広さ確保のしやすさ(戸建適性)を軽く加味する
    const familySize = answers.familyMemberCount ?? 1;
    const spaceBonus = familySize >= 3 ? area.scores.houseFit * 4 : 0;
    return clamp(78 + spaceBonus, 0, 100);
  }

  const priorities = answers.childcarePriorities ?? [];
  if (priorities.length === 0) {
    return area.scores.childcare * 20;
  }

  const weights = [3, 2, 1];
  let weightedSum = 0;
  let weightTotal = 0;
  priorities.slice(0, 3).forEach((priority, index) => {
    const w = weights[index] ?? 1;
    let subScore = area.scores.childcare * 20;
    if (priority === "park") subScore = area.scores.nature * 20;
    if (priority === "home_size") subScore = area.scores.houseFit * 20;
    if (priority === "access_to_parents_home") subScore = 70; // エリア単体では判定不可のため中立値
    weightedSum += subScore * w;
    weightTotal += w;
  });
  return weightTotal > 0 ? weightedSum / weightTotal : area.scores.childcare * 20;
}

function propertyTypeFitScore(area: Area, answers: Answers): number {
  const kind = answers.propertyKind;
  if (!kind || kind === "undecided") return 80;

  const isApartment = kind === "new_apartment" || kind === "used_apartment";
  const isHouse = kind === "new_house" || kind === "used_house" || kind === "land_and_house";

  const supportsKind = area.representativePropertyKinds.includes(kind);
  if (isApartment) {
    return clamp(area.scores.apartmentFit * 18 + (supportsKind ? 10 : 0), 0, 100);
  }
  if (isHouse) {
    return clamp(area.scores.houseFit * 18 + (supportsKind ? 10 : 0), 0, 100);
  }
  return 80;
}

function assetFitScore(area: Area): number {
  return area.scores.assetValue * 20;
}

function carAndOtherFitScore(area: Area, answers: Answers): number {
  switch (answers.carStatus) {
    case "own":
    case "planning":
      return area.scores.carCompatibility * 20;
    case "considering":
      return (area.scores.carCompatibility * 20 + 70) / 2;
    case "not_needed":
      return clamp(55 + area.scores.commercialConvenience * 9, 0, 100);
    default:
      return 75;
  }
}

const BASE_WEIGHTS: AreaScoreWeights = {
  commuteFit: 25,
  budgetFit: 20,
  townPreferenceFit: 15,
  familyChildcareFit: 15,
  propertyTypeFit: 10,
  assetFit: 10,
  carAndOtherFit: 5,
};

export function computeWeights(answers: Answers): AreaScoreWeights {
  const w: AreaScoreWeights = { ...BASE_WEIGHTS };

  if (answers.assetPriority === "asset_value_first") w.assetFit *= 2;
  if (answers.assetPriority === "comfort_first") w.assetFit *= 0.5;

  if (
    answers.futureOwnershipPlan === "sell_10_20_years" ||
    answers.futureOwnershipPlan === "may_rent_out"
  ) {
    w.assetFit *= 1.3;
  }

  if (hasOrWantsChildren(answers) || (answers.childcarePriorities?.length ?? 0) > 0) {
    w.familyChildcareFit *= 1.5;
  }

  if (answers.mustConditions?.includes("commute_time")) w.commuteFit *= 1.3;
  if (answers.mustConditions?.includes("price")) w.budgetFit *= 1.3;
  if (answers.mustConditions?.includes("asset_value")) w.assetFit *= 1.3;
  if (answers.mustConditions?.includes("childcare_environment")) w.familyChildcareFit *= 1.3;

  if (answers.carStatus === "not_needed") w.carAndOtherFit *= 0.5;
  if (answers.carStatus === "own" || answers.carStatus === "planning") w.carAndOtherFit *= 1.4;

  if (!answers.propertyKind || answers.propertyKind === "undecided") {
    w.propertyTypeFit *= 0.6;
  }

  return w;
}

function checkViolatesMust(area: Area, answers: Answers): boolean {
  const musts = answers.mustConditions ?? [];
  if (musts.length === 0) return false;

  if (musts.includes("commute_time") && answers.commuteSelf) {
    const { minutes } = estimateMinutesToStation(area, answers.commuteSelf);
    if (minutes > answers.commuteSelf.maxMinutes * 1.3) return true;
  }
  if (musts.includes("childcare_environment") && area.scores.childcare <= 2) {
    return true;
  }
  if (musts.includes("asset_value") && area.scores.assetValue <= 2) {
    return true;
  }
  if (musts.includes("apartment_or_house") && answers.propertyKind) {
    const isApartment = answers.propertyKind === "new_apartment" || answers.propertyKind === "used_apartment";
    const isHouse =
      answers.propertyKind === "new_house" ||
      answers.propertyKind === "used_house" ||
      answers.propertyKind === "land_and_house";
    if (isApartment && area.scores.apartmentFit <= 2) return true;
    if (isHouse && area.scores.houseFit <= 2) return true;
  }
  return false;
}

function checkViolatesPriceMust(area: Area, answers: Answers, budget: BudgetResult): boolean {
  if (!answers.mustConditions?.includes("price")) return false;
  return area.priceRange.minManYen > budget.comfortablePurchaseRangeManYen.max * 1.25;
}

function buildReasons(
  area: Area,
  answers: Answers,
  breakdown: AreaScoreBreakdown
): string[] {
  const reasons: string[] = [];

  if (breakdown.commuteFit >= 80 && answers.commuteSelf) {
    reasons.push(
      `「${answers.commuteSelf.stationName}まで${answers.commuteSelf.maxMinutes}分以内」の希望に対して通勤時間の目安が良好です。`
    );
  }
  if (breakdown.budgetFit >= 80) {
    reasons.push("算出した購入予算のレンジと、このエリアの価格帯がよく合っています。");
  }
  if (breakdown.townPreferenceFit >= 78 && answers.townPreferences) {
    reasons.push("街の雰囲気の好みが、このエリアの特徴と近い結果になりました。");
  }
  if (breakdown.familyChildcareFit >= 82 && hasOrWantsChildren(answers)) {
    reasons.push("子育て環境に関する回答から、重視したいポイントとの相性が良いと判断しました。");
  }
  if (breakdown.assetFit >= 80 && answers.assetPriority === "asset_value_first") {
    reasons.push("資産性を重視する回答に対して、将来の売却しやすさの参考評価が高めのエリアです。");
  }
  if (breakdown.carAndOtherFit >= 80 && (answers.carStatus === "own" || answers.carStatus === "planning")) {
    reasons.push("車を利用する生活スタイルとの相性が良いエリアです。");
  }
  if (reasons.length === 0) {
    reasons.push(`${area.city}・${area.representativeStation}周辺は、回答いただいた条件全体をバランス良く満たしています。`);
  }
  return reasons.slice(0, 4);
}

export function scoreArea(area: Area, answers: Answers, budget: BudgetResult): ScoredArea {
  const weights = computeWeights(answers);
  const breakdown: AreaScoreBreakdown = {
    commuteFit: commuteFitScore(area, answers),
    budgetFit: budgetFitScore(area, budget),
    townPreferenceFit: townPreferenceFitScore(area, answers),
    familyChildcareFit: familyChildcareFitScore(area, answers),
    propertyTypeFit: propertyTypeFitScore(area, answers),
    assetFit: assetFitScore(area),
    carAndOtherFit: carAndOtherFitScore(area, answers),
  };

  const weightSum = Object.values(weights).reduce((a, b) => a + b, 0);
  const weightedTotal =
    (Object.keys(breakdown) as (keyof AreaScoreBreakdown)[]).reduce(
      (sum, key) => sum + breakdown[key] * weights[key],
      0
    ) / weightSum;

  const violatesMust =
    checkViolatesMust(area, answers) || checkViolatesPriceMust(area, answers, budget);

  const totalScore = violatesMust ? weightedTotal * 0.5 : weightedTotal;

  return {
    area,
    totalScore,
    breakdown,
    weights,
    reasons: buildReasons(area, answers, breakdown),
    violatesMust,
  };
}

export function scoreAllAreas(areas: Area[], answers: Answers, budget: BudgetResult): ScoredArea[] {
  const scored = areas.map((area) => scoreArea(area, answers, budget));
  scored.sort((a, b) => {
    if (a.violatesMust !== b.violatesMust) return a.violatesMust ? 1 : -1;
    return b.totalScore - a.totalScore;
  });
  return scored;
}
