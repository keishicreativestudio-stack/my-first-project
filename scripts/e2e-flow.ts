/**
 * 実ブラウザ(スマホ幅)で主要フローを操作して確認するスクリプト。
 * 事前に `npm run dev` でサーバーを起動しておくこと。
 * 実行: npx tsx scripts/e2e-flow.ts
 */
import { chromium, devices } from "playwright";
import path from "node:path";
import fs from "node:fs";

const BASE_URL = "http://localhost:3000";
const SHOT_DIR = path.join(process.cwd(), "scripts", "screenshots");

async function main() {
  fs.mkdirSync(SHOT_DIR, { recursive: true });
  const browser = await chromium.launch({
    executablePath: "/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
  });
  const context = await browser.newContext({
    ...devices["iPhone 13"],
  });
  const page = await context.newPage();

  const errors: string[] = [];
  const assert = (cond: boolean, message: string) => {
    if (!cond) errors.push(message);
    console.log(cond ? `OK: ${message}` : `NG: ${message}`);
  };

  const checkNoHorizontalScroll = async (label: string) => {
    const { scrollW, clientW } = await page.evaluate(() => ({
      scrollW: document.documentElement.scrollWidth,
      clientW: document.documentElement.clientWidth,
    }));
    assert(scrollW <= clientW + 1, `横スクロールが発生していない (${label}) scrollW=${scrollW} clientW=${clientW}`);
  };

  // ---- トップページ ----
  await page.goto(BASE_URL + "/");
  await page.waitForSelector("text=あなたに合う家と街を");
  await checkNoHorizontalScroll("top");
  await page.screenshot({ path: path.join(SHOT_DIR, "01-top.png") });

  await page.getByRole("link", { name: "無料で診断する" }).first().click();
  await page.waitForURL("**/diagnose");

  const clickOption = async (label: string) => {
    const radio = page.getByRole("radio", { name: label, exact: true });
    if (await radio.count()) {
      await radio.first().click();
      return;
    }
    await page.getByRole("button", { name: label, exact: true }).first().click();
  };
  const fillNumber = async (labelText: string, value: string) => {
    const label = page.locator("label", { hasText: labelText }).first();
    const forId = await label.getAttribute("for");
    await page.locator(`#${forId}`).fill(value);
  };
  const fillText = async (labelText: string, value: string) => {
    const label = page.locator("label", { hasText: labelText }).first();
    const forId = await label.getAttribute("for");
    await page.locator(`#${forId}`).fill(value);
  };
  const next = () => page.getByRole("button", { name: /次へ|診断結果を見る/ }).click();

  // Q1 family_type
  await page.waitForSelector("text=この家には、どなたと住む予定ですか？");
  await clickOption("夫婦・パートナー＋子ども");
  await fillNumber("同居予定の人数", "4");
  await checkNoHorizontalScroll("diagnose-q1");
  await next();

  // Q2 future_family
  await page.waitForSelector("text=5〜10年後の暮らし");
  await clickOption("今と大きく変わらない予定");
  await next();

  // Q3 age
  await page.waitForSelector("text=年代を教えてください。");
  await clickOption("40代");
  await next();

  // Q4 income (self + partner because couple_with_children)
  await page.waitForSelector("text=世帯年収を教えてください。");
  await fillNumber("本人の年収", "600");
  await fillNumber("配偶者・パートナーの年収", "300");
  await next();

  // Q5 funds
  await page.waitForSelector("text=自己資金を教えてください。");
  await fillNumber("住宅購入に使える自己資金", "800");
  await fillNumber("購入後も手元に残しておきたい現金", "200");
  await next();

  // Q6 other loans
  await page.waitForSelector("text=住宅ローン以外の借入");
  await clickOption("なし");
  await next();

  // Q7 monthly budget
  await page.waitForSelector("text=毎月の住宅費は");
  await clickOption("25万円");
  await next();

  // Q8 commute
  await page.waitForSelector("text=通勤先や希望の通勤時間");
  await fillText("勤務先の最寄駅", "東京駅");
  await fillNumber("希望する通勤時間", "45");
  // partner section should also show since couple_with_children has partner
  const partnerStationLabels = page.locator("label", { hasText: "勤務先の最寄駅" });
  await expectCount(partnerStationLabels, 2);
  const partnerStationId = await partnerStationLabels.nth(1).getAttribute("for");
  await page.locator(`#${partnerStationId}`).fill("新宿駅");
  const partnerMinuteLabels = page.locator("label", { hasText: "希望する通勤時間" });
  const partnerMinuteId = await partnerMinuteLabels.nth(1).getAttribute("for");
  await page.locator(`#${partnerMinuteId}`).fill("40");
  await clickOption("同じくらい");
  await checkNoHorizontalScroll("diagnose-commute");
  await next();

  // Q9 leisure
  await page.waitForSelector("text=休日はどのように過ごすことが多いですか？");
  await clickOption("公園・自然");
  await clickOption("子どもと遊ぶ");
  await next();

  // Q10 town preference sliders
  await page.waitForSelector("text=理想の街の雰囲気");
  const sliders = page.locator('input[type="range"]');
  await expectCount(sliders, 5);
  for (let i = 0; i < 5; i++) {
    await sliders.nth(i).evaluate((el: HTMLInputElement, val) => {
      const nativeSetter = Object.getOwnPropertyDescriptor(
        window.HTMLInputElement.prototype,
        "value"
      )?.set;
      nativeSetter?.call(el, String(val));
      el.dispatchEvent(new Event("input", { bubbles: true }));
    }, 2 + i);
  }
  await next();

  // Q11 childcare (conditional - should appear because couple_with_children)
  await page.waitForSelector("text=子育てで特に重視したいものを選んでください。");
  await clickOption("保育環境");
  await clickOption("公園");
  await clickOption("治安");
  await next();

  // Q12 car
  await page.waitForSelector("text=車についてお聞かせください。");
  await clickOption("現在所有している");
  await next();

  // Q13 property kind
  await page.waitForSelector("text=現在イメージしている住宅タイプ");
  await clickOption("中古戸建");
  await clickOption("中古");
  await next();

  // Q14 asset priority
  await page.waitForSelector("text=住み心地と将来の資産性");
  await clickOption("バランス");
  await next();

  // Q15 future ownership
  await page.waitForSelector("text=将来どうする可能性");
  await clickOption("長く住み続けたい");
  await next();

  // Q16 must conditions
  await page.waitForSelector("text=どうしても譲れないもの");
  await clickOption("広さ");
  await clickOption("子育て環境");
  await clickOption("価格");
  await checkNoHorizontalScroll("diagnose-last");
  await next();

  // ---- Result page ----
  await page.waitForURL("**/result");
  await page.waitForSelector("text=あなたの住宅購入タイプ");
  await checkNoHorizontalScroll("result");
  await page.screenshot({ path: path.join(SHOT_DIR, "02-result.png"), fullPage: true });

  assert(await page.getByText("借入可能額の参考目安").isVisible(), "予算セクションが表示される");
  assert(
    await page.getByRole("heading", { name: "あなたに合うエリア" }).isVisible(),
    "エリアセクションが表示される"
  );
  assert((await page.getByText(/マッチ度/).count()) === 5, "上位エリアが5件表示される");
  assert(
    await page.getByRole("heading", { name: "おすすめの物件条件" }).isVisible(),
    "おすすめ物件条件セクションが表示される"
  );
  assert((await page.getByText(/プラン$/).count()) >= 3, "3プランが表示される");

  // ---- Contact flow ----
  await page.getByRole("link", { name: "この条件で実際に買える物件を見てみる" }).click();
  await page.waitForURL("**/contact");
  await checkNoHorizontalScroll("contact");
  await fillText("お名前", "テスト太郎");
  await fillText("電話番号", "09012345678");
  await fillText("メールアドレス", "test@example.com");
  await page.screenshot({ path: path.join(SHOT_DIR, "03-contact.png") });
  await page.getByRole("button", { name: "この内容で送信する" }).click();
  await page.waitForSelector("text=お問い合わせを受け付けました");
  assert(true, "問い合わせ送信が成功する");

  // ---- Admin ----
  await page.goto(BASE_URL + "/admin");
  await page.waitForSelector("text=テスト太郎 様");
  assert(
    (await page.getByText("テスト太郎 様").count()) >= 1,
    "管理画面に問い合わせが表示される"
  );
  await page.screenshot({ path: path.join(SHOT_DIR, "04-admin.png") });

  await browser.close();

  if (errors.length > 0) {
    console.error("\n失敗した項目:", errors);
    process.exit(1);
  }
  console.log("\n全項目OK");
}

async function expectCount(locator: ReturnType<import("playwright").Page["locator"]>, count: number) {
  const actual = await locator.count();
  if (actual !== count) {
    throw new Error(`期待した要素数と異なります: expected=${count} actual=${actual}`);
  }
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
