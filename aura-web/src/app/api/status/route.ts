import { NextResponse } from "next/server";
import path from "path";
import fs from "fs";

export async function GET() {
  const modelPath = path.resolve(process.cwd(), "../AuraCore/model.bin");
  const tokPath   = path.resolve(process.cwd(), "../AuraCore/tokenizer.bin");
  const trained   = fs.existsSync(modelPath) && fs.existsSync(tokPath);
  return NextResponse.json({ trained });
}
