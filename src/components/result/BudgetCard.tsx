import type { BudgetResult } from "@/types/domain";
import { formatManYen } from "@/lib/labels";
import { Card } from "./Section";

export function BudgetCard({ budget }: { budget: BudgetResult }) {
  return (
    <Card>
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
        <div>
          <p className="text-xs font-bold text-[var(--color-ink-soft)]">借入可能額の参考目安</p>
          <p className="mt-1 text-2xl font-black text-[var(--color-navy)]">
            {formatManYen(budget.maxLoanAmountManYen)}
          </p>
        </div>
        <div>
          <p className="text-xs font-bold text-[var(--color-ink-soft)]">おすすめ購入価格</p>
          <p className="mt-1 text-2xl font-black text-[var(--color-navy)]">
            {formatManYen(budget.comfortablePurchaseRangeManYen.min)}〜
            {formatManYen(budget.comfortablePurchaseRangeManYen.max)}
          </p>
        </div>
      </div>
      <div className="mt-5 flex items-center justify-between rounded-xl bg-[var(--color-surface)] px-4 py-3">
        <span className="text-sm font-bold text-[var(--color-ink)]">毎月返済参考額</span>
        <span className="text-lg font-black text-[var(--color-navy)]">
          約{budget.monthlyRepaymentManYen}万円
        </span>
      </div>

      <details className="mt-4 text-sm text-[var(--color-ink-soft)]">
        <summary className="cursor-pointer font-bold text-[var(--color-navy)]">
          計算の前提・注意事項を見る
        </summary>
        <ul className="mt-3 list-disc space-y-1.5 pl-5 leading-relaxed">
          <li>金利(年率): {budget.assumptions.interestRatePercent}%(参考値)</li>
          <li>返済期間: {budget.assumptions.loanTermYears}年</li>
          <li>審査上の返済負担率の目安: {budget.assumptions.maxDebtToIncomeRatioPercent}%</li>
          <li>無理のない返済負担率の目安: {budget.assumptions.comfortableDebtToIncomeRatioPercent}%</li>
          <li>世帯年収合計: {budget.totalHouseholdIncomeManYen}万円で計算</li>
          <li>自己資金のうち購入に充当できる額: {formatManYen(budget.usableOwnFundsManYen)}</li>
        </ul>
        <p className="mt-3 rounded-lg bg-[var(--color-gold-soft)]/40 px-3 py-2 text-xs leading-relaxed text-[var(--color-ink)]">
          ※
          これは金融機関による正式な融資審査の結果ではありません。実際の借入可能額は、金融機関の審査により異なります。あくまで購入検討の参考目安としてご利用ください。
        </p>
      </details>
    </Card>
  );
}
