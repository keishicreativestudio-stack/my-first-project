import type { Answers, BuyerProfile } from "@/types/domain";
import { hasOrWantsChildren } from "@/lib/questions";

function isCommuteFocused(answers: Answers): boolean {
  if (answers.mustConditions?.includes("commute_time")) return true;
  return Boolean(answers.commuteSelf && answers.commuteSelf.maxMinutes <= 30);
}

function isSpaceFocused(answers: Answers): boolean {
  return Boolean(answers.mustConditions?.includes("floor_area"));
}

function isAssetFocused(answers: Answers): boolean {
  return answers.assetPriority === "asset_value_first";
}

function isCarFocused(answers: Answers): boolean {
  return answers.carStatus === "own" || answers.carStatus === "planning";
}

export function buildBuyerProfile(answers: Answers): BuyerProfile {
  const familyFocused = hasOrWantsChildren(answers);
  const commuteFocused = isCommuteFocused(answers);
  const spaceFocused = isSpaceFocused(answers);
  const assetFocused = isAssetFocused(answers);
  const carFocused = isCarFocused(answers);

  let title: string;
  if (assetFocused && commuteFocused) {
    title = "資産性と通勤利便性を両立するアーバンバランスタイプ";
  } else if (familyFocused && spaceFocused) {
    title = "将来の家族構成を見据えた、広さ重視の子育て世代タイプ";
  } else if (commuteFocused && familyFocused) {
    title = "通勤と将来の家族構成を両立したい、バランス重視タイプ";
  } else if (assetFocused) {
    title = "将来の売却・資産性を見据えた、資産価値重視タイプ";
  } else if (spaceFocused || carFocused) {
    title = "住環境の広さとゆとりを重視する、暮らし優先タイプ";
  } else if (commuteFocused) {
    title = "通勤利便性を最優先する、アクセス重視タイプ";
  } else {
    title = "暮らし方に合わせて柔軟に選びたい、バランス重視タイプ";
  }

  const parts: string[] = [];
  if (answers.commuteSelf) {
    parts.push(`「${answers.commuteSelf.stationName}まで${answers.commuteSelf.maxMinutes}分以内」の通勤希望`);
  }
  if (familyFocused) {
    parts.push("将来の家族構成の変化");
  }
  if (assetFocused) {
    parts.push("資産性への意識");
  }
  if (spaceFocused) {
    parts.push("広さへのこだわり");
  }
  if (carFocused) {
    parts.push("車のある暮らし");
  }

  const description =
    parts.length > 0
      ? `${parts.join("、")}を踏まえて、あなたに合うエリアと物件条件をご提案します。`
      : "回答いただいた内容を総合的に分析し、あなたに合うエリアと物件条件をご提案します。";

  return { title, description };
}
