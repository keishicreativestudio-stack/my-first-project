import type { RecommendedPropertyCondition } from "@/types/domain";
import { formatManYen, propertyKindLabel } from "@/lib/labels";
import { Card } from "./Section";

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between border-b border-[var(--color-border)] py-2.5 last:border-none">
      <span className="text-sm text-[var(--color-ink-soft)]">{label}</span>
      <span className="text-sm font-bold text-[var(--color-ink)]">{value}</span>
    </div>
  );
}

export function RecommendedConditionCard({
  condition,
}: {
  condition: RecommendedPropertyCondition;
}) {
  return (
    <Card>
      <Row label="エリア" value={condition.areaLabel} />
      <Row
        label="価格"
        value={`${formatManYen(condition.priceRangeManYen.min)}〜${formatManYen(condition.priceRangeManYen.max)}`}
      />
      <Row label="種類" value={propertyKindLabel(condition.propertyKind)} />
      <Row
        label="面積"
        value={`${condition.floorAreaSqm.min}〜${condition.floorAreaSqm.max}㎡`}
      />
      <Row label="間取り" value={condition.layout} />
      <Row label="駅徒歩" value={`${condition.stationWalkMinutes}分以内`} />
      <Row
        label="築年"
        value={condition.buildingAgeYears === 0 ? "新築" : `${condition.buildingAgeYears}年以内`}
      />
      <p className="mt-4 rounded-xl bg-[var(--color-surface)] p-3 text-[13px] leading-relaxed text-[var(--color-ink-soft)]">
        {condition.reason}
      </p>
    </Card>
  );
}
