import type { Answers, BudgetResult, RecommendedPropertyCondition, RelaxationSuggestion, ScoredArea } from "@/types/domain";

/**
 * ユーザーがMustとして指定した条件は勝手に変更しない。
 * Must条件を変更する提案をする場合は「もしここだけ緩められるなら」という
 * 別案(isMustOverride=true)として提示する。
 */
export function buildRelaxationSuggestions(
  answers: Answers,
  recommended: RecommendedPropertyCondition,
  scoredAreas: ScoredArea[],
  budget: BudgetResult
): RelaxationSuggestion[] {
  const musts = answers.mustConditions ?? [];
  const suggestions: RelaxationSuggestion[] = [];

  // 1. 駅徒歩 vs 広さ・価格
  const tightWalk = 5;
  if (recommended.stationWalkMinutes > tightWalk) {
    suggestions.push({
      conditionLabel: "駅徒歩",
      originalValue: `駅徒歩${tightWalk}分以内`,
      suggestedValue: `駅徒歩${recommended.stationWalkMinutes}分以内`,
      explanation: `駅徒歩${tightWalk}分以内に限定すると、予算内では希望の広さ(${recommended.floorAreaSqm.min}〜${recommended.floorAreaSqm.max}㎡)を確保しにくくなる可能性があります。徒歩${recommended.stationWalkMinutes}分程度まで広げることで、価格・広さのバランスが取れる選択肢を探しやすくなります。`,
      isMustOverride: musts.includes("station_distance"),
    });
  }

  // 2. 新築 vs 中古(築年数)
  if (answers.newOrUsed === "new") {
    suggestions.push({
      conditionLabel: "新築／中古",
      originalValue: "新築のみ",
      suggestedValue: `築${recommended.buildingAgeYears}年程度までの中古も含めて検討`,
      explanation: `新築のみに絞ると選択肢が限られ、価格も高くなりやすい傾向があります。築${recommended.buildingAgeYears}年程度までの中古物件も候補に含めることで、同じ予算でも広さやエリアの選択肢が広がる可能性があります。`,
      isMustOverride: musts.includes("building_age"),
    });
  }

  // 3. 通勤時間の希望が厳しく、候補エリアが少ない場合
  if (musts.includes("commute_time") && answers.commuteSelf) {
    const strongCandidates = scoredAreas.filter((s) => !s.violatesMust && s.totalScore >= 65);
    if (strongCandidates.length < 3) {
      const relaxedMinutes = answers.commuteSelf.maxMinutes + 10;
      suggestions.push({
        conditionLabel: "通勤時間",
        originalValue: `${answers.commuteSelf.stationName}まで${answers.commuteSelf.maxMinutes}分以内`,
        suggestedValue: `${answers.commuteSelf.stationName}まで${relaxedMinutes}分以内`,
        explanation: `現在の通勤時間の希望では、条件に合うエリアの選択肢が少なくなっています。${relaxedMinutes}分程度まで広げることで、予算や広さの面でより良い選択肢が見つかりやすくなります。`,
        isMustOverride: true,
      });
    }
  }

  // 4. 価格を最優先しているが、予算とエリア相場の乖離が大きい場合
  if (musts.includes("price")) {
    const topArea = scoredAreas.find((s) => !s.violatesMust);
    if (topArea && topArea.area.priceRange.minManYen > budget.comfortablePurchaseRangeManYen.max) {
      suggestions.push({
        conditionLabel: "価格",
        originalValue: `${budget.comfortablePurchaseRangeManYen.max}万円以内`,
        suggestedValue: `${topArea.area.priceRange.minManYen}万円程度まで`,
        explanation:
          "ご希望のエリアの相場は算出した予算をやや上回っています。自己資金や返済計画を見直すか、専有面積・築年数の条件を調整することで選択肢が広がります。",
        isMustOverride: true,
      });
    }
  }

  return suggestions;
}
