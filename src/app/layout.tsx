import type { Metadata } from "next";
import { Noto_Sans_JP } from "next/font/google";
import "./globals.css";

const notoSansJP = Noto_Sans_JP({
  variable: "--font-noto-sans-jp",
  subsets: ["latin"],
  weight: ["400", "500", "700", "900"],
});

export const metadata: Metadata = {
  title: "住まいコンシェルジュAI | あなたに合う家と街をAIが見つけます",
  description:
    "予算や通勤時間だけでなく、暮らし方や将来設計まで分析。約3分の質問に答えるだけで、あなたに合った「街・予算・物件条件」をご提案します。",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="ja" className={`${notoSansJP.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col bg-[var(--color-surface)] text-[var(--color-ink)]">
        {children}
      </body>
    </html>
  );
}
