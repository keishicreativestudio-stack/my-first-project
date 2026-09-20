import { AREAS } from "@/data/areas";
import { MUST_CONDITION_OPTIONS } from "@/lib/questions";
import type { Answers, DiagnosisResult } from "@/types/domain";
import { calculateBudget } from "./budget";
import { scoreAllAreas } from "./scoring";
import { buildRecommendedCondition } from "./propertyCondition";
import { buildRelaxationSuggestions } from "./relaxation";
import { buildPurchasePlans } from "./plans";
import { buildBuyerProfile } from "./buyerProfile";

/**
 * 診断のオーケストレーター。
 *
 * 「決定論的な計算」(予算計算・エリアスコアリング)と
 * 「説明文などの提案生成」を分離しつつ、ここで1つの結果にまとめる。
 * V1ではすべてローカルのルールベースで完結するため、LLM APIが未設定でも動作する。
 */
export function runDiagnosis(answers: Answers): DiagnosisResult {
  const budget = calculateBudget(answers);
  const scoredAreas = scoreAllAreas(AREAS, answers, budget);
  const topAreas = scoredAreas.slice(0, 5);

  const bestArea = topAreas[0];
  const recommendedCondition = buildRecommendedCondition(bestArea.area, answers, budget);
  const relaxationSuggestions = buildRelaxationSuggestions(
    answers,
    recommendedCondition,
    scoredAreas,
    budget
  );
  const plans = buildPurchasePlans(scoredAreas, answers, budget);
  const buyerProfile = buildBuyerProfile(answers);

  const mustConditions = answers.mustConditions ?? [];
  const wantConditions = MUST_CONDITION_OPTIONS.map((o) => o.value).filter(
    (v) => !mustConditions.includes(v)
  );

  return {
    buyerProfile,
    budget,
    topAreas,
    recommendedCondition,
    relaxationSuggestions,
    plans,
    mustConditions,
    wantConditions,
    generatedAt: new Date().toISOString(),
  };
}
