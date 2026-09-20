import {
  PROPERTY_KIND_OPTIONS,
  MUST_CONDITION_OPTIONS,
  type SelectOption,
} from "@/lib/questions";
import type { AreaScoreBreakdown, MustCondition, PropertyKind } from "@/types/domain";

function toLabelMap<T extends string>(options: readonly SelectOption<T>[]): Record<T, string> {
  return Object.fromEntries(options.map((o) => [o.value, o.label])) as Record<T, string>;
}

export const PROPERTY_KIND_LABELS = toLabelMap(PROPERTY_KIND_OPTIONS);
export const MUST_CONDITION_LABELS = toLabelMap(MUST_CONDITION_OPTIONS);

export function propertyKindLabel(kind: PropertyKind): string {
  return PROPERTY_KIND_LABELS[kind] ?? kind;
}

export function mustConditionLabel(condition: MustCondition): string {
  return MUST_CONDITION_LABELS[condition] ?? condition;
}

export const BREAKDOWN_LABELS: Record<keyof AreaScoreBreakdown, string> = {
  commuteFit: "通勤",
  budgetFit: "価格",
  townPreferenceFit: "街の雰囲気",
  familyChildcareFit: "子育て",
  propertyTypeFit: "住宅タイプ",
  assetFit: "資産性",
  carAndOtherFit: "車・その他",
};

export function formatManYen(value: number): string {
  if (Math.abs(value) >= 10000) {
    const oku = value / 10000;
    return `${oku.toFixed(oku % 1 === 0 ? 0 : 1)}億円`;
  }
  return `${Math.round(value).toLocaleString("ja-JP")}万円`;
}
