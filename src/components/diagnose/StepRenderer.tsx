"use client";

import type { Answers, TownPreferenceSliders } from "@/types/domain";
import type { StepId } from "@/lib/questions";
import {
  STEPS,
  hasPartner,
  FAMILY_TYPE_OPTIONS,
  FUTURE_FAMILY_OPTIONS,
  AGE_BAND_OPTIONS,
  OTHER_LOAN_OPTIONS,
  MONTHLY_BUDGET_OPTIONS,
  LEISURE_OPTIONS,
  CHILDCARE_OPTIONS,
  CAR_STATUS_OPTIONS,
  PROPERTY_KIND_OPTIONS,
  NEW_OR_USED_OPTIONS,
  ASSET_PRIORITY_OPTIONS,
  FUTURE_OWNERSHIP_OPTIONS,
  MUST_CONDITION_OPTIONS,
} from "@/lib/questions";
import {
  incomeManYenSchema,
  fundsManYenSchema,
  exactAgeSchema,
  commuteMinutesSchema,
  familyMemberCountSchema,
  MAX_MUST_CONDITIONS,
  MAX_CHILDCARE_PRIORITIES,
} from "@/lib/validation";
import {
  QuestionShell,
  SingleSelectList,
  MultiSelectList,
  PriorityMultiSelect,
  NumberField,
  TextField,
  SliderField,
} from "./fields";

const DEFAULT_TOWN_PREFERENCES: TownPreferenceSliders = {
  quietVsLively: 3,
  natureVsUrban: 3,
  traditionalVsModern: 3,
  chainVsIndependent: 3,
  calmVsExciting: 3,
};

export function StepRenderer({
  stepId,
  answers,
  patch,
}: {
  stepId: StepId;
  answers: Answers;
  patch: (partial: Partial<Answers>) => void;
}) {
  const def = STEPS.find((s) => s.id === stepId);
  if (!def) return null;

  switch (stepId) {
    case "family_type":
      return (
        <QuestionShell title={def.title} subtitle={def.subtitle}>
          <SingleSelectList
            options={FAMILY_TYPE_OPTIONS}
            value={answers.familyType}
            onChange={(v) => patch({ familyType: v })}
          />
          {(answers.familyType === "couple_with_children" ||
            answers.familyType === "single_parent" ||
            answers.familyType === "with_parents" ||
            answers.familyType === "other") && (
            <div className="mt-5">
              <NumberField
                label="同居予定の人数(ご自身を含む)"
                value={answers.familyMemberCount}
                onChange={(v) => patch({ familyMemberCount: v })}
                schema={familyMemberCountSchema}
                suffix="人"
              />
            </div>
          )}
        </QuestionShell>
      );

    case "future_family":
      return (
        <QuestionShell title={def.title} subtitle={def.subtitle}>
          <SingleSelectList
            options={FUTURE_FAMILY_OPTIONS}
            value={answers.futureFamilyPlan}
            onChange={(v) => patch({ futureFamilyPlan: v })}
          />
        </QuestionShell>
      );

    case "age":
      return (
        <QuestionShell title={def.title} subtitle={def.subtitle}>
          <SingleSelectList
            options={AGE_BAND_OPTIONS}
            value={answers.ageBand}
            onChange={(v) => patch({ ageBand: v })}
          />
          <div className="mt-5">
            <NumberField
              label="詳しい年齢(任意)"
              value={answers.exactAge}
              onChange={(v) => patch({ exactAge: v })}
              schema={exactAgeSchema}
              suffix="歳"
              placeholder="例: 34"
            />
          </div>
        </QuestionShell>
      );

    case "income":
      return (
        <QuestionShell title={def.title} subtitle={def.subtitle}>
          <div className="space-y-5">
            <NumberField
              label="本人の年収"
              value={answers.incomeSelf}
              onChange={(v) => patch({ incomeSelf: v })}
              schema={incomeManYenSchema}
              suffix="万円"
              placeholder="例: 600"
            />
            {hasPartner(answers) && (
              <NumberField
                label="配偶者・パートナーの年収"
                value={answers.incomePartner}
                onChange={(v) => patch({ incomePartner: v })}
                schema={incomeManYenSchema}
                suffix="万円"
                placeholder="例: 400"
              />
            )}
          </div>
        </QuestionShell>
      );

    case "funds":
      return (
        <QuestionShell title={def.title} subtitle={def.subtitle}>
          <div className="space-y-5">
            <NumberField
              label="住宅購入に使える自己資金"
              value={answers.ownFunds}
              onChange={(v) => patch({ ownFunds: v })}
              schema={fundsManYenSchema}
              suffix="万円"
              placeholder="例: 500"
            />
            <NumberField
              label="購入後も手元に残しておきたい現金"
              value={answers.fundsToKeep}
              onChange={(v) => patch({ fundsToKeep: v })}
              schema={fundsManYenSchema}
              suffix="万円"
              placeholder="例: 100"
            />
          </div>
        </QuestionShell>
      );

    case "other_loans":
      return (
        <QuestionShell title={def.title}>
          <MultiSelectList
            options={OTHER_LOAN_OPTIONS}
            values={answers.otherLoanTypes ?? []}
            onChange={(v) => patch({ otherLoanTypes: v })}
          />
          {answers.otherLoanTypes &&
            answers.otherLoanTypes.length > 0 &&
            !answers.otherLoanTypes.includes("none") && (
              <div className="mt-5">
                <NumberField
                  label="その他借入の月々の返済額"
                  value={answers.otherLoanMonthlyPayment}
                  onChange={(v) => patch({ otherLoanMonthlyPayment: v })}
                  schema={fundsManYenSchema}
                  suffix="万円/月"
                  placeholder="例: 2"
                />
              </div>
            )}
        </QuestionShell>
      );

    case "monthly_budget":
      return (
        <QuestionShell title={def.title} subtitle={def.subtitle}>
          <SingleSelectList
            options={MONTHLY_BUDGET_OPTIONS}
            value={answers.monthlyHousingBudget}
            onChange={(v) => patch({ monthlyHousingBudget: v })}
          />
        </QuestionShell>
      );

    case "commute":
      return (
        <QuestionShell title={def.title} subtitle={def.subtitle}>
          <div className="space-y-6">
            <div className="rounded-2xl border border-[var(--color-border)] bg-white p-4">
              <p className="mb-3 text-sm font-bold text-[var(--color-navy)]">本人の通勤</p>
              <div className="space-y-3">
                <TextField
                  label="勤務先の最寄駅"
                  value={answers.commuteSelf?.stationName ?? ""}
                  onChange={(v) =>
                    patch({
                      commuteSelf: {
                        stationName: v,
                        maxMinutes: answers.commuteSelf?.maxMinutes ?? 30,
                      },
                    })
                  }
                  placeholder="例: 新宿駅"
                />
                <NumberField
                  label="希望する通勤時間(片道)"
                  value={answers.commuteSelf?.maxMinutes}
                  onChange={(v) =>
                    patch({
                      commuteSelf: {
                        stationName: answers.commuteSelf?.stationName ?? "",
                        maxMinutes: v ?? 30,
                      },
                    })
                  }
                  schema={commuteMinutesSchema}
                  suffix="分以内"
                  placeholder="例: 40"
                />
              </div>
            </div>

            {hasPartner(answers) && (
              <div className="rounded-2xl border border-[var(--color-border)] bg-white p-4">
                <p className="mb-3 text-sm font-bold text-[var(--color-navy)]">
                  配偶者・パートナーの通勤
                </p>
                <div className="space-y-3">
                  <TextField
                    label="勤務先の最寄駅"
                    value={answers.commutePartner?.stationName ?? ""}
                    onChange={(v) =>
                      patch({
                        commutePartner: {
                          stationName: v,
                          maxMinutes: answers.commutePartner?.maxMinutes ?? 30,
                        },
                      })
                    }
                    placeholder="例: 東京駅"
                  />
                  <NumberField
                    label="希望する通勤時間(片道)"
                    value={answers.commutePartner?.maxMinutes}
                    onChange={(v) =>
                      patch({
                        commutePartner: {
                          stationName: answers.commutePartner?.stationName ?? "",
                          maxMinutes: v ?? 30,
                        },
                      })
                    }
                    schema={commuteMinutesSchema}
                    suffix="分以内"
                    placeholder="例: 45"
                  />
                </div>
                <div className="mt-4">
                  <p className="mb-2 text-sm font-bold text-[var(--color-ink)]">
                    どちらの通勤を優先しますか？
                  </p>
                  <SingleSelectList
                    options={[
                      { value: "equal", label: "同じくらい" },
                      { value: "self", label: "自分を優先" },
                      { value: "partner", label: "パートナーを優先" },
                    ]}
                    value={answers.commutePriority}
                    onChange={(v) => patch({ commutePriority: v })}
                  />
                </div>
              </div>
            )}
            <p className="text-xs leading-relaxed text-[var(--color-ink-soft)]">
              ※ V1では実際の鉄道経路検索を行わず、路線ごとの目安時間からモックで算出しています。
            </p>
          </div>
        </QuestionShell>
      );

    case "leisure":
      return (
        <QuestionShell title={def.title} subtitle={def.subtitle}>
          <MultiSelectList
            options={LEISURE_OPTIONS}
            values={answers.leisureActivities ?? []}
            onChange={(v) => patch({ leisureActivities: v })}
          />
        </QuestionShell>
      );

    case "town_preference": {
      const p = answers.townPreferences ?? DEFAULT_TOWN_PREFERENCES;
      const set = (partial: Partial<TownPreferenceSliders>) =>
        patch({ townPreferences: { ...p, ...partial } });
      return (
        <QuestionShell title={def.title} subtitle={def.subtitle}>
          <div className="space-y-7">
            <SliderField
              leftLabel="静かな住宅街"
              rightLabel="賑やかな街"
              value={p.quietVsLively}
              onChange={(v) => set({ quietVsLively: v })}
            />
            <SliderField
              leftLabel="自然が多い"
              rightLabel="都会的"
              value={p.natureVsUrban}
              onChange={(v) => set({ natureVsUrban: v })}
            />
            <SliderField
              leftLabel="昔ながら"
              rightLabel="新しく整備された街"
              value={p.traditionalVsModern}
              onChange={(v) => set({ traditionalVsModern: v })}
            />
            <SliderField
              leftLabel="大型商業施設が便利"
              rightLabel="個性的な個人店が多い"
              value={p.chainVsIndependent}
              onChange={(v) => set({ chainVsIndependent: v })}
            />
            <SliderField
              leftLabel="落ち着き"
              rightLabel="刺激・利便性"
              value={p.calmVsExciting}
              onChange={(v) => set({ calmVsExciting: v })}
            />
          </div>
        </QuestionShell>
      );
    }

    case "childcare":
      return (
        <QuestionShell title={def.title} subtitle={def.subtitle}>
          <PriorityMultiSelect
            options={CHILDCARE_OPTIONS}
            values={answers.childcarePriorities ?? []}
            onChange={(v) => patch({ childcarePriorities: v })}
            max={MAX_CHILDCARE_PRIORITIES}
          />
        </QuestionShell>
      );

    case "car":
      return (
        <QuestionShell title={def.title}>
          <SingleSelectList
            options={CAR_STATUS_OPTIONS}
            value={answers.carStatus}
            onChange={(v) => patch({ carStatus: v })}
          />
        </QuestionShell>
      );

    case "property_kind":
      return (
        <QuestionShell title={def.title}>
          <SingleSelectList
            options={PROPERTY_KIND_OPTIONS}
            value={answers.propertyKind}
            onChange={(v) => patch({ propertyKind: v })}
          />
          <div className="mt-6">
            <p className="mb-2 text-sm font-bold text-[var(--color-ink)]">新築・中古の希望は？</p>
            <SingleSelectList
              options={NEW_OR_USED_OPTIONS}
              value={answers.newOrUsed}
              onChange={(v) => patch({ newOrUsed: v })}
            />
          </div>
        </QuestionShell>
      );

    case "asset_priority":
      return (
        <QuestionShell title={def.title} subtitle={def.subtitle}>
          <SingleSelectList
            options={ASSET_PRIORITY_OPTIONS}
            value={answers.assetPriority}
            onChange={(v) => patch({ assetPriority: v })}
          />
        </QuestionShell>
      );

    case "future_ownership":
      return (
        <QuestionShell title={def.title}>
          <SingleSelectList
            options={FUTURE_OWNERSHIP_OPTIONS}
            value={answers.futureOwnershipPlan}
            onChange={(v) => patch({ futureOwnershipPlan: v })}
          />
        </QuestionShell>
      );

    case "must_conditions":
      return (
        <QuestionShell title={def.title} subtitle={def.subtitle}>
          <MultiSelectList
            options={MUST_CONDITION_OPTIONS}
            values={answers.mustConditions ?? []}
            onChange={(v) => patch({ mustConditions: v })}
            max={MAX_MUST_CONDITIONS}
          />
        </QuestionShell>
      );

    default:
      return null;
  }
}
