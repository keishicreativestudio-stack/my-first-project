import { Container } from "@/components/ui/Container";
import { getAllSubmissions } from "@/lib/server/submissionsStore";
import { formatManYen, mustConditionLabel, propertyKindLabel } from "@/lib/labels";

export const dynamic = "force-dynamic";

const CONTACT_METHOD_LABEL: Record<string, string> = {
  phone: "電話",
  email: "メール",
  either: "どちらでも",
};
const CONTACT_TIME_LABEL: Record<string, string> = {
  morning: "午前中",
  daytime: "日中",
  evening: "夕方",
  night: "夜間",
  anytime: "いつでも",
};

export default function AdminPage() {
  const submissions = getAllSubmissions();

  return (
    <div className="flex flex-1 flex-col bg-[var(--color-surface)] py-8">
      <Container className="max-w-4xl">
        <h1 className="text-xl font-black text-[var(--color-navy)]">問い合わせ一覧(営業担当向け・簡易版)</h1>
        <p className="mt-2 text-xs leading-relaxed text-[var(--color-ink-soft)]">
          V1では簡易的にサーバーメモリ上のデータを表示しています。本番運用ではCRM等の永続ストレージに置き換える想定です。
        </p>

        {submissions.length === 0 ? (
          <p className="mt-8 text-sm text-[var(--color-ink-soft)]">まだ問い合わせはありません。</p>
        ) : (
          <div className="mt-6 space-y-4">
            {submissions.map((s) => (
              <details
                key={s.id}
                className="rounded-2xl border border-[var(--color-border)] bg-white p-5 open:shadow-md"
              >
                <summary className="cursor-pointer list-none">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div>
                      <p className="text-base font-bold text-[var(--color-ink)]">{s.contact.name} 様</p>
                      <p className="text-xs text-[var(--color-ink-soft)]">
                        {new Date(s.submittedAt).toLocaleString("ja-JP")}
                      </p>
                    </div>
                    <span className="rounded-full bg-[var(--color-navy)]/5 px-3 py-1 text-xs font-bold text-[var(--color-navy)]">
                      {s.result.buyerProfile.title}
                    </span>
                  </div>
                </summary>

                <div className="mt-4 grid grid-cols-1 gap-4 border-t border-[var(--color-border)] pt-4 sm:grid-cols-2">
                  <div>
                    <p className="text-xs font-bold text-[var(--color-navy)]">顧客情報</p>
                    <ul className="mt-1.5 space-y-1 text-[13px] text-[var(--color-ink)]">
                      <li>電話番号: {s.contact.phone}</li>
                      <li>メール: {s.contact.email}</li>
                      <li>
                        希望連絡方法: {CONTACT_METHOD_LABEL[s.contact.preferredContactMethod]} /{" "}
                        {CONTACT_TIME_LABEL[s.contact.preferredContactTime]}
                      </li>
                      {s.contact.freeText && <li>自由記入: {s.contact.freeText}</li>}
                    </ul>
                  </div>

                  <div>
                    <p className="text-xs font-bold text-[var(--color-navy)]">家族構成・世帯情報</p>
                    <ul className="mt-1.5 space-y-1 text-[13px] text-[var(--color-ink)]">
                      <li>家族構成: {s.answers.familyType ?? "未回答"}</li>
                      <li>将来の家族計画: {s.answers.futureFamilyPlan ?? "未回答"}</li>
                      <li>
                        世帯年収: 本人 {s.answers.incomeSelf ?? "-"}万円 / パートナー{" "}
                        {s.answers.incomePartner ?? "-"}万円
                      </li>
                      <li>自己資金: {s.answers.ownFunds ?? "-"}万円</li>
                    </ul>
                  </div>

                  <div>
                    <p className="text-xs font-bold text-[var(--color-navy)]">通勤・住宅タイプ</p>
                    <ul className="mt-1.5 space-y-1 text-[13px] text-[var(--color-ink)]">
                      <li>
                        本人通勤: {s.answers.commuteSelf?.stationName ?? "-"} まで{" "}
                        {s.answers.commuteSelf?.maxMinutes ?? "-"}分以内
                      </li>
                      <li>
                        住宅タイプ:{" "}
                        {s.answers.propertyKind ? propertyKindLabel(s.answers.propertyKind) : "未回答"}
                      </li>
                      <li>車: {s.answers.carStatus ?? "未回答"}</li>
                      <li>資産性の優先度: {s.answers.assetPriority ?? "未回答"}</li>
                    </ul>
                  </div>

                  <div>
                    <p className="text-xs font-bold text-[var(--color-navy)]">Must / Want条件</p>
                    <p className="mt-1.5 text-[13px] text-[var(--color-ink)]">
                      Must: {s.result.mustConditions.map(mustConditionLabel).join("、") || "なし"}
                    </p>
                  </div>

                  <div className="sm:col-span-2">
                    <p className="text-xs font-bold text-[var(--color-navy)]">AI提案結果</p>
                    <p className="mt-1.5 text-[13px] text-[var(--color-ink)]">
                      予算目安: {formatManYen(s.result.budget.comfortablePurchaseRangeManYen.min)}〜
                      {formatManYen(s.result.budget.comfortablePurchaseRangeManYen.max)}
                    </p>
                    <p className="mt-1 text-[13px] text-[var(--color-ink)]">
                      おすすめエリア:{" "}
                      {s.result.topAreas
                        .map((a) => `${a.area.representativeStation}(${Math.round(a.totalScore)}%)`)
                        .join("、")}
                    </p>
                    <p className="mt-1 text-[13px] text-[var(--color-ink)]">
                      おすすめ物件条件: {s.result.recommendedCondition.areaLabel} /{" "}
                      {propertyKindLabel(s.result.recommendedCondition.propertyKind)} /{" "}
                      {s.result.recommendedCondition.floorAreaSqm.min}〜
                      {s.result.recommendedCondition.floorAreaSqm.max}㎡
                    </p>
                  </div>
                </div>
              </details>
            ))}
          </div>
        )}
      </Container>
    </div>
  );
}
