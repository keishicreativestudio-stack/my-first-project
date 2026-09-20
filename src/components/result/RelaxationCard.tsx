import type { RelaxationSuggestion } from "@/types/domain";
import { Card } from "./Section";

export function RelaxationCard({ suggestion }: { suggestion: RelaxationSuggestion }) {
  return (
    <Card className={suggestion.isMustOverride ? "border-[var(--color-gold)]" : undefined}>
      {suggestion.isMustOverride && (
        <p className="mb-2 inline-block rounded-full bg-[var(--color-gold-soft)] px-2.5 py-1 text-[11px] font-bold text-[var(--color-navy)]">
          もしここだけ緩められるなら
        </p>
      )}
      <p className="text-sm font-bold text-[var(--color-navy)]">{suggestion.conditionLabel}</p>
      <div className="mt-2 flex flex-wrap items-center gap-2 text-sm">
        <span className="rounded-lg bg-[var(--color-surface)] px-2.5 py-1 text-[var(--color-ink-soft)] line-through">
          {suggestion.originalValue}
        </span>
        <span aria-hidden className="text-[var(--color-ink-soft)]">
          →
        </span>
        <span className="rounded-lg bg-[var(--color-navy)]/5 px-2.5 py-1 font-bold text-[var(--color-navy)]">
          {suggestion.suggestedValue}
        </span>
      </div>
      <p className="mt-3 text-[13px] leading-relaxed text-[var(--color-ink-soft)]">
        {suggestion.explanation}
      </p>
    </Card>
  );
}
