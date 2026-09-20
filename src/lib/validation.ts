import { z } from "zod";

export const incomeManYenSchema = z
  .number({ message: "数値で入力してください。" })
  .min(0, "0以上の金額を入力してください。")
  .max(100000, "金額が大きすぎます。万円単位で入力してください。");

export const fundsManYenSchema = z
  .number({ message: "数値で入力してください。" })
  .min(0, "0以上の金額を入力してください。")
  .max(100000, "金額が大きすぎます。万円単位で入力してください。");

export const exactAgeSchema = z
  .number({ message: "数値で入力してください。" })
  .int("整数で入力してください。")
  .min(18, "18歳以上の年齢を入力してください。")
  .max(100, "年齢が大きすぎます。もう一度ご確認ください。");

export const commuteMinutesSchema = z
  .number({ message: "数値で入力してください。" })
  .int("整数で入力してください。")
  .min(1, "1分以上で入力してください。")
  .max(180, "通勤時間が長すぎます。もう一度ご確認ください。");

export const stationNameSchema = z
  .string()
  .min(1, "駅名を入力してください。")
  .max(30, "駅名が長すぎます。");

export const familyMemberCountSchema = z
  .number({ message: "数値で入力してください。" })
  .int("整数で入力してください。")
  .min(1, "1人以上を入力してください。")
  .max(10, "人数が多すぎます。もう一度ご確認ください。");

export const MAX_MUST_CONDITIONS = 3;
export const MAX_CHILDCARE_PRIORITIES = 3;

export const phoneSchema = z
  .string()
  .min(1, "電話番号を入力してください。")
  .regex(/^0\d{9,10}$/, "ハイフンなしの電話番号を入力してください。(例: 09012345678)");

export const emailSchema = z
  .string()
  .min(1, "メールアドレスを入力してください。")
  .email("正しいメールアドレスの形式で入力してください。");

export const contactFormSchema = z.object({
  name: z.string().min(1, "お名前を入力してください。").max(50, "お名前が長すぎます。"),
  phone: phoneSchema,
  email: emailSchema,
  preferredContactMethod: z.enum(["phone", "email", "either"]),
  preferredContactTime: z.enum(["morning", "daytime", "evening", "night", "anytime"]),
  freeText: z.string().max(1000, "1000文字以内で入力してください。").optional(),
});

export type ContactFormErrors = Partial<Record<keyof z.infer<typeof contactFormSchema>, string>>;
