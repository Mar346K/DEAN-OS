import React, { useState, useEffect, useRef } from 'react';
import ReactFlow, { Background, Controls } from 'reactflow';
import 'reactflow/dist/style.css';

export default function App() {
  // --- STATE MANAGEMENT ---
  const [telemetry, setTelemetry] = useState({
    status: "STANDBY", cpu_usage_percent: 0, ram_usage_percent: 0, vram_usage_percent: 0, gpu_temp_c: 0
  });
  const [traceLogs, setTraceLogs] = useState([]);
  const [hitlAlert, setHitlAlert] = useState(null);
  const [astNodes, setAstNodes] = useState([]);
  const [astEdges, setAstEdges] = useState([]);
  const [promptInput, setPromptInput] = useState("");

  const traceEndRef = useRef(null);

  // --- WEBSOCKET CONNECTION ---
  useEffect(() => {
    const ws = new WebSocket("ws://127.0.0.1:8000/ws");

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);

      switch(msg.type) {
        case "telemetry":
          setTelemetry(msg.payload);
          break;
        case "agent_trace":
          setTraceLogs(prev => [...prev.slice(-49), msg.payload]);
          break;
        case "hitl_alert":
          setHitlAlert(msg.payload);
          break;
        case "ast_map":
          const formattedNodes = msg.payload.nodes.map((n, i) => ({
            id: n.id,
            position: { x: 250 * (i % 3), y: 100 * Math.floor(i / 3) },
            data: { label: `${n.id} (Churn: ${n.churn_score})` },
            style: {
                background: n.churn_score > 3 ? '#131315' : '#131315',
                color: n.churn_score > 3 ? '#fe00fe' : '#00f3ff',
                border: `2px solid ${n.churn_score > 3 ? '#fe00fe' : '#00f3ff'}`,
                borderRadius: '0px',
                boxShadow: n.churn_score > 3 ? '0 0 15px rgba(254, 0, 254, 0.3)' : '0 0 15px rgba(0, 243, 255, 0.3)',
                fontFamily: 'Space Grotesk', fontSize: '10px', fontWeight: 'bold'
            }
          }));
          setAstNodes(formattedNodes);
          setAstEdges(msg.payload.edges.map((e, i) => ({
            id: `e${i}`, source: e.source, target: e.target, animated: true, style: { stroke: '#3a494b' }
          })));
          break;
        default:
          break;
      }
    };

    return () => ws.close();
  }, []);

  // Auto-scroll the terminal
  useEffect(() => {
    traceEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [traceLogs]);

  // --- UI HELPER ---
  const renderDial = (value, label, isCritical) => {
    const offset = 364.4 - (364.4 * (value / 100));
    const colorClass = isCritical ? "text-secondary-container" : "text-primary-container";
    return (
      <div className="flex flex-col items-center">
        <div className="relative w-32 h-32 flex items-center justify-center">
          <svg className="w-full h-full -rotate-90">
            <circle className="text-surface-container-highest" cx="64" cy="64" r="58" fill="transparent" stroke="currentColor" strokeWidth="2" />
            <circle className={`transition-all duration-500 ease-out ${colorClass}`} cx="64" cy="64" r="58" fill="transparent" stroke="currentColor" strokeWidth="4" strokeDasharray="364.4" strokeDashoffset={offset} />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className={`font-headline text-lg font-bold ${colorClass}`}>{value.toFixed(1)}%</span>
            <span className="font-headline text-[8px] tracking-widest text-on-surface-variant uppercase">{label}</span>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="bg-background text-on-surface font-body min-h-screen selection:bg-primary-container selection:text-on-primary">
      {/* TOP NAV */}
      <header className="fixed top-0 w-full z-50 flex justify-between items-center px-6 h-14 bg-[#131315] shadow-[0_1px_0_0_rgba(0,243,255,0.1)]">
        <div className="text-xl font-black text-[#00f3ff] tracking-tighter font-headline neon-glow-cyan">DEAN_OS_v3.0</div>
        <div className="flex items-center gap-4">
            <span className="font-headline text-[10px] text-primary-container font-bold tracking-widest">
                {telemetry.status === "HEALTHY" ? "🟢 SYSTEM SECURE" : "🔴 HARDWARE CRITICAL"}
            </span>
        </div>
      </header>

      {/* TELEMETRY SIDEBAR */}
      <aside className="fixed left-0 top-14 bottom-48 w-72 z-40 flex flex-col bg-[#0e0e10] border-r border-[#3a494b]/20 p-6 overflow-y-auto">
        <div className="flex items-center gap-3 mb-8">
          <div className="w-2 h-2 rounded-full bg-primary-container neon-glow-cyan"></div>
          <span className="font-headline font-bold text-[10px] tracking-widest uppercase text-on-surface-variant">AETHELGARD_TELEMETRY</span>
        </div>
        <div className="space-y-8">
          {renderDial(telemetry.cpu_usage_percent, "CPU_LOAD", false)}
          {renderDial(telemetry.ram_usage_percent, "RAM_UTIL", telemetry.ram_usage_percent > 85)}
          {renderDial(telemetry.vram_usage_percent, "VRAM_POOL", telemetry.vram_usage_percent > 90)}
        </div>

        {/* NEW: Command Input & Deploy Button */}
        <div className="mt-auto pt-6 border-t border-outline-variant/20">
          <div className="flex justify-between items-center mb-4">
            <span className="font-headline text-[10px] text-on-surface-variant">GPU_TEMP</span>
            <span className="font-headline text-[10px] text-primary-container font-bold">{telemetry.gpu_temp_c}C</span>
          </div>

          <div className="flex flex-col gap-2">
              <input
                  type="text"
                  value={promptInput}
                  onChange={(e) => setPromptInput(e.target.value)}
                  placeholder="Enter system prompt..."
                  className="w-full bg-surface-container-low border-b-2 border-outline-variant focus:border-primary-container focus:ring-0 text-primary-container font-mono text-[10px] p-2 outline-none"
              />
              <button
                  onClick={async () => {
                      if (!promptInput) return;
                      await fetch("http://127.0.0.1:8000/build", {
                          method: "POST",
                          headers: { "Content-Type": "application/json" },
                          body: JSON.stringify({ prompt: promptInput })
                      });
                      setPromptInput(""); // clear after sending
                  }}
                  className="w-full py-3 bg-gradient-to-r from-primary to-primary-container text-on-primary font-headline font-bold text-[10px] tracking-widest uppercase transition-all hover:brightness-110 active:scale-95">
                  DEPLOY_AGENT
              </button>
          </div>
        </div>
      </aside>

      {/* BLAST RADIUS GRAPH */}
      <main className="ml-72 mt-14 mb-48 p-8 h-[calc(100vh-14rem)] relative flex flex-col">
        <div className="flex justify-between items-end mb-4">
          <div>
            <h1 className="font-headline text-4xl font-black text-on-surface tracking-tighter uppercase mb-1">BLAST_RADIUS</h1>
            <p className="font-headline text-[10px] tracking-[0.2em] text-on-surface-variant uppercase">FORENSIC_PIM_VISUALIZER</p>
          </div>
        </div>
        <div className="flex-1 bg-surface-container-lowest border border-outline-variant/10 relative">
          <ReactFlow nodes={astNodes} edges={astEdges} fitView>
            <Background color="#3a494b" gap={20} size={1} />
            <Controls className="bg-surface border-outline-variant text-primary-container fill-primary-container" />
          </ReactFlow>
        </div>
      </main>

      {/* WATERFALL TRACE */}
      <footer className="fixed bottom-0 left-0 right-0 h-48 bg-[#131315]/90 backdrop-blur-xl border-t border-[#3a494b]/30 z-50 p-4 flex flex-col">
        <div className="flex items-center justify-between mb-2 border-b border-outline-variant/10 pb-2 pl-72">
          <span className="font-headline text-[10px] font-bold text-primary-container tracking-widest uppercase">WATERFALL_TRACE</span>
        </div>
        <div className="flex-1 overflow-y-auto terminal-scrollbar font-mono text-[11px] space-y-1 p-2 bg-surface-container-lowest ml-72">
          {traceLogs.length === 0 && <div className="text-on-surface-variant/50 italic">Awaiting swarm dispatch...</div>}
          {traceLogs.map((log, i) => (
            <div key={i} className={log.status === 'error' ? 'text-secondary-container font-bold' : 'text-primary-container'}>
              <span className="opacity-50">[{new Date().toLocaleTimeString()}]</span> [TASK: {log.trace_id}] [AGENT: {log.agent}] {log.action}
            </div>
          ))}
          <div ref={traceEndRef} className="text-primary-container animate-pulse">_</div>
        </div>
      </footer>

      {/* HITL MODAL */}
      {hitlAlert && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-6 bg-surface-container-lowest/80 backdrop-blur-md">
          <div className="w-full max-w-xl bg-surface border-2 border-secondary-container neon-glow-magenta shadow-2xl">
            <div className="bg-secondary-container p-3 flex justify-between items-center">
              <span className="font-headline font-black text-xs tracking-widest text-on-secondary">HITL_ALERT_OVERRIDE</span>
              <span className="font-headline text-[9px] text-on-secondary font-bold">TASK: {hitlAlert.trace_id}</span>
            </div>
            <div className="p-6">
              <div className="mb-4 bg-surface-container-high p-4 border-l-2 border-secondary-container">
                <div className="font-headline text-lg font-bold text-on-surface mb-1">{hitlAlert.filename} (Attempt {hitlAlert.attempt})</div>
                <code className="block font-mono text-[10px] text-secondary-container bg-black/40 p-2 mt-2 break-words">
                  {hitlAlert.error_traceback}
                </code>
              </div>
              <textarea
                className="w-full bg-surface-container-low border-b-2 border-outline-variant focus:border-secondary-container focus:ring-0 text-primary-container font-mono text-xs p-4 h-24 outline-none resize-none mb-4"
                placeholder="Enter fix implementation here..."
                id="hitl-input"
              />
              <div className="flex gap-4">
                <button
                  onClick={async () => {
                    const hintInput = document.getElementById('hitl-input').value;
                    if (!hintInput) return;

                    // Fire the human hint back to the Orchestrator
                    await fetch("http://127.0.0.1:8000/hitl/resolve", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            filename: hitlAlert.filename,
                            hint: hintInput,
                            error_traceback: hitlAlert.error_traceback
                        })
                    });

                    setHitlAlert(null); // Dismiss the modal
                  }}
                  className="flex-1 bg-secondary-container text-on-secondary font-headline font-bold text-[10px] tracking-[0.2em] py-3 uppercase hover:brightness-110 active:scale-95"
                >
                  SUBMIT_FIX
                </button>
                <button
                  onClick={() => setHitlAlert(null)}
                  className="px-6 border border-outline-variant text-on-surface-variant font-headline font-bold text-[10px] tracking-[0.2em] py-3 uppercase hover:bg-white/5 active:scale-95"
                >
                  QUARANTINE
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
