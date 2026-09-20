"use client";

import { useId, useState } from "react";
import type { z } from "zod";
import type { SelectOption } from "@/lib/questions";

export function QuestionShell({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <h1 className="text-xl font-bold leading-snug text-[var(--color-navy)]">{title}</h1>
      {subtitle && (
        <p className="mt-2 text-sm leading-relaxed text-[var(--color-ink-soft)]">{subtitle}</p>
      )}
      <div className="mt-6">{children}</div>
    </div>
  );
}

export function SingleSelectList<T extends string>({
  options,
  value,
  onChange,
}: {
  options: readonly SelectOption<T>[] | readonly { value: T; label: string }[];
  value?: T;
  onChange: (value: T) => void;
}) {
  return (
    <div className="space-y-2.5" role="radiogroup">
      {options.map((opt) => {
        const selected = opt.value === value;
        return (
          <button
            key={opt.value}
            type="button"
            role="radio"
            aria-checked={selected}
            onClick={() => onChange(opt.value)}
            className={`flex w-full items-center justify-between rounded-2xl border px-4 py-3.5 text-left text-[15px] transition-colors ${
              selected
                ? "border-[var(--color-navy)] bg-[var(--color-navy)]/5 font-bold text-[var(--color-navy)]"
                : "border-[var(--color-border)] bg-white text-[var(--color-ink)] hover:border-[var(--color-navy)]/40"
            }`}
          >
            <span>{opt.label}</span>
            <span
              aria-hidden
              className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-2 ${
                selected ? "border-[var(--color-navy)]" : "border-[var(--color-border)]"
              }`}
            >
              {selected && <span className="h-2.5 w-2.5 rounded-full bg-[var(--color-navy)]" />}
            </span>
          </button>
        );
      })}
    </div>
  );
}

export function MultiSelectList<T extends string>({
  options,
  values,
  onChange,
  max,
}: {
  options: readonly SelectOption<T>[];
  values: T[];
  onChange: (values: T[]) => void;
  max?: number;
}) {
  const toggle = (v: T) => {
    const exists = values.includes(v);
    if (exists) {
      onChange(values.filter((x) => x !== v));
      return;
    }
    if (max && values.length >= max) return;
    onChange([...values, v]);
  };

  return (
    <div>
      {max && (
        <p className="mb-3 text-xs font-medium text-[var(--color-ink-soft)]">
          最大{max}つまで選択できます({values.length}/{max})
        </p>
      )}
      <div className="space-y-2.5" role="group">
        {options.map((opt) => {
          const selected = values.includes(opt.value);
          const disabled = !selected && !!max && values.length >= max;
          return (
            <button
              key={opt.value}
              type="button"
              aria-pressed={selected}
              disabled={disabled}
              onClick={() => toggle(opt.value)}
              className={`flex w-full items-center justify-between rounded-2xl border px-4 py-3.5 text-left text-[15px] transition-colors ${
                selected
                  ? "border-[var(--color-navy)] bg-[var(--color-navy)]/5 font-bold text-[var(--color-navy)]"
                  : disabled
                    ? "border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-ink-soft)] opacity-60"
                    : "border-[var(--color-border)] bg-white text-[var(--color-ink)] hover:border-[var(--color-navy)]/40"
              }`}
            >
              <span>{opt.label}</span>
              <span
                aria-hidden
                className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-md border-2 ${
                  selected ? "border-[var(--color-navy)] bg-[var(--color-navy)]" : "border-[var(--color-border)]"
                }`}
              >
                {selected && (
                  <svg viewBox="0 0 16 16" className="h-3 w-3 fill-white">
                    <path d="M6.5 11.5 3 8l1-1 2.5 2.5L12 4l1 1z" />
                  </svg>
                )}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

/** 優先順位付きの複数選択(選んだ順に1位・2位・3位が付く) */
export function PriorityMultiSelect<T extends string>({
  options,
  values,
  onChange,
  max = 3,
}: {
  options: readonly SelectOption<T>[];
  values: T[];
  onChange: (values: T[]) => void;
  max?: number;
}) {
  const toggle = (v: T) => {
    const exists = values.includes(v);
    if (exists) {
      onChange(values.filter((x) => x !== v));
      return;
    }
    if (values.length >= max) return;
    onChange([...values, v]);
  };

  return (
    <div>
      <p className="mb-3 text-xs font-medium text-[var(--color-ink-soft)]">
        選んだ順に優先順位が付きます({values.length}/{max})
      </p>
      <div className="space-y-2.5" role="group">
        {options.map((opt) => {
          const rank = values.indexOf(opt.value);
          const selected = rank !== -1;
          const disabled = !selected && values.length >= max;
          return (
            <button
              key={opt.value}
              type="button"
              aria-pressed={selected}
              disabled={disabled}
              onClick={() => toggle(opt.value)}
              className={`flex w-full items-center justify-between rounded-2xl border px-4 py-3.5 text-left text-[15px] transition-colors ${
                selected
                  ? "border-[var(--color-gold)] bg-[var(--color-gold-soft)]/40 font-bold text-[var(--color-navy)]"
                  : disabled
                    ? "border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-ink-soft)] opacity-60"
                    : "border-[var(--color-border)] bg-white text-[var(--color-ink)] hover:border-[var(--color-navy)]/40"
              }`}
            >
              <span>{opt.label}</span>
              {selected ? (
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[var(--color-gold)] text-xs font-bold text-white">
                  {rank + 1}
                </span>
              ) : (
                <span
                  aria-hidden
                  className="h-6 w-6 shrink-0 rounded-full border-2 border-[var(--color-border)]"
                />
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}

export function NumberField({
  label,
  value,
  onChange,
  schema,
  suffix,
  placeholder,
  allowUndefined = true,
}: {
  label: string;
  value: number | undefined;
  onChange: (value: number | undefined) => void;
  schema: z.ZodType<number>;
  suffix?: string;
  placeholder?: string;
  allowUndefined?: boolean;
}) {
  const [text, setText] = useState(value !== undefined ? String(value) : "");
  const [error, setError] = useState<string | null>(null);
  const inputId = useId();
  const errorId = `${inputId}-error`;

  const commit = (raw: string) => {
    setText(raw);
    if (raw.trim() === "") {
      setError(null);
      if (allowUndefined) onChange(undefined);
      return;
    }
    const num = Number(raw);
    if (Number.isNaN(num)) {
      setError("数値で入力してください。");
      return;
    }
    const result = schema.safeParse(num);
    if (!result.success) {
      setError(result.error.issues[0]?.message ?? "入力内容をご確認ください。");
      return;
    }
    setError(null);
    onChange(result.data);
  };

  return (
    <div>
      <label htmlFor={inputId} className="mb-1.5 block text-sm font-bold text-[var(--color-ink)]">
        {label}
      </label>
      <div className="flex items-center gap-2">
        <input
          id={inputId}
          type="number"
          inputMode="numeric"
          value={text}
          placeholder={placeholder}
          onChange={(e) => commit(e.target.value)}
          className={`w-full rounded-xl border px-4 py-3 text-[15px] focus:outline-none focus:ring-2 focus:ring-[var(--color-navy)]/30 ${
            error ? "border-[var(--color-danger)]" : "border-[var(--color-border)]"
          }`}
          aria-invalid={!!error}
          aria-describedby={error ? errorId : undefined}
        />
        {suffix && <span className="shrink-0 text-sm text-[var(--color-ink-soft)]">{suffix}</span>}
      </div>
      {error && (
        <p id={errorId} className="mt-1.5 text-xs font-medium text-[var(--color-danger)]">
          {error}
        </p>
      )}
    </div>
  );
}

export function TextField({
  label,
  value,
  onChange,
  placeholder,
  error,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  error?: string | null;
}) {
  const inputId = useId();
  const errorId = `${inputId}-error`;
  return (
    <div>
      <label htmlFor={inputId} className="mb-1.5 block text-sm font-bold text-[var(--color-ink)]">
        {label}
      </label>
      <input
        id={inputId}
        type="text"
        value={value}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
        className={`w-full rounded-xl border px-4 py-3 text-[15px] focus:outline-none focus:ring-2 focus:ring-[var(--color-navy)]/30 ${
          error ? "border-[var(--color-danger)]" : "border-[var(--color-border)]"
        }`}
        aria-invalid={!!error}
        aria-describedby={error ? errorId : undefined}
      />
      {error && (
        <p id={errorId} className="mt-1.5 text-xs font-medium text-[var(--color-danger)]">
          {error}
        </p>
      )}
    </div>
  );
}

export function SliderField({
  leftLabel,
  rightLabel,
  value,
  onChange,
}: {
  leftLabel: string;
  rightLabel: string;
  value: number;
  onChange: (value: number) => void;
}) {
  return (
    <div>
      <div className="mb-2 flex items-center justify-between text-[13px] font-medium text-[var(--color-ink)]">
        <span>{leftLabel}</span>
        <span>{rightLabel}</span>
      </div>
      <input
        type="range"
        min={1}
        max={5}
        step={1}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="h-2 w-full cursor-pointer appearance-none rounded-full bg-[var(--color-border)] accent-[var(--color-navy)]"
        aria-label={`${leftLabel} 〜 ${rightLabel}`}
      />
      <div className="mt-1 flex justify-between px-0.5">
        {[1, 2, 3, 4, 5].map((n) => (
          <span
            key={n}
            className={`h-1 w-1 rounded-full ${
              n <= value ? "bg-[var(--color-navy)]" : "bg-[var(--color-border)]"
            }`}
          />
        ))}
      </div>
    </div>
  );
}
