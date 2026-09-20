import type { ScoredArea } from "@/types/domain";
import { BREAKDOWN_LABELS } from "@/lib/labels";
import { Card } from "./Section";

const VISIBLE_METRICS = ["commuteFit", "budgetFit", "familyChildcareFit", "townPreferenceFit", "assetFit"] as const;

export function AreaCard({ scored, rank }: { scored: ScoredArea; rank: number }) {
  const matchPercent = Math.round(scored.totalScore);
  return (
    <Card className="relative">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-bold text-[var(--color-gold)]">エリア {rank}</p>
          <h3 className="mt-0.5 text-lg font-black text-[var(--color-navy)]">
            {scored.area.city}・{scored.area.representativeStation}
          </h3>
          <p className="mt-0.5 text-xs text-[var(--color-ink-soft)]">
            {scored.area.lines.join(" / ")}
          </p>
        </div>
        <div className="shrink-0 rounded-full bg-[var(--color-navy)] px-3 py-1.5 text-center">
          <p className="text-[10px] font-bold text-white/70">マッチ度</p>
          <p className="text-base font-black text-white">{matchPercent}%</p>
        </div>
      </div>

      <div className="mt-4 space-y-2">
        {VISIBLE_METRICS.map((key) => {
          const value = Math.round(scored.breakdown[key]);
          return (
            <div key={key} className="flex items-center gap-2">
              <span className="w-20 shrink-0 text-[11px] font-medium text-[var(--color-ink-soft)]">
                {BREAKDOWN_LABELS[key]}
              </span>
              <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-[var(--color-border)]">
                <div
                  className="h-full rounded-full bg-[var(--color-gold)]"
                  style={{ width: `${Math.min(100, value)}%` }}
                />
              </div>
              <span className="w-8 shrink-0 text-right text-[11px] tabular-nums text-[var(--color-ink-soft)]">
                {value}
              </span>
            </div>
          );
        })}
      </div>

      <ul className="mt-4 space-y-1.5 border-t border-[var(--color-border)] pt-4">
        {scored.reasons.map((reason, i) => (
          <li key={i} className="flex gap-2 text-[13px] leading-relaxed text-[var(--color-ink)]">
            <span aria-hidden className="text-[var(--color-gold)]">
              ・
            </span>
            <span>{reason}</span>
          </li>
        ))}
      </ul>

      <p className="mt-3 text-[11px] text-[var(--color-ink-soft)]">{scored.area.notes}</p>
    </Card>
  );
}
