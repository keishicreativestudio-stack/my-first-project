import type { ButtonHTMLAttributes } from "react";

type Variant = "primary" | "secondary" | "ghost";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  fullWidth?: boolean;
}

const variantClasses: Record<Variant, string> = {
  primary:
    "bg-[var(--color-navy)] text-white hover:bg-[var(--color-navy-deep)] disabled:bg-[var(--color-ink-soft)]",
  secondary:
    "bg-white text-[var(--color-navy)] border border-[var(--color-navy)] hover:bg-[var(--color-navy)]/5 disabled:opacity-50",
  ghost:
    "bg-transparent text-[var(--color-ink-soft)] hover:text-[var(--color-ink)] disabled:opacity-50",
};

export function Button({
  variant = "primary",
  fullWidth = false,
  className = "",
  disabled,
  ...props
}: ButtonProps) {
  return (
    <button
      className={`inline-flex items-center justify-center gap-2 rounded-full px-6 py-3.5 text-base font-bold transition-colors disabled:cursor-not-allowed focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-gold)] ${
        fullWidth ? "w-full" : ""
      } ${variantClasses[variant]} ${className}`}
      disabled={disabled}
      {...props}
    />
  );
}
