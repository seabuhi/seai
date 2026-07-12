"use client";

import { useState, useRef, useEffect, useCallback } from "react";

// ── Types ──────────────────────────────────────────────────────────────────
interface LogLine { text: string; type: "normal"|"loss"|"success"|"error"|"header"|"gen"; }
interface LossPoint { epoch: number; loss: number; }
interface ChatMsg { role: "user"|"ai"; content: string; streaming?: boolean; }

function classifyLine(line: string): LogLine["type"] {
  if (line.includes("===")) return "header";
  if (line.includes("UGURLU") || line.includes("UĞURLU") || line.includes("OK")) return "success";
  if (line.includes("XETA") || line.includes("XƏTA") || line.includes("error")) return "error";
  if (line.includes("Generasiya") || line.includes("Nəticə")) return "gen";
  if (line.includes("Loss:") || line.includes("loss")) return "loss";
  return "normal";
}
function parseLoss(line: string): LossPoint | null {
  const m = line.match(/Epoch\s+(\d+)\s*\|\s*Loss:\s*([\d.]+)/i);
  return m ? { epoch: parseInt(m[1]), loss: parseFloat(m[2]) } : null;
}

// ── Mini Loss Chart ────────────────────────────────────────────────────────
function LossChart({ points }: { points: LossPoint[] }) {
  if (points.length < 2) return (
    <div className="flex items-center justify-center h-full text-zinc-600 text-sm">Məlumat gözlənilir...</div>
  );
  const W=400,H=120,pad=12;
  const maxE=Math.max(...points.map(p=>p.epoch));
  const maxL=Math.max(...points.map(p=>p.loss));
  const minL=Math.min(...points.map(p=>p.loss));
  const range=maxL-minL||1;
  const toX=(e:number)=>pad+((e/(maxE||1))*(W-pad*2));
  const toY=(l:number)=>H-pad-((l-minL)/range)*(H-pad*2);
  const d=points.map((p,i)=>`${i===0?"M":"L"} ${toX(p.epoch)} ${toY(p.loss)}`).join(" ");
  const fill=d+` L ${toX(maxE)} ${H-pad} L ${pad} ${H-pad} Z`;
  const last=points[points.length-1];
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-full">
      <defs>
        <linearGradient id="lg" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#a78bfa" stopOpacity="0.4"/>
          <stop offset="100%" stopColor="#a78bfa" stopOpacity="0"/>
        </linearGradient>
        <filter id="glow"><feGaussianBlur stdDeviation="2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
      </defs>
      {[0,.25,.5,.75,1].map(t=><line key={t} x1={pad} y1={pad+t*(H-pad*2)} x2={W-pad} y2={pad+t*(H-pad*2)} stroke="#27272a" strokeWidth="1"/>)}
      <path d={fill} fill="url(#lg)"/>
      <path d={d} fill="none" stroke="#a78bfa" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" filter="url(#glow)"/>
      <circle cx={toX(last.epoch)} cy={toY(last.loss)} r="4" fill="#a78bfa" filter="url(#glow)"/>
      <text x={pad} y={H-2} fill="#52525b" fontSize="8">0</text>
      <text x={W-pad-10} y={H-2} fill="#52525b" fontSize="8">{maxE}</text>
      <text x={pad} y={pad+8} fill="#52525b" fontSize="8">{maxL.toFixed(2)}</text>
    </svg>
  );
}

function StatCard({ label, value, sub, color }:{label:string;value:string;sub?:string;color:string}) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4 backdrop-blur-sm">
      <div className="text-xs text-zinc-500 mb-1">{label}</div>
      <div className="text-2xl font-bold" style={{color}}>{value}</div>
      {sub&&<div className="text-xs text-zinc-600 mt-1">{sub}</div>}
    </div>
  );
}

// ── Chat Component ─────────────────────────────────────────────────────────
function ChatPanel() {
  const [chatMode, setChatMode] = useState<"cpp" | "mcts">("cpp");
  const [messages, setMessages] = useState<ChatMsg[]>([
    { role: "ai", content: "Salam! Mən Aura — sıfırdan C++ ilə yazılmış Mini GPT modeliyəm. Bir şey yazın, sizi tamamlayım! (MCTS + LLM rejimini də yoxlaya bilərsiniz)" }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState("");
  const [showDatasetInfo, setShowDatasetInfo] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = useCallback(async () => {
    const text = input.trim();
    if (!text || loading) return;
    setInput("");
    setLoading(true);

    setMessages(prev => [...prev, { role: "user", content: text }]);
    setMessages(prev => [...prev, { role: "ai", content: "", streaming: true }]);

    try {
      if (chatMode === "cpp") {
        const res = await fetch(`/api/generate?seed=${encodeURIComponent(text)}`);
        if (!res.body) throw new Error("No stream");
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buf = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buf += decoder.decode(value, { stream: true });
          const parts = buf.split("\n\n");
          buf = parts.pop() ?? "";
          for (const part of parts) {
            if (!part.startsWith("data:")) continue;
            try {
              const payload = JSON.parse(part.slice(5).trim());
              if (payload.status) {
                setStatusMsg(payload.status);
              }
              if (payload.token !== undefined) {
                setMessages(prev => {
                  const msgs = [...prev];
                  const last = msgs[msgs.length - 1];
                  if (last.role === "ai") {
                    msgs[msgs.length - 1] = { ...last, content: last.content + payload.token };
                  }
                  return msgs;
                });
              }
              if (payload.done) {
                setMessages(prev => {
                  const msgs = [...prev];
                  const last = msgs[msgs.length - 1];
                  if (last.role === "ai") msgs[msgs.length - 1] = { ...last, streaming: false };
                  return msgs;
                });
              }
            } catch {}
          }
        }
      } else {
        setStatusMsg("MCTS zəncirvari axtarış aparılır...");
        const res = await fetch("/api/chat", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ message: text }),
        });
        const data = await res.json();
        
        let fullReply = data.reply || "Aura ilə əlaqə qurularkən xəta baş verdi.";
        let currentText = "";
        let i = 0;
        
        const typeEffect = () => {
          if (i < fullReply.length) {
            const nextChunk = fullReply.slice(i, i + 3);
            currentText += nextChunk;
            i += 3;
            setMessages(prev => {
              const msgs = [...prev];
              const last = msgs[msgs.length - 1];
              if (last.role === "ai") {
                msgs[msgs.length - 1] = { ...last, content: currentText };
              }
              return msgs;
            });
            setTimeout(typeEffect, 10);
          } else {
            setMessages(prev => {
              const msgs = [...prev];
              const last = msgs[msgs.length - 1];
              if (last.role === "ai") msgs[msgs.length - 1] = { ...last, streaming: false };
              return msgs;
            });
            setLoading(false);
            setStatusMsg("");
          }
        };
        typeEffect();
        return;
      }
    } catch (e: unknown) {
      setMessages(prev => {
        const msgs = [...prev];
        msgs[msgs.length - 1] = { role: "ai", content: `Xəta: ${(e as Error).message}` };
        return msgs;
      });
    } finally {
      if (chatMode === "cpp") {
        setLoading(false);
        setStatusMsg("");
      }
    }
  }, [input, loading, chatMode]);

  return (
    <div className="flex flex-col h-full gap-3">
      {/* Mode Selector and Tools */}
      <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-zinc-800/80">
        <div className="flex bg-zinc-900/90 rounded-lg p-0.5 border border-zinc-800">
          <button
            onClick={() => {
              setChatMode("cpp");
              setMessages([
                { role: "ai", content: "C++ rejimindəsiniz. Bu rejim yerli olaraq öyrədilmiş Transformer modelini işlədir." }
              ]);
            }}
            className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-all ${
              chatMode === "cpp"
                ? "bg-violet-600 text-white shadow-md shadow-violet-900/30"
                : "text-zinc-400 hover:text-zinc-200"
            }`}
          >
            ⚡ C++ Mini GPT Core
          </button>
          <button
            onClick={() => {
              setChatMode("mcts");
              setMessages([
                { role: "ai", content: "Aura Reasoning Brain (MCTS + LLM) rejimindəsiniz. Bu rejim Səməd Vurğun da daxil olmaqla mürəkkəb mövzuları axtarış və bilik bazası ilə mükəmməl izah edir!" }
              ]);
            }}
            className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-all ${
              chatMode === "mcts"
                ? "bg-violet-600 text-white shadow-md shadow-violet-900/30"
                : "text-zinc-400 hover:text-zinc-200"
            }`}
          >
            🧠 Aura Reasoning (MCTS + LLM)
          </button>
        </div>

        <button
          onClick={() => setShowDatasetInfo(!showDatasetInfo)}
          className="text-xs font-semibold text-violet-400 hover:text-violet-300 transition-colors flex items-center gap-1 py-1 px-2.5 rounded-lg border border-violet-900/30 bg-violet-950/20"
        >
          📂 Dataset Bələdçisi
        </button>
      </div>

      {/* Dataset Info Drawer/Overlay */}
      {showDatasetInfo && (
        <div className="p-4 rounded-xl border border-zinc-850 bg-zinc-900/95 backdrop-blur-md text-xs text-zinc-300 space-y-3 shadow-2xl animate-fadeIn">
          <div className="flex items-center justify-between border-b border-zinc-850 pb-2">
            <span className="font-bold text-violet-400 text-sm">📂 Dataset Bələdçisi: Hardan və Necə yükləməli?</span>
            <button onClick={() => setShowDatasetInfo(false)} className="text-zinc-500 hover:text-zinc-300 text-sm">✕</button>
          </div>
          <p className="leading-relaxed">
            Modelinizi istənilən mövzuda (məsələn, <strong>Səməd Vurğun</strong>, tibb, hüquq) mükəmməl öyrətmək üçün müvafiq mətn datasetlərini aşağıdakı mənbələrdən əldə edə bilərsiniz:
          </p>
          <ul className="list-disc pl-4 space-y-2 leading-relaxed">
            <li>
              <strong className="text-white">1. Wikipedia Dumps (Tövsiyə olunan):</strong> Wikipedia-nın rəsmi bazasından Azərbaycan dili üzrə tam məqalə arxivlərini (.xml.bz2 formatında) yükləyib xam mətnə (.txt) çevirə bilərsiniz. Həmçinin hər hansı məqaləni (məs. Səməd Vurğun) kopyalayıb birbaşa <code className="bg-zinc-950 px-1 py-0.5 rounded text-violet-300 font-mono">AuraCore/dataset.txt</code>-ə əlavə edə bilərsiniz.
            </li>
            <li>
              <strong className="text-white">2. Hugging Face Datasets:</strong> Hugging Face-də olan Azərbaycan dili korpuslarını (<code className="text-violet-300 font-mono">az-corpus</code>, <code className="text-violet-300 font-mono">azerbaijani-dataset</code>) axtararaq minlərlə dialoq və məqaləni yükləyə bilərsiniz.
            </li>
            <li>
              <strong className="text-white">3. Kaggle:</strong> NLP datasetləri bölməsində xam söhbət və ya sual-cavab cütlüklərini asanlıqla tapmaq olar.
            </li>
            <li>
              <strong className="text-white">4. Xüsusi Generator:</strong> <code className="bg-zinc-950 px-1 py-0.5 rounded text-violet-300 font-mono">AuraCore/generate_dataset.py</code> faylına istədiyiniz sual-cavabları yazaraq <code className="text-zinc-400 font-mono">dataset.txt</code>-i yenidən yarada bilərsiniz.
            </li>
          </ul>
          <p className="text-[10px] text-zinc-500">
            * Yüklədiyiniz faylı Dashboard-dakı fayl yükləmə hissəsindən modelə ötürərək təlimi başlada bilərsiniz.
          </p>
        </div>
      )}

      {/* Info Banner */}
      <div className={`px-3 py-2 rounded-lg text-xs border transition-all ${
        chatMode === "cpp"
          ? "bg-amber-950/40 border-amber-800/40 text-amber-300"
          : "bg-violet-950/30 border-violet-800/40 text-violet-300"
      }`}>
        {chatMode === "cpp" ? (
          <span>⚠ <strong>C++ Mini GPT:</strong> Model yerli C++ Transformer ilə sözü tamamlayır. Uzun və mənalı cavablar üçün onu daha böyük datasetlə təlim edin.</span>
        ) : (
          <span>✨ <strong>Aura Reasoning Engine:</strong> MCTS qərar mexanizmi. Wikipedia axtarışı + Yerli Bilik bazası + Qwen-72B əsaslı ağıllı reasoning zənciri.</span>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-3 pr-1 min-h-0">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed transition-all duration-200
              ${msg.role === "user"
                ? "bg-violet-600 text-white rounded-br-sm shadow-md"
                : "bg-zinc-900 text-zinc-200 rounded-bl-sm border border-zinc-800/80 shadow-sm"
              }`}>
              {msg.role === "ai" && (
                <span className="text-[10px] text-violet-400 font-bold block mb-1">
                  {chatMode === "cpp" ? "Aura GPT (C++ Core)" : "Aura Reasoning Brain (MCTS)"}
                </span>
              )}
              <span className={`whitespace-pre-wrap ${chatMode === "cpp" ? "font-mono text-xs" : "font-sans"}`}>
                {msg.content}
                {msg.streaming && (
                  <span className="inline-block w-1.5 h-3.5 bg-violet-400 ml-0.5 animate-pulse rounded-sm align-middle" />
                )}
              </span>
            </div>
          </div>
        ))}
        {statusMsg && (
          <div className="text-center text-xs text-zinc-500 animate-pulse py-1 font-mono">{statusMsg}</div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="flex gap-2 pt-2 border-t border-zinc-900">
        <input
          id="chat-input"
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === "Enter" && send()}
          placeholder={chatMode === "cpp" ? "Bir söz yazın, C++ mühərriki tamamlasın... (Enter)" : "Mövzu soruşun, məs. Səməd Vurğun kimdir? (Enter)"}
          disabled={loading}
          className="flex-1 bg-zinc-900 border border-zinc-800 rounded-xl px-4 py-2.5 text-sm
                     text-zinc-200 placeholder-zinc-600 outline-none
                     focus:border-violet-600/80 transition-colors disabled:opacity-50"
        />
        <button
          id="btn-chat-send"
          onClick={send}
          disabled={loading || !input.trim()}
          className="px-5 py-2.5 bg-violet-600 hover:bg-violet-500 disabled:opacity-40
                     rounded-xl text-sm font-semibold text-white transition-all shadow-md shadow-violet-900/20"
        >
          {loading ? "···" : "Göndər"}
        </button>
      </div>
    </div>
  );
}

// ── Main Dashboard ─────────────────────────────────────────────────────────
export default function Dashboard() {
  const [tab, setTab] = useState<"train"|"chat">("train");
  const [logs, setLogs] = useState<LogLine[]>([]);
  const [lossPoints, setLossPoints] = useState<LossPoint[]>([]);
  const [running, setRunning] = useState(false);
  const [done, setDone] = useState(false);
  const [generation, setGeneration] = useState<string|null>(null);
  const [stats, setStats] = useState({ params:"–", vocab:"–", dataset:"–", initialLoss:"–", finalLoss:"–" });
  const logRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController|null>(null);

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [logs]);

  const parseLine = useCallback((raw: string) => {
    const pm = raw.match(/Model parameters:\s*(\d+)/i);
    if (pm) setStats(s=>({...s, params: Number(pm[1]).toLocaleString()}));
    const vm = raw.match(/Vocabulary size\s*:\s*(\d+)/i);
    if (vm) setStats(s=>({...s, vocab: vm[1]}));
    const dm = raw.match(/Dataset length\s*:\s*(\d+)/i);
    if (dm) setStats(s=>({...s, dataset: dm[1]}));
    const im = raw.match(/Baslangi[cç] loss[:\s]*([\d.]+)/i) || raw.match(/başlanğıc loss\s*:\s*([\d.]+)/i);
    if (im) setStats(s=>({...s, initialLoss: parseFloat(im[1]).toFixed(4)}));
    const fm = raw.match(/Son loss\s*:\s*([\d.]+)/i);
    if (fm) setStats(s=>({...s, finalLoss: parseFloat(fm[1]).toFixed(4)}));
    const gm = raw.match(/^(.{10,})$/);
    if (raw.includes("---") && gm) setGeneration(raw);
    const pt = parseLoss(raw);
    if (pt) setLossPoints(prev=>[...prev, pt]);
    setLogs(prev=>[...prev, { text: raw, type: classifyLine(raw) }]);
  }, []);

  const runModel = useCallback(async () => {
    setLogs([]); setLossPoints([]); setDone(false); setGeneration(null);
    setStats({ params:"–", vocab:"–", dataset:"–", initialLoss:"–", finalLoss:"–" });
    setRunning(true);
    abortRef.current = new AbortController();
    try {
      const res = await fetch("/api/run", { signal: abortRef.current.signal });
      if (!res.body) throw new Error("No body");
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buf = "";
      while (true) {
        const { done: rd, value } = await reader.read();
        if (rd) break;
        buf += decoder.decode(value, { stream: true });
        const parts = buf.split("\n\n");
        buf = parts.pop() ?? "";
        for (const part of parts) {
          if (!part.startsWith("data:")) continue;
          try {
            const p = JSON.parse(part.slice(5).trim());
            if (p.done) { setDone(true); break; }
            if (p.line) parseLine(p.line);
          } catch {}
        }
      }
    } catch (e: unknown) {
      if ((e as Error).name !== "AbortError")
        setLogs(prev=>[...prev, { text: `⚠ ${(e as Error).message}`, type:"error" }]);
    } finally { setRunning(false); }
  }, [parseLine]);

  const stopModel = () => { abortRef.current?.abort(); setRunning(false); };

  const lineColor: Record<LogLine["type"],string> = {
    header:"text-violet-400 font-bold", success:"text-emerald-400 font-semibold",
    error:"text-red-400", loss:"text-amber-300", gen:"text-cyan-300 font-semibold", normal:"text-zinc-400",
  };
  const reduction = (() => {
    const i=parseFloat(stats.initialLoss), f=parseFloat(stats.finalLoss);
    return (!isNaN(i)&&!isNaN(f)&&i>0) ? (((i-f)/i)*100).toFixed(1) : null;
  })();

  return (
    <div className="min-h-screen bg-[#09090b] text-white font-sans p-4 md:p-6">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            <span className="text-violet-400">Aura</span>
            <span className="text-zinc-300"> Core</span>
            <span className="ml-3 text-sm font-normal text-zinc-500 align-middle">Mini GPT — Chat-Ready</span>
          </h1>
          <p className="text-xs text-zinc-600 mt-0.5">C++ Autograd · BPE Tokenizer · Transformer · Chat Interface</p>
        </div>
        <div className="flex gap-2">
          {/* Tab switcher */}
          <div className="flex rounded-lg border border-zinc-800 overflow-hidden">
            <button onClick={()=>setTab("train")}
              className={`px-4 py-2 text-sm font-medium transition-colors
                ${tab==="train" ? "bg-zinc-800 text-white" : "text-zinc-500 hover:text-zinc-300"}`}>
              🚀 Təlim
            </button>
            <button onClick={()=>setTab("chat")}
              className={`px-4 py-2 text-sm font-medium transition-colors
                ${tab==="chat" ? "bg-zinc-800 text-white" : "text-zinc-500 hover:text-zinc-300"}`}>
              💬 Chat
            </button>
          </div>
          {tab==="train" && (
            <button id="btn-run" onClick={running ? stopModel : runModel}
              className={`px-5 py-2 rounded-lg text-sm font-semibold transition-all
                ${running ? "bg-red-900/60 hover:bg-red-800 text-red-300 border border-red-800"
                          : "bg-violet-600 hover:bg-violet-500 text-white shadow-lg shadow-violet-900/40"}`}>
              {running ? "⏹ Dayandır" : done ? "↺ Yenidən" : "▶ Başlat"}
            </button>
          )}
        </div>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 mb-6">
        <StatCard label="Parametr" value={stats.params} color="#a78bfa" sub="model weights"/>
        <StatCard label="Lüğət" value={stats.vocab} color="#60a5fa" sub="BPE subwords"/>
        <StatCard label="Dataset" value={stats.dataset} color="#34d399" sub="tokens"/>
        <StatCard label="Başlanğıc Loss" value={stats.initialLoss} color="#f87171" sub="cross-entropy"/>
        <StatCard label={`Son Loss${reduction?` (↓${reduction}%)`:""}` } value={stats.finalLoss} color="#4ade80" sub="epoch 1000"/>
      </div>

      {tab === "train" ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Log Terminal */}
          <div className="lg:col-span-2 rounded-xl border border-zinc-800 bg-zinc-950 overflow-hidden">
            <div className="flex items-center gap-2 px-4 py-2 border-b border-zinc-800 bg-zinc-900/50">
              <div className="flex gap-1.5">
                <div className="w-3 h-3 rounded-full bg-red-500/70"/>
                <div className="w-3 h-3 rounded-full bg-yellow-500/70"/>
                <div className="w-3 h-3 rounded-full bg-green-500/70"/>
              </div>
              <span className="text-xs text-zinc-500 ml-2 font-mono">tensor.exe — training</span>
              {running&&<div className="ml-auto flex items-center gap-1.5"><div className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse"/><span className="text-xs text-green-400">işləyir</span></div>}
              {done&&!running&&<div className="ml-auto text-xs text-zinc-500">tamamlandı ✓</div>}
            </div>
            <div ref={logRef} className="h-80 overflow-y-auto p-4 font-mono text-xs leading-relaxed">
              {logs.length===0&&!running&&(
                <div className="text-zinc-700 text-center mt-16">▶ &quot;Başlat&quot; düyməsinə basın</div>
              )}
              {logs.map((l,i)=>(
                <div key={i} className={`whitespace-pre-wrap break-all ${lineColor[l.type]}`}>{l.text}</div>
              ))}
              {running&&<div className="flex items-center gap-1 mt-1"><div className="w-1.5 h-3 bg-violet-400 animate-pulse rounded-sm"/></div>}
            </div>
          </div>

          {/* Right Column */}
          <div className="flex flex-col gap-4">
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4">
              <div className="text-xs text-zinc-500 mb-2 font-medium">📉 Loss Əyrisi</div>
              <div className="h-28"><LossChart points={lossPoints}/></div>
            </div>
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4 flex-1">
              <div className="text-xs text-zinc-500 mb-2 font-medium">✨ Generasiya</div>
              {generation ? (
                <div className="font-mono text-sm text-cyan-300 bg-zinc-950 rounded-lg p-3 leading-relaxed border border-zinc-800 break-all">{generation}</div>
              ) : (
                <div className="text-zinc-700 text-xs text-center mt-4">Təlim bitdikdən sonra burada görünəcək</div>
              )}
            </div>
          </div>
        </div>
      ) : (
        /* CHAT TAB */
        <div className="rounded-xl border border-zinc-800 bg-zinc-950 overflow-hidden" style={{height:"60vh"}}>
          <div className="flex items-center gap-2 px-4 py-2 border-b border-zinc-800 bg-zinc-900/50">
            <div className="flex gap-1.5">
              <div className="w-3 h-3 rounded-full bg-red-500/70"/>
              <div className="w-3 h-3 rounded-full bg-yellow-500/70"/>
              <div className="w-3 h-3 rounded-full bg-green-500/70"/>
            </div>
            <span className="text-xs text-zinc-500 ml-2">Aura GPT — tensor.exe --generate</span>
            <div className="ml-auto flex items-center gap-1.5">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-400"/>
              <span className="text-xs text-emerald-400">online</span>
            </div>
          </div>
          <div className="p-4 flex flex-col" style={{height:"calc(100% - 41px)"}}>
            <ChatPanel/>
          </div>
        </div>
      )}

      {/* Architecture info (always visible at bottom) */}
      <div className="mt-4 grid grid-cols-3 sm:grid-cols-5 gap-1.5 text-[10px]">
        {["Autograd","Tensor Ops","AdamW","Attention","MHA","LayerNorm","Transformer","BPE","Mini GPT","Chat API"].map(l=>(
          <div key={l} className="rounded px-2 py-1 text-center font-medium bg-violet-900/40 text-violet-300 border border-violet-800/40">
            ✓ {l}
          </div>
        ))}
      </div>

      <div className="mt-4 text-center text-[10px] text-zinc-700">
        Aura Core · Phase 9 · C++ Transformer from Scratch · Chat-Ready
      </div>
    </div>
  );
}