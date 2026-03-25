import React, { useState, useEffect, useRef } from 'react';
import ReactFlow, { Background, Controls } from 'reactflow';
import 'reactflow/dist/style.css';

export default function App() {
  const [activeTab, setActiveTab] = useState("AST_MAPPER");
  const [forensicLogs, setForensicLogs] = useState([]);
  const [workspaceFiles, setWorkspaceFiles] = useState([]);

  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isMapping, setIsMapping] = useState(false);

  const [telemetry, setTelemetry] = useState({
    status: "STANDBY", cpu_usage_percent: 0, ram_usage_percent: 0, vram_usage_percent: 0, gpu_temp_c: 0
  });
  const [traceLogs, setTraceLogs] = useState([]);
  const [hitlAlert, setHitlAlert] = useState(null);
  const [astNodes, setAstNodes] = useState([]);
  const [astEdges, setAstEdges] = useState([]);
  const [promptInput, setPromptInput] = useState("");

  const traceEndRef = useRef(null);

  const fetchLogs = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/logs");
      const data = await res.json();
      setForensicLogs(data);
    } catch (err) {}
  };

  const fetchWorkspace = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/workspace");
      const data = await res.json();
      setWorkspaceFiles(data);
    } catch (err) {}
  };

  useEffect(() => {
    if (activeTab === "LOGS") fetchLogs();
    if (activeTab === "WORKSPACE") fetchWorkspace();
  }, [activeTab]);

  useEffect(() => {
    const ws = new WebSocket("ws://127.0.0.1:8000/ws");
    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      switch(msg.type) {
        case "telemetry": setTelemetry(msg.payload); break;
        case "agent_trace":
          setTraceLogs(prev => [...prev.slice(-49), msg.payload]);
          if (msg.payload.agent === "Deployer" && msg.payload.status === "success") fetchWorkspace();
          break;
        case "hitl_alert": setHitlAlert(msg.payload); break;
        case "ast_map":
          setIsMapping(false);
          const formattedNodes = msg.payload.nodes.map((n, i) => ({
            id: n.id,
            position: { x: 250 * (i % 3), y: 100 * Math.floor(i / 3) },
            data: { label: `${n.id} \n(Churn: ${n.churn_score})` },
            style: {
                background: '#131315', padding: '10px',
                color: n.churn_score > 3 ? '#fe00fe' : '#00f3ff',
                border: `2px solid ${n.churn_score > 3 ? '#fe00fe' : '#00f3ff'}`,
                borderRadius: '0px',
                boxShadow: n.churn_score > 3 ? '0 0 15px rgba(254, 0, 254, 0.3)' : '0 0 15px rgba(0, 243, 255, 0.3)',
                fontFamily: 'Space Grotesk', fontSize: '10px', fontWeight: 'bold'
            }
          }));
          setAstNodes(formattedNodes);
          setAstEdges(msg.payload.edges.map((e, i) => ({
            id: `e${i}`, source: e.source, target: e.target, animated: true,
            style: { stroke: '#00f3ff', strokeWidth: 1.5 }
          })));
          setActiveTab("AST_MAPPER");
          break;
        default: break;
      }
    };
    return () => ws.close();
  }, []);

  useEffect(() => { traceEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [traceLogs]);

  const handleDrop = async (e) => {
    e.preventDefault();
    setIsDragging(false);
    const files = e.dataTransfer.files;
    if (files.length === 0) return;

    setIsUploading(true);
    const formData = new FormData();
    formData.append("file", files[0]);

    try {
        const res = await fetch("http://127.0.0.1:8000/ingest", { method: "POST", body: formData });
        const result = await res.json();
        if(result.status === "success") fetchWorkspace();
    } catch (err) { alert("Failed to connect to Intake Forge."); }
    finally { setIsUploading(false); }
  };

  const handleDelete = async (path) => {
      try {
          await fetch("http://127.0.0.1:8000/workspace/delete", {
              method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ path })
          });
          fetchWorkspace();
      } catch (err) {}
  };

  const handleGenerateMap = async () => {
      setIsMapping(true);
      try {
          await fetch("http://127.0.0.1:8000/workspace/map", { method: "POST" });
      } catch (err) {
          setIsMapping(false);
      }
  };

  const renderDial = (value, label, isCritical) => {
    const offset = 364.4 - (364.4 * (value / 100));
    const colorClass = isCritical ? "text-secondary-container" : "text-primary-container";
    return (
      <div className="flex flex-col items-center">
        <div className="relative w-32 h-32 flex items-center justify-center">
          <svg className="w-full h-full -rotate-90">
            <circle className="text-surface-container-highest" cx="64" cy="64" r="58" fill="transparent" strokeWidth="2" />
            <circle className={`transition-all duration-500 ${colorClass}`} cx="64" cy="64" r="58" fill="transparent" stroke="currentColor" strokeWidth="4" strokeDasharray="364.4" strokeDashoffset={offset} />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className={`font-headline text-lg font-bold ${colorClass}`}>{value.toFixed(1)}%</span>
            <span className="font-headline text-[8px] tracking-widest text-on-surface-variant uppercase">{label}</span>
          </div>
        </div>
      </div>
    );
  };

  const renderTree = (nodes) => {
    return nodes.map((node, i) => (
      <div key={i} className="ml-4 mt-2">
        <div className="flex items-center justify-between gap-2 font-mono text-[11px] bg-surface-container-low/50 p-1 border border-outline-variant/10">
          <span className={node.type === "folder" ? "text-secondary-container" : "text-primary-container"}>
            {node.type === "folder" ? "📁" : "📄"} {node.name}
          </span>
          {/* Always visible delete button for mobile/touch users */}
          <button
            onClick={() => handleDelete(node.path)}
            className="text-error border border-error/50 px-2 py-1 text-[8px] uppercase tracking-widest bg-black hover:bg-error/20 active:scale-95 transition-all">
            🗑️ DELETE
          </button>
        </div>
        {node.children && <div className="border-l border-outline-variant/30 ml-2 pl-2">{renderTree(node.children)}</div>}
      </div>
    ));
  };

  return (
    <div className="bg-background text-on-surface font-body min-h-screen selection:bg-primary-container selection:text-on-primary">
      <header className="fixed top-0 w-full z-50 flex justify-between items-center px-6 h-14 bg-[#131315] shadow-[0_1px_0_0_rgba(0,243,255,0.1)]">
        <div className="flex items-center gap-12">
            <div className="text-xl font-black text-[#00f3ff] tracking-tighter font-headline neon-glow-cyan">DEAN_OS_v3.0</div>
            <nav className="hidden lg:flex gap-8 font-headline text-[10px] font-bold tracking-[0.2em] mt-1">
                {["AST_MAPPER", "STAGING", "WORKSPACE", "LOGS", "SETTINGS"].map(tab => (
                    <button key={tab} onClick={() => setActiveTab(tab)} className={`transition-colors pb-4 ${activeTab === tab ? "text-primary-container border-b-2 border-primary-container" : "text-on-surface-variant hover:text-white"}`}>
                        {tab.replace("_", " ")}
                    </button>
                ))}
            </nav>
        </div>
        <div className="flex items-center gap-4">
            <span className="font-headline text-[10px] text-primary-container font-bold tracking-widest">
                {telemetry.status === "HEALTHY" ? "🟢 SYSTEM SECURE" : "🔴 HARDWARE CRITICAL"}
            </span>
        </div>
      </header>

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
        <div className="mt-auto pt-6 border-t border-outline-variant/20">
          <div className="flex flex-col gap-2">
              <input type="text" value={promptInput} onChange={(e) => setPromptInput(e.target.value)} placeholder="Enter system prompt..." className="w-full bg-surface-container-low border-b-2 border-outline-variant focus:border-primary-container text-primary-container font-mono text-[10px] p-2 outline-none"/>
              <button onClick={async () => {
                      if (!promptInput) return;
                      await fetch("http://127.0.0.1:8000/build", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ prompt: promptInput }) });
                      setPromptInput("");
                  }} className="w-full py-3 bg-gradient-to-r from-primary to-primary-container text-on-primary font-headline font-bold text-[10px] tracking-widest uppercase hover:brightness-110 active:scale-95">
                  DEPLOY_AGENT
              </button>
          </div>
        </div>
      </aside>

      <main className="ml-72 mt-14 mb-48 p-8 h-[calc(100vh-14rem)] relative flex flex-col">
        {activeTab === "AST_MAPPER" && (
            <>
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
            </>
        )}

        {activeTab === "LOGS" && (
            <div className="flex-1 flex flex-col h-full">
                <div className="flex justify-between items-end mb-4">
                  <div><h1 className="font-headline text-4xl font-black mb-1">FORENSIC_LEDGER</h1></div>
                  <button onClick={fetchLogs} className="border px-6 py-2 text-[10px] text-primary-container">Refresh_Records</button>
                </div>
                <div className="flex-1 overflow-y-auto bg-surface-container-lowest p-6 font-mono text-[11px] space-y-4">
                    {forensicLogs.map((log, i) => (
                        <div key={i} className="border-b border-outline-variant/20 pb-4 mb-2">
                            <div className="flex gap-4 text-on-surface-variant mb-2">
                                <span>[{new Date(log.timestamp).toLocaleString()}]</span> <span>ID: {log.trace_id}</span>
                                <span className="text-primary-container font-bold">{log.agent_name}</span>
                            </div>
                            <div className={`text-sm ${log.status === 'error' ? 'text-error' : 'text-on-surface'}`}>{log.action}</div>
                            {log.logs && <pre className="mt-3 p-4 bg-[#08080a] text-secondary-container">{log.logs}</pre>}
                        </div>
                    ))}
                </div>
            </div>
        )}

        {activeTab === "WORKSPACE" && (
            <div className="flex-1 flex gap-8 h-full">
                <div className="w-1/2 flex flex-col">
                    <div className="flex justify-between items-end mb-4">
                        <div>
                            <h1 className="font-headline text-4xl font-black uppercase mb-1">PRODUCTION_ENV</h1>
                            <p className="font-headline text-[10px] tracking-[0.2em] text-on-surface-variant">MANUAL_PRUNING_REQUIRED</p>
                        </div>
                        {/* Generate Map Button - Now ALWAYS visible if files exist */}
                        {workspaceFiles.length > 0 && (
                            <button
                                onClick={handleGenerateMap}
                                disabled={isMapping}
                                className="bg-primary-container text-black font-headline font-black text-[12px] tracking-widest px-8 py-4 uppercase transition-all hover:brightness-110 active:scale-95 shadow-[0_0_20px_rgba(0,243,255,0.6)] border-2 border-primary-container">
                                {isMapping ? "MAPPING..." : "GENERATE AST MAP"}
                            </button>
                        )}
                    </div>
                    <div className="flex-1 overflow-y-auto bg-surface-container-lowest border border-outline-variant/20 p-4 terminal-scrollbar">
                        {workspaceFiles.length === 0 ? (
                            <div className="text-on-surface-variant/50 italic font-mono text-[11px]">Workspace is empty. Drop a ZIP to begin.</div>
                        ) : renderTree(workspaceFiles)}
                    </div>
                </div>

                <div className="w-1/2 flex flex-col">
                    <div className="mb-4">
                        <h1 className="font-headline text-4xl font-black mb-1">INTAKE_FORGE</h1>
                        <p className="font-headline text-[10px] tracking-[0.2em] text-on-surface-variant">AIR_GAPPED_EXTRACTION</p>
                    </div>
                    <div
                        onDragOver={(e) => {e.preventDefault(); setIsDragging(true);}}
                        onDragLeave={() => setIsDragging(false)}
                        onDrop={handleDrop}
                        className={`flex-1 flex flex-col items-center justify-center border-2 border-dashed transition-all ${isDragging ? 'border-primary-container bg-primary-container/10' : 'border-outline-variant/50 bg-surface-container-lowest'} ${isUploading ? 'opacity-50' : ''}`}
                    >
                        {isUploading ? (
                            <div className="text-center animate-pulse">
                                <h2 className="font-headline text-lg font-bold text-primary-container uppercase">Extracting...</h2>
                            </div>
                        ) : (
                            <div className="text-center pointer-events-none">
                                <div className="text-outline-variant text-4xl mb-4">📥</div>
                                <h2 className="font-headline text-lg font-bold text-on-surface-variant uppercase tracking-widest">Drop Codebase (.ZIP)</h2>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        )}

        {["STAGING", "SETTINGS"].includes(activeTab) && (
            <div className="flex-1 flex items-center justify-center border-2 border-dashed border-outline-variant/30 bg-surface-container-lowest/50">
                <div className="text-center">
                    <div className="text-primary-container text-4xl mb-4 opacity-50">🚧</div>
                    <h2 className="font-headline text-xl font-bold text-on-surface-variant uppercase tracking-widest">MODULE_UNDER_CONSTRUCTION</h2>
                    <p className="font-mono text-[10px] text-outline-variant mt-2 uppercase tracking-widest">Awaiting deployment...</p>
                </div>
            </div>
        )}
      </main>

      <footer className="fixed bottom-0 left-0 right-0 h-48 bg-[#131315]/90 border-t border-[#3a494b]/30 z-50 p-4 flex flex-col">
        <div className="flex items-center justify-between mb-2 border-b border-outline-variant/10 pb-2 pl-72">
          <span className="font-headline text-[10px] font-bold text-primary-container tracking-widest uppercase">WATERFALL_TRACE</span>
        </div>
        <div className="flex-1 overflow-y-auto terminal-scrollbar font-mono text-[11px] space-y-1 p-2 bg-surface-container-lowest ml-72">
          {traceLogs.map((log, i) => (
            <div key={i} className={log.status === 'error' ? 'text-secondary-container font-bold' : 'text-primary-container'}>
              <span className="opacity-50">[{new Date().toLocaleTimeString()}]</span> [TASK: {log.trace_id}] [AGENT: {log.agent}] {log.action}
            </div>
          ))}
          <div ref={traceEndRef} className="text-primary-container animate-pulse">_</div>
        </div>
      </footer>
    </div>
  );
}
