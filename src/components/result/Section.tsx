import type { ReactNode } from "react";

export function Section({
  eyebrow,
  title,
  children,
}: {
  eyebrow: string;
  title: string;
  children: ReactNode;
}) {
  return (
    <section className="border-b border-[var(--color-border)] py-8 first:pt-0">
      <p className="mb-1.5 text-xs font-bold tracking-widest text-[var(--color-gold)]">
        {eyebrow}
      </p>
      <h2 className="mb-5 text-lg font-black text-[var(--color-navy)]">{title}</h2>
      {children}
    </section>
  );
}

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <div
      className={`rounded-2xl border border-[var(--color-border)] bg-white p-5 shadow-sm ${className}`}
    >
      {children}
    </div>
  );
}
