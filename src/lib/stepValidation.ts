import type { Answers } from "@/types/domain";
import type { StepId } from "@/lib/questions";
import { hasPartner } from "@/lib/questions";

/** 各ステップで「次へ」に進めるかどうかの必須項目チェック */
export function canProceed(stepId: StepId, answers: Answers): boolean {
  switch (stepId) {
    case "family_type":
      return !!answers.familyType;
    case "future_family":
      return !!answers.futureFamilyPlan;
    case "age":
      return !!answers.ageBand;
    case "income":
      return (
        answers.incomeSelf !== undefined &&
        answers.incomeSelf >= 0 &&
        (!hasPartner(answers) || answers.incomePartner !== undefined)
      );
    case "funds":
      return answers.ownFunds !== undefined && answers.fundsToKeep !== undefined;
    case "other_loans":
      return !!(answers.otherLoanTypes && answers.otherLoanTypes.length > 0);
    case "monthly_budget":
      return !!answers.monthlyHousingBudget;
    case "commute": {
      const selfOk = !!answers.commuteSelf?.stationName && !!answers.commuteSelf?.maxMinutes;
      if (!hasPartner(answers)) return selfOk;
      const partnerOk =
        !!answers.commutePartner?.stationName && !!answers.commutePartner?.maxMinutes;
      return selfOk && partnerOk && !!answers.commutePriority;
    }
    case "leisure":
      return !!(answers.leisureActivities && answers.leisureActivities.length > 0);
    case "town_preference":
      return !!answers.townPreferences;
    case "childcare":
      return !!(answers.childcarePriorities && answers.childcarePriorities.length > 0);
    case "car":
      return !!answers.carStatus;
    case "property_kind":
      return !!answers.propertyKind && !!answers.newOrUsed;
    case "asset_priority":
      return !!answers.assetPriority;
    case "future_ownership":
      return !!answers.futureOwnershipPlan;
    case "must_conditions":
      return !!(answers.mustConditions && answers.mustConditions.length > 0);
    default:
      return true;
  }
}
