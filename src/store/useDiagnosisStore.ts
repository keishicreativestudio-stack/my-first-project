"use client";

import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";
import type { Answers } from "@/types/domain";
import type { StepId } from "@/lib/questions";

interface DiagnosisState {
  answers: Answers;
  /** ユーザーが現在表示している質問のID。表示ステップ一覧は回答内容に応じて変わるため、
   *  インデックスではなくIDで保持することでブラウザを閉じても正しい位置から再開できる。 */
  currentStepId: StepId | null;
  hasStarted: boolean;
  isCompleted: boolean;
  setAnswer: <K extends keyof Answers>(key: K, value: Answers[K]) => void;
  setAnswers: (partial: Partial<Answers>) => void;
  setCurrentStepId: (id: StepId | null) => void;
  startDiagnosis: () => void;
  completeDiagnosis: () => void;
  reset: () => void;
}

const initialState = {
  answers: {} as Answers,
  currentStepId: null as StepId | null,
  hasStarted: false,
  isCompleted: false,
};

export const useDiagnosisStore = create<DiagnosisState>()(
  persist(
    (set) => ({
      ...initialState,
      setAnswer: (key, value) =>
        set((state) => ({ answers: { ...state.answers, [key]: value } })),
      setAnswers: (partial) =>
        set((state) => ({ answers: { ...state.answers, ...partial } })),
      setCurrentStepId: (id) => set({ currentStepId: id }),
      startDiagnosis: () => set({ hasStarted: true }),
      completeDiagnosis: () => set({ isCompleted: true }),
      reset: () => set({ ...initialState, answers: {} }),
    }),
    {
      name: "sumai-concierge-diagnosis",
      storage: createJSONStorage(() => localStorage),
      version: 1,
    }
  )
);
