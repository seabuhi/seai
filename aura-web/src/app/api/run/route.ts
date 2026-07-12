import { NextRequest } from "next/server";
import { spawn } from "child_process";
import path from "path";

export const dynamic = "force-dynamic";

export async function GET(req: NextRequest) {
  const exePath = path.resolve(
    process.cwd(),
    "../AuraCore/tensor.exe"
  );

  const encoder = new TextEncoder();

  const stream = new ReadableStream({
    start(controller) {
      const env = { ...process.env, PATH: `C:\\msys64\\ucrt64\\bin;${process.env.PATH || ""}` };
      const child = spawn(exePath, [], {
        cwd: path.dirname(exePath),
        env,
        shell: false,
      });

      child.stdout.on("data", (chunk: Buffer) => {
        const lines = chunk.toString().split(/\r?\n/);
        for (const line of lines) {
          if (line.trim()) {
            controller.enqueue(
              encoder.encode(`data: ${JSON.stringify({ line })}\n\n`)
            );
          }
        }
      });

      child.stderr.on("data", (chunk: Buffer) => {
        const line = chunk.toString().trim();
        if (line) {
          controller.enqueue(
            encoder.encode(`data: ${JSON.stringify({ line, error: true })}\n\n`)
          );
        }
      });

      child.on("close", (code) => {
        controller.enqueue(
          encoder.encode(
            `data: ${JSON.stringify({ done: true, code })}\n\n`
          )
        );
        controller.close();
      });

      child.on("error", (err) => {
        controller.enqueue(
          encoder.encode(
            `data: ${JSON.stringify({ line: `Process error: ${err.message}`, error: true })}\n\n`
          )
        );
        controller.close();
      });
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    },
  });
}
