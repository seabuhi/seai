import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function POST(req: NextRequest) {
  try {
    const { message } = await req.json();
    
    const response = await fetch("http://localhost:8000/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ message }),
      // Keep timeout reasonable so it fails quickly if backend is down
      signal: AbortSignal.timeout(10000), 
    });
    
    if (!response.ok) {
      throw new Error(`Python API responded with status ${response.status}`);
    }
    
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error: any) {
    console.error("API Proxy Error:", error);
    
    return NextResponse.json({
      reply: "⚠ Aura Reasoning Brain (Python) ilə əlaqə qurulmadı.\n\n" +
             "Bu rejimin işləməsi üçün Python FastAPI serverinin 8000 portunda aktiv olması lazımdır.\n\n" +
             "İşə salmaq üçün terminalda icra edin:\n" +
             "python AuraBrain/api/main.py"
    }, { status: 200 });
  }
}
