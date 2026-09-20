"use client";

import { useMemo } from "react";
import Link from "next/link";
import { Container } from "@/components/ui/Container";
import { Button } from "@/components/ui/Button";
import { Section } from "@/components/result/Section";
import { BudgetCard } from "@/components/result/BudgetCard";
import { AreaCard } from "@/components/result/AreaCard";
import { RecommendedConditionCard } from "@/components/result/RecommendedConditionCard";
import { RelaxationCard } from "@/components/result/RelaxationCard";
import { PlanCard } from "@/components/result/PlanCard";
import { useDiagnosisStore } from "@/store/useDiagnosisStore";
import { runDiagnosis } from "@/lib/logic/diagnosis";
import { mustConditionLabel } from "@/lib/labels";
import { useHasMounted } from "@/lib/useHasMounted";

export default function ResultPage() {
  const mounted = useHasMounted();
  const answers = useDiagnosisStore((s) => s.answers);
  const hasStarted = useDiagnosisStore((s) => s.hasStarted);

  const result = useMemo(() => {
    if (!mounted || !hasStarted) return null;
    return runDiagnosis(answers);
  }, [mounted, hasStarted, answers]);

  if (!mounted) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <p className="text-sm text-[var(--color-ink-soft)]">診断結果を計算しています…</p>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center px-6 text-center">
        <p className="text-base font-bold text-[var(--color-navy)]">
          まだ診断が完了していません
        </p>
        <p className="mt-2 text-sm text-[var(--color-ink-soft)]">
          質問に回答すると、あなたに合うエリアと物件条件をご提案します。
        </p>
        <Link href="/diagnose" className="mt-6">
          <Button>診断をはじめる</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col bg-[var(--color-surface)]">
      <div className="bg-[var(--color-navy)] py-10 text-white">
        <Container>
          <p className="text-xs font-bold tracking-widest text-[var(--color-gold)]">
            あなたの住宅購入タイプ
          </p>
          <h1 className="mt-2 text-2xl font-black leading-snug">{result.buyerProfile.title}</h1>
          <p className="mt-3 text-sm leading-relaxed text-white/80">
            {result.buyerProfile.description}
          </p>
        </Container>
      </div>

      <Container className="py-2">
        <Section eyebrow="Budget" title="購入予算">
          <BudgetCard budget={result.budget} />
        </Section>

        <Section eyebrow="Areas" title="あなたに合うエリア">
          <div className="space-y-4">
            {result.topAreas.map((scored, i) => (
              <AreaCard key={scored.area.id} scored={scored} rank={i + 1} />
            ))}
          </div>
          <p className="mt-3 text-[11px] leading-relaxed text-[var(--color-ink-soft)]">
            ※
            エリアスコアは統計データに基づく実測値ではなく、V1用の参考評価(モックデータ)です。通勤時間も路線ごとの目安から算出した参考値です。
          </p>
        </Section>

        <Section eyebrow="Property Condition" title="おすすめの物件条件">
          <RecommendedConditionCard condition={result.recommendedCondition} />
        </Section>

        {result.relaxationSuggestions.length > 0 && (
          <Section eyebrow="Suggestion" title="条件を少し変えると、選択肢が広がります">
            <div className="space-y-4">
              {result.relaxationSuggestions.map((s, i) => (
                <RelaxationCard key={i} suggestion={s} />
              ))}
            </div>
          </Section>
        )}

        <Section eyebrow="3 Plans" title="3つの購入プランを比較">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            {result.plans.map((plan) => (
              <PlanCard key={plan.key} plan={plan} />
            ))}
          </div>
        </Section>

        {(result.mustConditions.length > 0 || result.wantConditions.length > 0) && (
          <Section eyebrow="Priorities" title="あなたの譲れない条件・叶えたい条件">
            <div className="space-y-3">
              {result.mustConditions.length > 0 && (
                <div>
                  <p className="mb-1.5 text-xs font-bold text-[var(--color-navy)]">
                    絶対条件(Must)
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {result.mustConditions.map((c) => (
                      <span
                        key={c}
                        className="rounded-full bg-[var(--color-navy)] px-3 py-1 text-xs font-bold text-white"
                      >
                        {mustConditionLabel(c)}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              <div>
                <p className="mb-1.5 text-xs font-bold text-[var(--color-ink-soft)]">
                  できれば叶えたい条件(Want)
                </p>
                <div className="flex flex-wrap gap-2">
                  {result.wantConditions.map((c) => (
                    <span
                      key={c}
                      className="rounded-full bg-[var(--color-surface)] px-3 py-1 text-xs font-medium text-[var(--color-ink-soft)] ring-1 ring-[var(--color-border)]"
                    >
                      {mustConditionLabel(c)}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </Section>
        )}

        <section className="py-10 text-center">
          <p className="text-sm font-bold text-[var(--color-navy)]">
            この診断結果を、実際の物件探しに活かしませんか？
          </p>
          <p className="mt-2 text-xs leading-relaxed text-[var(--color-ink-soft)]">
            診断結果をもとに、現在販売されている物件を担当者がお探しします。
          </p>
          <Link href="/contact" className="mt-5 inline-block w-full sm:w-auto">
            <Button fullWidth>この条件で実際に買える物件を見てみる</Button>
          </Link>
        </section>

        <footer className="border-t border-[var(--color-border)] py-6">
          <p className="text-center text-[11px] leading-relaxed text-[var(--color-ink-soft)]">
            本診断は住宅ローンの正式な融資審査ではありません。価格・資産性・エリア評価はV1時点の参考情報であり、将来の値上がりや値下がりを保証するものではありません。
          </p>
        </footer>
      </Container>
    </div>
  );
}
