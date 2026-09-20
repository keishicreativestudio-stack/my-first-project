import type { PurchasePlan } from "@/types/domain";
import { formatManYen } from "@/lib/labels";
import { Card } from "./Section";

export function PlanCard({ plan }: { plan: PurchasePlan }) {
  return (
    <Card className="flex h-full flex-col">
      <h3 className="text-base font-black text-[var(--color-navy)]">{plan.title}</h3>
      <p className="mt-1 text-sm font-bold text-[var(--color-ink)]">{plan.area}</p>

      <div className="mt-3 space-y-1.5 text-[13px]">
        <div className="flex justify-between">
          <span className="text-[var(--color-ink-soft)]">価格</span>
          <span className="font-bold text-[var(--color-ink)]">
            {formatManYen(plan.priceRangeManYen.min)}〜{formatManYen(plan.priceRangeManYen.max)}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-[var(--color-ink-soft)]">広さ</span>
          <span className="font-bold text-[var(--color-ink)]">
            {plan.floorAreaSqm.min}〜{plan.floorAreaSqm.max}㎡ / {plan.layout}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-[var(--color-ink-soft)]">駅徒歩</span>
          <span className="font-bold text-[var(--color-ink)]">{plan.stationWalkMinutes}分</span>
        </div>
        <div className="flex justify-between">
          <span className="text-[var(--color-ink-soft)]">築年</span>
          <span className="font-bold text-[var(--color-ink)]">
            {plan.buildingAgeYears === 0 ? "新築" : `${plan.buildingAgeYears}年以内`}
          </span>
        </div>
      </div>

      <div className="mt-4 flex-1 space-y-2 border-t border-[var(--color-border)] pt-3">
        <p className="text-[12px] leading-relaxed text-[var(--color-ink)]">
          <span className="font-bold text-[var(--color-success)]">向いている理由　</span>
          {plan.suitableReason}
        </p>
        <p className="text-[12px] leading-relaxed text-[var(--color-ink)]">
          <span className="font-bold text-[var(--color-danger)]">妥協するポイント　</span>
          {plan.tradeOffPoint}
        </p>
      </div>
    </Card>
  );
}
