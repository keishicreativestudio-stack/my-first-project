"use client";

import { useState } from "react";
import Link from "next/link";
import { Container } from "@/components/ui/Container";
import { Button } from "@/components/ui/Button";
import { TextField } from "@/components/diagnose/fields";
import { SingleSelectList } from "@/components/diagnose/fields";
import { useDiagnosisStore } from "@/store/useDiagnosisStore";
import { contactFormSchema, type ContactFormErrors } from "@/lib/validation";
import type { ContactFormInput } from "@/types/domain";

const CONTACT_METHOD_OPTIONS = [
  { value: "phone", label: "電話" },
  { value: "email", label: "メール" },
  { value: "either", label: "どちらでも" },
] as const;

const CONTACT_TIME_OPTIONS = [
  { value: "morning", label: "午前中" },
  { value: "daytime", label: "日中" },
  { value: "evening", label: "夕方" },
  { value: "night", label: "夜間" },
  { value: "anytime", label: "いつでも" },
] as const;

const initialForm: ContactFormInput = {
  name: "",
  phone: "",
  email: "",
  preferredContactMethod: "either",
  preferredContactTime: "anytime",
  freeText: "",
};

export default function ContactPage() {
  const answers = useDiagnosisStore((s) => s.answers);
  const [form, setForm] = useState<ContactFormInput>(initialForm);
  const [errors, setErrors] = useState<ContactFormErrors>({});
  const [status, setStatus] = useState<"idle" | "submitting" | "success" | "error">("idle");
  const [serverError, setServerError] = useState<string | null>(null);

  const patch = (partial: Partial<ContactFormInput>) => setForm((f) => ({ ...f, ...partial }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const result = contactFormSchema.safeParse(form);
    if (!result.success) {
      const nextErrors: ContactFormErrors = {};
      for (const issue of result.error.issues) {
        const key = issue.path[0] as keyof ContactFormErrors;
        if (key && !nextErrors[key]) nextErrors[key] = issue.message;
      }
      setErrors(nextErrors);
      return;
    }
    setErrors({});
    setStatus("submitting");
    setServerError(null);
    try {
      const res = await fetch("/api/contact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ contact: result.data, answers }),
      });
      if (!res.ok) {
        setStatus("error");
        setServerError("送信に失敗しました。時間をおいて再度お試しください。");
        return;
      }
      setStatus("success");
    } catch {
      setStatus("error");
      setServerError("通信エラーが発生しました。ネットワーク環境をご確認ください。");
    }
  };

  if (status === "success") {
    return (
      <div className="flex flex-1 flex-col items-center justify-center px-6 text-center">
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-[var(--color-success)]/10">
          <svg viewBox="0 0 24 24" className="h-7 w-7 fill-[var(--color-success)]">
            <path d="M9 16.2 4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4z" />
          </svg>
        </div>
        <h1 className="mt-5 text-lg font-black text-[var(--color-navy)]">
          お問い合わせを受け付けました
        </h1>
        <p className="mt-2 text-sm leading-relaxed text-[var(--color-ink-soft)]">
          診断結果をもとに、現在販売されている物件を担当者がお探しします。
          <br />
          ご入力いただいたご連絡先に、担当者よりご連絡いたします。
        </p>
        <Link href="/" className="mt-6">
          <Button variant="secondary">トップページに戻る</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col bg-[var(--color-surface)] py-8">
      <Container>
        <h1 className="text-xl font-black text-[var(--color-navy)]">物件を探してもらう</h1>
        <p className="mt-3 rounded-2xl bg-white p-4 text-[13px] leading-relaxed text-[var(--color-ink-soft)] ring-1 ring-[var(--color-border)]">
          ご入力いただく情報は、診断結果をもとに実際の物件をご紹介するためにのみ利用します。
          営業目的以外での第三者提供は行いません。
        </p>

        <form onSubmit={handleSubmit} className="mt-6 space-y-5">
          <TextField
            label="お名前"
            value={form.name}
            onChange={(v) => patch({ name: v })}
            placeholder="例: 山田 太郎"
            error={errors.name}
          />
          <TextField
            label="電話番号"
            value={form.phone}
            onChange={(v) => patch({ phone: v })}
            placeholder="例: 09012345678"
            error={errors.phone}
          />
          <TextField
            label="メールアドレス"
            value={form.email}
            onChange={(v) => patch({ email: v })}
            placeholder="例: taro@example.com"
            error={errors.email}
          />

          <div>
            <p className="mb-2 text-sm font-bold text-[var(--color-ink)]">希望連絡方法</p>
            <SingleSelectList
              options={CONTACT_METHOD_OPTIONS}
              value={form.preferredContactMethod}
              onChange={(v) => patch({ preferredContactMethod: v })}
            />
          </div>

          <div>
            <p className="mb-2 text-sm font-bold text-[var(--color-ink)]">希望連絡時間帯</p>
            <SingleSelectList
              options={CONTACT_TIME_OPTIONS}
              value={form.preferredContactTime}
              onChange={(v) => patch({ preferredContactTime: v })}
            />
          </div>

          <div>
            <label
              htmlFor="contact-free-text"
              className="mb-1.5 block text-sm font-bold text-[var(--color-ink)]"
            >
              自由記入欄(任意)
            </label>
            <textarea
              id="contact-free-text"
              value={form.freeText}
              onChange={(e) => patch({ freeText: e.target.value })}
              rows={4}
              placeholder="ご要望などあればご記入ください"
              className="w-full rounded-xl border border-[var(--color-border)] px-4 py-3 text-[15px] focus:outline-none focus:ring-2 focus:ring-[var(--color-navy)]/30"
            />
            {errors.freeText && (
              <p className="mt-1.5 text-xs font-medium text-[var(--color-danger)]">
                {errors.freeText}
              </p>
            )}
          </div>

          {serverError && (
            <p role="alert" className="text-sm font-medium text-[var(--color-danger)]">
              {serverError}
            </p>
          )}

          <Button type="submit" fullWidth disabled={status === "submitting"}>
            {status === "submitting" ? "送信中…" : "この内容で送信する"}
          </Button>
        </form>
      </Container>
    </div>
  );
}
