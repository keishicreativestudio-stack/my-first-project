"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Container } from "@/components/ui/Container";
import { Button } from "@/components/ui/Button";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { StepRenderer } from "@/components/diagnose/StepRenderer";
import { getVisibleSteps } from "@/lib/questions";
import { canProceed } from "@/lib/stepValidation";
import { useDiagnosisStore } from "@/store/useDiagnosisStore";
import { useHasMounted } from "@/lib/useHasMounted";

export default function DiagnosePage() {
  const router = useRouter();
  const mounted = useHasMounted();
  const [showValidationError, setShowValidationError] = useState(false);

  const answers = useDiagnosisStore((s) => s.answers);
  const currentStepId = useDiagnosisStore((s) => s.currentStepId);
  const setAnswers = useDiagnosisStore((s) => s.setAnswers);
  const setCurrentStepId = useDiagnosisStore((s) => s.setCurrentStepId);
  const startDiagnosis = useDiagnosisStore((s) => s.startDiagnosis);
  const completeDiagnosis = useDiagnosisStore((s) => s.completeDiagnosis);

  const visibleSteps = useMemo(() => getVisibleSteps(answers), [answers]);

  useEffect(() => {
    if (!mounted) return;
    startDiagnosis();
    if (!currentStepId || !visibleSteps.some((s) => s.id === currentStepId)) {
      setCurrentStepId(visibleSteps[0]?.id ?? null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mounted]);

  if (!mounted || !currentStepId) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <p className="text-sm text-[var(--color-ink-soft)]">読み込んでいます…</p>
      </div>
    );
  }

  const currentIndex = visibleSteps.findIndex((s) => s.id === currentStepId);
  const total = visibleSteps.length;
  const isLast = currentIndex === total - 1;
  const isFirst = currentIndex === 0;
  const proceedable = canProceed(currentStepId, answers);

  const goNext = () => {
    if (!proceedable) {
      setShowValidationError(true);
      return;
    }
    setShowValidationError(false);
    if (isLast) {
      completeDiagnosis();
      router.push("/result");
      return;
    }
    const nextSteps = getVisibleSteps(answers);
    const idx = nextSteps.findIndex((s) => s.id === currentStepId);
    const next = nextSteps[idx + 1];
    if (next) setCurrentStepId(next.id);
  };

  const goBack = () => {
    setShowValidationError(false);
    if (isFirst) {
      router.push("/");
      return;
    }
    const prev = visibleSteps[currentIndex - 1];
    if (prev) setCurrentStepId(prev.id);
  };

  return (
    <div className="flex min-h-dvh flex-col bg-[var(--color-surface)]">
      <div className="sticky top-0 z-10 border-b border-[var(--color-border)] bg-[var(--color-surface)]/95 backdrop-blur">
        <Container className="py-4">
          <ProgressBar current={currentIndex + 1} total={total} />
        </Container>
      </div>

      <div className="flex-1 py-8">
        <Container>
          <StepRenderer
            stepId={currentStepId}
            answers={answers}
            patch={(partial) => {
              setShowValidationError(false);
              setAnswers(partial);
            }}
          />
          {showValidationError && (
            <p
              role="alert"
              className="mt-5 rounded-xl bg-[var(--color-danger)]/10 px-4 py-3 text-sm font-medium text-[var(--color-danger)]"
            >
              回答が未入力、または内容にご確認が必要な項目があります。
            </p>
          )}
        </Container>
      </div>

      <div className="sticky bottom-0 border-t border-[var(--color-border)] bg-white/95 backdrop-blur">
        <Container className="flex gap-3 py-4">
          <Button variant="ghost" onClick={goBack} className="!px-4">
            戻る
          </Button>
          <Button fullWidth onClick={goNext}>
            {isLast ? "診断結果を見る" : "次へ"}
          </Button>
        </Container>
      </div>
    </div>
  );
}
