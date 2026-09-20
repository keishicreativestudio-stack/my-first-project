import { NextResponse } from "next/server";
import { z } from "zod";
import { contactFormSchema } from "@/lib/validation";
import { addSubmission } from "@/lib/server/submissionsStore";
import { runDiagnosis } from "@/lib/logic/diagnosis";
import type { Answers, ContactSubmission } from "@/types/domain";

const requestSchema = z.object({
  contact: contactFormSchema,
  answers: z.custom<Answers>((v) => typeof v === "object" && v !== null),
});

export async function POST(request: Request) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "リクエストの形式が正しくありません。" }, { status: 400 });
  }

  const parsed = requestSchema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json(
      { error: "入力内容に誤りがあります。", issues: parsed.error.issues },
      { status: 400 }
    );
  }

  const { contact, answers } = parsed.data;

  // 診断結果はクライアントから受け取らず、送信時点の回答からサーバー側で再計算する
  // (診断ロジックはルールベースで決定論的なため、改ざんの心配なく再現できる)
  const result = runDiagnosis(answers);

  const submission: ContactSubmission = {
    id: crypto.randomUUID(),
    submittedAt: new Date().toISOString(),
    contact,
    answers,
    result,
  };

  // V1では送信先(営業システム/CRM/メール等)が未設定のため、安全なモック送信として
  // サーバー内メモリに保存するのみ。Phase 2でCRM/メール連携に差し替える。
  addSubmission(submission);

  return NextResponse.json({ id: submission.id });
}
