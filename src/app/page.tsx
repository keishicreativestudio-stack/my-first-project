import Link from "next/link";
import { Container } from "@/components/ui/Container";
import { Button } from "@/components/ui/Button";

const STEPS = [
  {
    step: "STEP 1",
    title: "質問に答える",
    description: "予算・通勤・暮らし方など、約3分・シンプルな質問に答えるだけ。",
  },
  {
    step: "STEP 2",
    title: "あなたの希望を分析",
    description: "回答をもとに、譲れない条件と叶えたい条件を整理して分析します。",
  },
  {
    step: "STEP 3",
    title: "街・予算・物件条件を提案",
    description: "あなたに合うエリアと、購入価格・広さなどの具体的な条件をご提案します。",
  },
];

export default function Home() {
  return (
    <div className="flex flex-1 flex-col bg-[var(--color-surface)]">
      <section className="border-b border-[var(--color-border)] bg-gradient-to-b from-white to-[var(--color-surface)] pt-14 pb-12">
        <Container>
          <p className="mb-4 text-xs font-bold tracking-widest text-[var(--color-gold)]">
            住まいコンシェルジュAI
          </p>
          <h1 className="text-3xl font-black leading-tight text-[var(--color-navy)] sm:text-4xl">
            あなたに合う家と街を、
            <br />
            AIが見つけます。
          </h1>
          <p className="mt-5 text-[15px] leading-relaxed text-[var(--color-ink-soft)]">
            予算や通勤時間だけでなく、暮らし方や将来設計まで分析。
            <br />
            約3分の質問に答えるだけで、あなたに合った
            <br />
            「街・予算・物件条件」をご提案します。
          </p>
          <div className="mt-8">
            <Link href="/diagnose">
              <Button fullWidth className="shadow-lg shadow-[var(--color-navy)]/10">
                無料で診断する
              </Button>
            </Link>
            <p className="mt-3 text-center text-xs text-[var(--color-ink-soft)]">
              登録不要・所要時間は約3〜5分です
            </p>
          </div>
        </Container>
      </section>

      <section className="py-12">
        <Container>
          <ol className="space-y-5">
            {STEPS.map((s, i) => (
              <li
                key={s.step}
                className="flex gap-4 rounded-2xl bg-white p-5 shadow-sm ring-1 ring-[var(--color-border)]"
              >
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[var(--color-navy)] text-sm font-bold text-white">
                  {i + 1}
                </div>
                <div>
                  <p className="text-[11px] font-bold tracking-widest text-[var(--color-gold)]">
                    {s.step}
                  </p>
                  <h2 className="mt-0.5 text-base font-bold text-[var(--color-ink)]">
                    {s.title}
                  </h2>
                  <p className="mt-1 text-sm leading-relaxed text-[var(--color-ink-soft)]">
                    {s.description}
                  </p>
                </div>
              </li>
            ))}
          </ol>
        </Container>
      </section>

      <section className="border-t border-[var(--color-border)] bg-white py-12">
        <Container>
          <h2 className="text-lg font-bold text-[var(--color-navy)]">
            「どこに、どんな家を買えばいいか分からない」を解決します
          </h2>
          <p className="mt-4 text-sm leading-relaxed text-[var(--color-ink-soft)]">
            一般的な不動産ポータルサイトでは、価格やエリア、駅徒歩などの条件を自分で決める必要があります。
            住まいコンシェルジュAIでは逆に、あなたの暮らし方や将来設計をお聞きし、
            「あなたなら、このエリアで、このくらいの価格・広さの物件を探すと良い」というところまで、
            条件そのものを一緒に整理します。
          </p>
          <p className="mt-4 text-xs leading-relaxed text-[var(--color-ink-soft)]">
            対象エリア：東京都・神奈川県・埼玉県・千葉県(1都3県)
          </p>
        </Container>
      </section>

      <section className="py-12">
        <Container>
          <Link href="/diagnose">
            <Button fullWidth>無料で診断する</Button>
          </Link>
        </Container>
      </section>

      <footer className="border-t border-[var(--color-border)] py-6">
        <Container>
          <p className="text-center text-[11px] text-[var(--color-ink-soft)]">
            本サービスの診断結果は、購入を検討する際の参考情報です。住宅ローンの借入可能額や将来の資産性を保証するものではありません。
          </p>
        </Container>
      </footer>
    </div>
  );
}
