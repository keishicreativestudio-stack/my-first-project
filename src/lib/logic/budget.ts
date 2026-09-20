import { BUDGET_ASSUMPTIONS } from "@/data/config";
import type { Answers, BudgetResult } from "@/types/domain";

/** 年代の代表年齢(歳)。ローン完済年齢の概算に利用する。 */
const AGE_BAND_REPRESENTATIVE: Record<string, number> = {
  "20s": 25,
  "30s": 35,
  "40s": 45,
  "50s": 55,
  "60s_plus": 65,
};

/** 完済想定年齢の上限(歳)。この年齢を超えない範囲で返済期間を調整する。 */
const MAX_PAYOFF_AGE = 80;

function monthlyBudgetOptionToManYen(answers: Answers): number | null {
  if (answers.monthlyHousingBudgetCustom && answers.monthlyHousingBudgetCustom > 0) {
    return answers.monthlyHousingBudgetCustom;
  }
  switch (answers.monthlyHousingBudget) {
    case "100000":
      return 10;
    case "150000":
      return 15;
    case "200000":
      return 20;
    case "250000":
      return 25;
    case "300000":
      return 30;
    case "350000_plus":
      return 35;
    case "unknown":
    default:
      return null;
  }
}

/** 元利均等返済のローン元本(万円)を、月々返済額(万円)から逆算する。 */
function loanPrincipalFromMonthlyPayment(
  monthlyPaymentManYen: number,
  annualRatePercent: number,
  termYears: number
): number {
  if (monthlyPaymentManYen <= 0 || termYears <= 0) return 0;
  const monthlyRate = annualRatePercent / 100 / 12;
  const n = termYears * 12;
  if (monthlyRate === 0) return monthlyPaymentManYen * n;
  const factor = (1 - Math.pow(1 + monthlyRate, -n)) / monthlyRate;
  return monthlyPaymentManYen * factor;
}

function estimateLoanTermYears(answers: Answers): number {
  const representativeAge =
    answers.exactAge ?? (answers.ageBand ? AGE_BAND_REPRESENTATIVE[answers.ageBand] : 35);
  const ageBasedMax = Math.max(MAX_PAYOFF_AGE - representativeAge, 5);
  return Math.min(BUDGET_ASSUMPTIONS.loanTermYears, ageBasedMax);
}

export function calculateBudget(answers: Answers): BudgetResult {
  const incomeSelf = answers.incomeSelf ?? 0;
  const incomePartner = answers.incomePartner ?? 0;
  const totalHouseholdIncomeManYen = incomeSelf + incomePartner;

  const otherLoanMonthly = answers.otherLoanTypes?.includes("none")
    ? 0
    : answers.otherLoanMonthlyPayment ?? 0;
  const otherLoanAnnual = otherLoanMonthly * 12;

  const termYears = estimateLoanTermYears(answers);
  const { interestRatePercent, maxDebtToIncomeRatioPercent, comfortableDebtToIncomeRatioPercent } =
    BUDGET_ASSUMPTIONS;

  // 借入可能額の参考目安 (審査基準に近い返済負担率の上限を使用)
  const maxAnnualRepayment = Math.max(
    totalHouseholdIncomeManYen * (maxDebtToIncomeRatioPercent / 100) - otherLoanAnnual,
    0
  );
  const maxMonthlyRepayment = maxAnnualRepayment / 12;
  const maxLoanAmountManYen = Math.round(
    loanPrincipalFromMonthlyPayment(maxMonthlyRepayment, interestRatePercent, termYears)
  );

  // 無理のない返済額: ユーザーが答えた「毎月の住宅費」を優先し、未回答なら保守的な負担率を使う
  const userStatedMonthly = monthlyBudgetOptionToManYen(answers);
  const comfortableAnnualRepaymentFallback = Math.max(
    totalHouseholdIncomeManYen * (comfortableDebtToIncomeRatioPercent / 100) - otherLoanAnnual,
    0
  );
  const comfortableMonthlyRepayment =
    userStatedMonthly ?? comfortableAnnualRepaymentFallback / 12;
  const comfortableLoanAmountManYen = loanPrincipalFromMonthlyPayment(
    comfortableMonthlyRepayment,
    interestRatePercent,
    termYears
  );

  const ownFunds = Math.max(answers.ownFunds ?? 0, 0);
  const fundsToKeep = Math.max(answers.fundsToKeep ?? 0, 0);
  const usableOwnFundsManYen = Math.max(ownFunds - fundsToKeep, 0);

  const comfortableCenter = comfortableLoanAmountManYen + usableOwnFundsManYen;
  const comfortableMin = Math.max(Math.round(comfortableCenter * 0.9), 0);
  const comfortableMax = Math.min(
    Math.round(comfortableCenter * 1.08),
    maxLoanAmountManYen + usableOwnFundsManYen
  );

  return {
    maxLoanAmountManYen,
    comfortablePurchaseRangeManYen: {
      min: comfortableMin,
      max: Math.max(comfortableMax, comfortableMin),
    },
    monthlyRepaymentManYen: Math.round(comfortableMonthlyRepayment * 10) / 10,
    usableOwnFundsManYen,
    assumptions: {
      interestRatePercent,
      loanTermYears: termYears,
      maxDebtToIncomeRatioPercent,
      comfortableDebtToIncomeRatioPercent,
    },
    totalHouseholdIncomeManYen,
  };
}
