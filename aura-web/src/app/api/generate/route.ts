import { NextRequest } from "next/server";
import { spawn } from "child_process";
import path from "path";

export const dynamic = "force-dynamic";

export async function GET(req: NextRequest) {
  let rawSeed = req.nextUrl.searchParams.get("seed") ?? "Salam";
  
  // Capitalize first letter to match the dataset exactly
  if (rawSeed.length > 0) {
    rawSeed = rawSeed.charAt(0).toUpperCase() + rawSeed.slice(1);
  }

  const seed = `[USER] ${rawSeed}\n[AURA] `;

  const exePath = path.resolve(
    process.cwd(),
    "../AuraCore/tensor.exe"
  );

  const encoder = new TextEncoder();

  const stream = new ReadableStream({
    start(controller) {
      const env = { ...process.env, PATH: `C:\\msys64\\ucrt64\\bin;${process.env.PATH || ""}` };
      const child = spawn(exePath, ["--generate", seed], {
        cwd: path.dirname(exePath),
        env,
        shell: false,
      });

      let buf = "";
      let accumulatedOutput = "";
      
      child.stdout.on("data", (chunk: Buffer) => {
        buf += chunk.toString();
        const lines = buf.split(/\r?\n/);
        buf = lines.pop() ?? "";
        for (const line of lines) {
          if (line.startsWith("TOKEN:")) {
            const token = line.slice(6)
              .replace(/\\n/g, "\n")
              .replace(/\\r/g, "\r");
              
            accumulatedOutput += token;
            
            // Stop generating if it tries to predict the next user turn
            if (accumulatedOutput.includes("[USER]")) {
              child.kill();
              return;
            }
            
            controller.enqueue(
              encoder.encode(`data: ${JSON.stringify({ token })}\n\n`)
            );
          } else if (line.startsWith("STATUS:")) {
            controller.enqueue(
              encoder.encode(`data: ${JSON.stringify({ status: line.slice(7) })}\n\n`)
            );
          }
        }
      });

      child.stderr.on("data", () => {}); // suppress stderr

      child.on("close", () => {
        controller.enqueue(encoder.encode(`data: ${JSON.stringify({ done: true })}\n\n`));
        controller.close();
      });

      child.on("error", (err) => {
        controller.enqueue(
          encoder.encode(`data: ${JSON.stringify({ error: err.message })}\n\n`)
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
