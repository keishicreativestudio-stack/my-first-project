export function ProgressBar({
  current,
  total,
  label,
}: {
  current: number;
  total: number;
  label?: string;
}) {
  const percent = total > 0 ? Math.min(100, Math.round((current / total) * 100)) : 0;
  return (
    <div>
      <div className="mb-1.5 flex items-center justify-between text-xs font-medium text-[var(--color-ink-soft)]">
        <span>{label ?? `質問 ${current} / ${total}`}</span>
        <span>{percent}%</span>
      </div>
      <div
        className="h-1.5 w-full overflow-hidden rounded-full bg-[var(--color-border)]"
        role="progressbar"
        aria-valuenow={percent}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div
          className="h-full rounded-full bg-[var(--color-gold)] transition-all duration-300 ease-out"
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  );
}
