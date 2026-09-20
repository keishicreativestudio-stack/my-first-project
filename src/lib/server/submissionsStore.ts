import "server-only";
import fs from "node:fs";
import path from "node:path";
import type { ContactSubmission } from "@/types/domain";

/**
 * V1用の簡易データストア。
 *
 * Next.jsの開発サーバー(Turbopack)ではRoute HandlerとServer Componentが
 * 別々のモジュールインスタンスとして評価されることがあり、単純な
 * モジュールスコープの配列では状態が共有されない場合がある。
 * そのためV1ではローカルのJSONファイルに書き出す方式にしている。
 *
 * 本番運用ではDB(CRM連携も見据えたテーブル)に置き換える前提のモック実装。
 */
const DATA_DIR = path.join(process.cwd(), ".data");
const DATA_FILE = path.join(DATA_DIR, "submissions.json");

function readAll(): ContactSubmission[] {
  try {
    const raw = fs.readFileSync(DATA_FILE, "utf-8");
    return JSON.parse(raw) as ContactSubmission[];
  } catch {
    return [];
  }
}

function writeAll(submissions: ContactSubmission[]): void {
  fs.mkdirSync(DATA_DIR, { recursive: true });
  fs.writeFileSync(DATA_FILE, JSON.stringify(submissions, null, 2), "utf-8");
}

export function addSubmission(submission: ContactSubmission): void {
  const submissions = readAll();
  submissions.unshift(submission);
  writeAll(submissions);
}

export function getAllSubmissions(): ContactSubmission[] {
  return readAll();
}

export function getSubmissionById(id: string): ContactSubmission | undefined {
  return readAll().find((s) => s.id === id);
}
