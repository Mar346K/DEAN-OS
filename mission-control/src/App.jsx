import React, { useState, useEffect, useRef } from 'react';
import ReactFlow, { Background, Controls } from 'reactflow';
import 'reactflow/dist/style.css';

export default function App() {
  const [activeTab, setActiveTab] = useState("SETTINGS");
  const [forensicLogs, setForensicLogs] = useState([]);
  const [workspaceFiles, setWorkspaceFiles] = useState([]);

  // --- NEW: Vault Files State ---
  const [vaultFiles, setVaultFiles] = useState([]);

  const [selectedPaths, setSelectedPaths] = useState(new Set());
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isMapping, setIsMapping] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const [outputFiles, setOutputFiles] = useState([]);
  const [activeFilePath, setActiveFilePath] = useState(null);
  const [activeFileContent, setActiveFileContent] = useState("");
  const [activeError, setActiveError] = useState(null);
  const [isSaving, setIsSaving] = useState(false);

  const [validationLogs, setValidationLogs] = useState([]);
  const [quarantineFiles, setQuarantineFiles] = useState([]);
  const validationLogEndRef = useRef(null);

  // --- FINOPS & TELEMETRY STATE ---
  const [telemetry, setTelemetry] = useState({ status: "STANDBY", cpu_usage_percent: 0, ram_usage_percent: 0, vram_usage_percent: 0, gpu_temp_c: 0 });
  const [geminiQuota, setGeminiQuota] = useState(0); // Max 15
  const [rushMode, setRushMode] = useState(false);

  // --- ORACLE CHAT STATE ---
  const [chatHistory, setChatHistory] = useState([
      { role: "oracle", text: "Oracle initialized. My context window is locked to your current tab. How can I assist the Swarm?" }
  ]);
  const [chatInput, setChatInput] = useState("");
  const chatEndRef = useRef(null);

  const [healthLogs, setHealthLogs] = useState("");
  const [activeLogService, setActiveLogService] = useState("api");

  const [traceLogs, setTraceLogs] = useState([]);
  const [astNodes, setAstNodes] = useState([]);
  const [astEdges, setAstEdges] = useState([]);
  const [promptInput, setPromptInput] = useState("");
  const [isDeploying, setIsDeploying] = useState(false);
  const traceEndRef = useRef(null);

  const [keys, setKeys] = useState({ openai: "", anthropic: "", gemini: "", openrouter: "" });
  const [keyStatus, setKeyStatus] = useState({ openai: "UNSEALED", anthropic: "UNSEALED", gemini: "UNSEALED" });
  const [budget, setBudget] = useState(1.00);
  const [budgetStatus, setBudgetStatus] = useState("SYNCED");

  const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

  // --- THE WATERFALL FIX ---
  const fetchLogs = async () => {
    try {
      const res = await fetch(`${API_BASE}/logs`);
      const data = await res.json();
      setForensicLogs(data);

      const persistentTraces = data.slice(0, 50).reverse().map(l => ({
          trace_id: l.trace_id,
          agent: l.agent_name,
          action: l.action,
          status: l.status,
          timestamp: l.timestamp
      }));
      setTraceLogs(persistentTraces);
    } catch (err) {}
  };

  const fetchWorkspace = async () => {
    try {
      const res = await fetch(`${API_BASE}/workspace`);
      const data = await res.json();
      setWorkspaceFiles(data);
    } catch (err) {}
  };

  const fetchOutputTree = async () => {
    try {
      const res = await fetch(`${API_BASE}/output/tree`);
      const data = await res.json();
      setOutputFiles(data);
    } catch (err) {}
  };

  // --- NEW: Fetch Vault Tree ---
  const fetchVaultTree = async () => {
      try {
          const res = await fetch(`${API_BASE}/vault/tree`);
          const data = await res.json();
          setVaultFiles(data);
      } catch (err) {}
  };

  const fetchHealthLogs = async (service) => {
    setActiveLogService(service);
    setHealthLogs("Fetching logs from Docker Daemon...");
    try {
        const res = await fetch(`${API_BASE}/system/logs/${service}`);
        const data = await res.json();
        setHealthLogs(data.logs);
    } catch (err) {
        setHealthLogs("Fatal error connecting to API: " + err.message);
    }
  };

  useEffect(() => {
    if (activeTab === "LOGS") fetchLogs();
    if (activeTab === "WORKSPACE") fetchWorkspace();
    if (activeTab === "FACTORY_FLOOR") fetchOutputTree();
    if (activeTab === "RELEASE_VAULT") fetchVaultTree();
    if (activeTab === "SYSTEM_HEALTH") fetchHealthLogs(activeLogService);
  }, [activeTab]);

  useEffect(() => {
    const wsUrl = API_BASE.replace(/^http/, "ws") + "/ws";
    const ws = new WebSocket(wsUrl);
    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      switch(msg.type) {
        case "telemetry": setTelemetry(msg.payload); break;
        case "quota_update": setGeminiQuota(msg.payload.rpm); break;
        case "agent_trace":
          setTraceLogs(prev => [...prev.slice(-49), msg.payload]);
          if (msg.payload.agent === "Deployer" && msg.payload.status === "success") fetchWorkspace();
          setValidationLogs(prev => [...prev.slice(-99), {
              time: new Date().toLocaleTimeString(),
              agent: msg.payload.agent,
              action: msg.payload.action,
              status: msg.payload.status
          }]);
          break;
        case "hitl_alert":
          setQuarantineFiles(prev => {
              if (prev.find(f => f.filename === msg.payload.filename)) return prev;
              return [...prev, msg.payload];
          });
          break;
        case "staging_log":
          setValidationLogs(prev => [...prev.slice(-99), {
              time: new Date().toLocaleTimeString(),
              agent: "System",
              action: msg.payload.text,
              status: msg.payload.type === "stderr" ? "error" : "info"
          }]);
          break;
        case "ast_map":
          setIsMapping(false);
          const formattedNodes = msg.payload.nodes.map((n, i) => ({
            id: n.id,
            position: { x: 300 * (i % 3), y: 150 * Math.floor(i / 3) },
            data: { label: `${n.id}\n(Churn: ${n.churn_score})` },
            style: {
                background: '#131315', padding: '15px',
                color: n.churn_score > 3 ? '#fe00fe' : '#00f3ff',
                border: `2px solid ${n.churn_score > 3 ? '#fe00fe' : '#00f3ff'}`,
                borderRadius: '0px',
                boxShadow: n.churn_score > 3 ? '0 0 15px rgba(254, 0, 254, 0.3)' : '0 0 15px rgba(0, 243, 255, 0.3)',
                fontFamily: 'Space Grotesk', fontSize: '12px', fontWeight: 'bold'
            }
          }));
          setAstNodes(formattedNodes);
          setAstEdges(msg.payload.edges.map((e, i) => ({
            id: `e${i}`, source: e.source, target: e.target, animated: true,
            style: { stroke: '#00f3ff', strokeWidth: 2 }
          })));
          setActiveTab("AST_MAPPER");
          break;
        default: break;
      }
    };
    return () => ws.close();
  }, [API_BASE]);

  useEffect(() => { traceEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [traceLogs]);
  useEffect(() => { validationLogEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [validationLogs]);

  // --- ORACLE CHAT HANDLER ---
  const handleChatSubmit = async (e) => {
      e.preventDefault();
      if (!chatInput.trim()) return;

      const newMsg = { role: "user", text: chatInput };
      setChatHistory(prev => [...prev, newMsg]);
      setChatInput("");

      setTimeout(() => {
          setChatHistory(prev => [...prev, {
              role: "oracle",
              text: `I am querying the ${activeTab.replace("_", " ")} context vectors... (Backend endpoint integration pending in Phase 12).`
          }]);
      }, 800);
  };

  const handleSaveKey = async (provider) => {
    setKeyStatus(prev => ({ ...prev, [provider]: "ENCRYPTING..." }));
    try {
        const res = await fetch(`${API_BASE}/settings/keys`, {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ provider, api_key: keys[provider] })
        });
        const data = await res.json();
        if (data.status === "success") {
            setKeyStatus(prev => ({ ...prev, [provider]: "SEALED" }));
            setKeys(prev => ({ ...prev, [provider]: "" }));
        } else {
            setKeyStatus(prev => ({ ...prev, [provider]: "FAILED" }));
        }
    } catch (err) { setKeyStatus(prev => ({ ...prev, [provider]: "FAILED" })); }
  };

  const handleSaveBudget = async () => {
      setBudgetStatus("SYNCING...");
      try {
          await fetch(`${API_BASE}/settings/budget`, {
              method: "POST", headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ limit: budget })
          });
          setTimeout(() => setBudgetStatus("SYNCED"), 500);
      } catch (err) { setBudgetStatus("FAILED"); }
  };

  const handlePurge = async () => {
      try {
          await fetch(`${API_BASE}/staging/purge`, { method: "POST" });
          fetchOutputTree();
          setActiveFilePath(null);
          setActiveFileContent("");
      } catch (err) {}
  };

  const handleKill = async () => {
      try {
          await fetch(`${API_BASE}/staging/kill`, { method: "POST" });
      } catch (err) {}
  };

  const handleDrop = async (e) => {
    e.preventDefault();
    setIsDragging(false);
    const files = e.dataTransfer.files;
    if (files.length === 0) return;
    setIsUploading(true);
    const formData = new FormData();
    formData.append("file", files[0]);
    try {
        const res = await fetch(`${API_BASE}/ingest`, { method: "POST", body: formData });
        const result = await res.json();
        if(result.status === "success") { setSelectedPaths(new Set()); fetchWorkspace(); }
    } catch (err) {
        alert("Upload Failed. Error: " + err.message);
    } finally { setIsUploading(false); }
  };

  const handleToggleSelect = (path) => {
    const newSet = new Set(selectedPaths);
    if (newSet.has(path)) newSet.delete(path);
    else newSet.add(path);
    setSelectedPaths(newSet);
  };

  const handleDeleteSelected = async () => {
    const pathsToDelete = Array.from(selectedPaths);
    if (pathsToDelete.length === 0) return;
    setIsDeleting(true);
    try {
        for (const path of pathsToDelete) {
            await fetch(`${API_BASE}/workspace/delete`, {
                method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ path })
            });
        }
        setSelectedPaths(new Set()); fetchWorkspace();
    } catch (err) {} finally { setIsDeleting(false); }
  };

  const handlePruneVenv = async () => {
      setIsDeleting(true);
      try {
          const res = await fetch(`${API_BASE}/workspace/prune-venv`, { method: "POST" });
          const result = await res.json();
          if (result.status === "success") fetchWorkspace();
      } catch (err) { alert("Failed to prune workspace."); }
      finally { setIsDeleting(false); }
  };

  const handleGenerateWorkspaceMap = async () => {
      setIsMapping(true);
      try { await fetch(`${API_BASE}/workspace/map`, { method: "POST" }); }
      catch (err) { setIsMapping(false); }
  };

  // --- NEW: Multi-Directory File Loader ---
  const handleLoadFile = async (path, type = "staging", errorTraceback = null) => {
      setActiveFilePath(path);
      setActiveError(errorTraceback);

      // Determine which endpoint to hit based on where the file lives
      const endpoint = type === "vault" ? "/vault/read" : "/file/read";

      try {
          const res = await fetch(`${API_BASE}${endpoint}`, {
              method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ path })
          });
          const data = await res.json();
          if (data.status === "success") {
              setActiveFileContent(data.content);
          } else {
              if (data.message && data.message.includes("No such file")) {
                  setActiveFileContent(`# File '${path}' is missing.\n# Write your code here to create it and rescue the Swarm...`);
              } else {
                  setActiveFileContent(`// Error loading file: ${data.message}`);
              }
          }
      } catch (err) { setActiveFileContent("// Failed to connect to backend to read file."); }
  };

  const handleSaveFile = async () => {
      if (!activeFilePath) return;
      setIsSaving(true);
      try {
          await fetch(`${API_BASE}/file/write`, {
              method: "POST", headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ path: activeFilePath, content: activeFileContent })
          });
          const isQuarantined = quarantineFiles.find(f => f.filename === activeFilePath);
          if (isQuarantined) {
              await fetch(`${API_BASE}/hitl/resolve`, {
                  method: "POST", headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ filename: activeFilePath, hint: "Fixed via Active Editor", error_traceback: activeError })
              });
              setQuarantineFiles(prev => prev.filter(f => f.filename !== activeFilePath));
              setActiveError(null);
          }
          setTimeout(() => setIsSaving(false), 500);
      } catch (err) { setIsSaving(false); alert("Failed to save file."); }
  };

  const handleGenerateOutputMap = async () => {
      setIsMapping(true);
      try { await fetch(`${API_BASE}/output/map`, { method: "POST" }); }
      catch (err) { setIsMapping(false); }
  };

  const renderDial = (value, label, alertLevel) => {
    const offset = 364.4 - (364.4 * (value / 100));
    let colorClass = "text-primary-container";
    if (alertLevel === "critical") { colorClass = "text-red-500 font-black drop-shadow-[0_0_8px_rgba(239,68,68,0.8)]"; }
    else if (alertLevel === "ai-load") { colorClass = "text-secondary-container drop-shadow-[0_0_8px_rgba(254,0,254,0.6)]"; }

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

  const renderWorkspaceTree = (nodes) => {
    return nodes.map((node, i) => (
      <div key={i} className="ml-4 mt-2">
        <div className="flex items-center gap-3 font-mono text-[12px] bg-[#1a1a1c] p-1.5 border border-outline-variant/10 rounded-sm mb-1 hover:bg-[#222225] transition-colors">
          <input type="checkbox" checked={selectedPaths.has(node.path)} onChange={() => handleToggleSelect(node.path)} className="w-4 h-4 accent-primary-container cursor-pointer" />
          <span className={node.type === "folder" ? "text-secondary-container font-bold" : "text-primary-container"}>
            {node.type === "folder" ? "📁" : "📄"} {node.name}
          </span>
        </div>
        {node.children && <div className="border-l-2 border-outline-variant/20 ml-2 pl-3">{renderWorkspaceTree(node.children)}</div>}
      </div>
    ));
  };

  // --- UPDATED: Pass directory type to loader ---
  const renderOutputTree = (nodes, type = "staging") => {
    return nodes.map((node, i) => (
      <div key={i} className="ml-3 mt-1">
        <div onClick={() => node.type === "file" && handleLoadFile(node.path, type)} className={`flex items-center gap-2 font-mono text-[11px] p-1.5 border border-outline-variant/10 rounded-sm transition-colors cursor-pointer ${activeFilePath === node.path ? 'bg-primary-container/20 border-primary-container/50' : 'bg-[#1a1a1c] hover:bg-[#222225]'}`}>
          <span className={node.type === "folder" ? "text-secondary-container font-bold" : "text-primary-container"}>
            {node.type === "folder" ? "📁" : "📄"} {node.name}
          </span>
        </div>
        {node.children && <div className="border-l border-outline-variant/20 ml-2 pl-2">{renderOutputTree(node.children, type)}</div>}
      </div>
    ));
  };

  const isSystemCritical = telemetry.cpu_usage_percent >= 95 || telemetry.ram_usage_percent >= 95;

  return (
    <div className="bg-background text-on-surface font-body min-h-screen selection:bg-primary-container selection:text-on-primary">
      <header className="fixed top-0 w-full z-50 flex justify-between items-center px-6 h-14 bg-[#131315] shadow-[0_1px_0_0_rgba(0,243,255,0.1)]">
        <div className="flex items-center gap-12">
            <div className="text-xl font-black text-[#00f3ff] tracking-tighter font-headline neon-glow-cyan">DEAN_OS_v5.1</div>
            <nav className="hidden lg:flex gap-8 font-headline text-[10px] font-bold tracking-[0.2em] mt-1">
                {/* --- UI UPDATE: TABS RENAMED AND ADDED --- */}
                {["WORKSPACE", "FACTORY_FLOOR", "RELEASE_VAULT", "AST_MAPPER", "LOGS", "SYSTEM_HEALTH", "SETTINGS"].map(tab => (
                    <button key={tab} onClick={() => setActiveTab(tab)} className={`transition-colors pb-4 ${activeTab === tab ? "text-primary-container border-b-2 border-primary-container" : "text-on-surface-variant hover:text-white"}`}>
                        {tab.replace("_", " ")}
                    </button>
                ))}
            </nav>
        </div>
        <div className="flex items-center gap-4">
            <span className={`font-headline text-[10px] font-bold tracking-widest ${isSystemCritical ? 'text-red-500 animate-pulse drop-shadow-[0_0_8px_rgba(239,68,68,0.8)]' : 'text-primary-container'}`}>
                {!isSystemCritical ? "🟢 SYSTEM SECURE" : "🔴 HARDWARE CRITICAL"}
            </span>
        </div>
      </header>

      <aside className="fixed left-0 top-14 bottom-32 w-72 z-40 flex flex-col bg-[#0e0e10] border-r border-[#3a494b]/20 p-6 overflow-y-auto terminal-scrollbar">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-2 h-2 rounded-full bg-primary-container neon-glow-cyan"></div>
          <span className="font-headline font-bold text-[10px] tracking-widest uppercase text-on-surface-variant">AETHELGARD_TELEMETRY</span>
        </div>
        <div className="space-y-6 flex-1">
          {renderDial(telemetry.cpu_usage_percent, "CPU", 100, telemetry.cpu_usage_percent >= 95 ? "critical" : "normal")}
          {renderDial(telemetry.ram_usage_percent, "RAM", 100, telemetry.ram_usage_percent >= 95 ? "critical" : "normal")}
          <div className="pt-4 border-t border-outline-variant/10">
              <div className="flex justify-between items-center mb-2">
                  <span className="text-[9px] font-mono text-secondary-container">GEMINI_QUOTA</span>
                  <span className="text-[9px] font-mono text-on-surface-variant">{geminiQuota}/15 RPM</span>
              </div>
              {renderDial(geminiQuota, "RPM", 15, geminiQuota >= 14 ? "critical" : geminiQuota >= 10 ? "warning" : "normal")}
          </div>
        </div>
        <div className="mt-auto pt-6 border-t border-outline-variant/20 flex flex-col gap-4">
            <div className="flex items-center justify-between bg-surface-container-lowest p-3 border border-outline-variant/10 cursor-pointer hover:border-error/50 transition-colors" onClick={() => setRushMode(!rushMode)}>
                <div className="flex flex-col">
                    <span className={`font-headline text-[10px] font-bold tracking-widest uppercase ${rushMode ? 'text-error drop-shadow-[0_0_5px_rgba(239,68,68,0.8)]' : 'text-on-surface-variant'}`}>RUSH_MODE</span>
                    <span className="font-mono text-[8px] text-on-surface-variant/70">Enterprise API Override</span>
                </div>
                <div className={`w-8 h-4 rounded-full flex items-center p-0.5 transition-colors ${rushMode ? 'bg-error' : 'bg-outline-variant/30'}`}>
                    <div className={`w-3 h-3 bg-white rounded-full transition-transform ${rushMode ? 'translate-x-4' : 'translate-x-0'}`}></div>
                </div>
            </div>
            <input type="text" value={promptInput} onChange={(e) => setPromptInput(e.target.value)} placeholder="Enter system prompt..." className="w-full bg-surface-container-low border-b-2 border-outline-variant focus:border-primary-container text-primary-container font-mono text-[10px] p-2 outline-none"/>
            <button
                    disabled={!promptInput || isDeploying}
                    onClick={async () => {
                        if (!promptInput || isDeploying) return;

                        // 1. Lock the button to prevent double-firing
                        setIsDeploying(true);

                        // 2. Instantly wipe old logs and inject a UI-only starting message
                        setTraceLogs([{
                            trace_id: "UI-BOOT",
                            agent: "System",
                            action: `Dispatching task to Factory Floor (Rush Mode: ${rushMode ? 'ON' : 'OFF'})...`,
                            status: "running",
                            timestamp: new Date().toISOString()
                        }]);

                        // 3. Send the actual API request
                        try {
                            await fetch(`${API_BASE}/build`, {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify({ prompt: promptInput, rush_mode: rushMode })
                            });
                            setPromptInput("");
                        } catch (err) {
                            console.error(err);
                        } finally {
                            // 4. Unlock the button after 3 seconds
                            setTimeout(() => setIsDeploying(false), 3000);
                        }
                    }}
                    className="w-full py-3 bg-gradient-to-r from-primary to-primary-container text-on-primary font-headline font-bold text-[10px] tracking-widest uppercase hover:brightness-110 active:scale-95 shadow-[0_0_10px_rgba(0,243,255,0.2)] disabled:opacity-50 disabled:cursor-not-allowed transition-all">
                    {isDeploying ? "TRANSMITTING..." : "DEPLOY_AGENT"}
                </button>
        </div>
      </aside>

      <main className="ml-72 mt-14 mb-32 pr-80 p-8 h-[calc(100vh-14rem)] relative flex flex-col">

        {/* --- GOVERNANCE HUB (SETTINGS) --- */}
        {activeTab === "SETTINGS" && (
            <div className="flex-1 flex gap-8 h-full">
                {/* Pillar 1: Encrypted Key Vault */}
                <div className="w-1/2 flex flex-col gap-6 overflow-y-auto terminal-scrollbar pr-2">
                    <div>
                        <h1 className="font-headline text-4xl font-black uppercase mb-1">SECURE_VAULT</h1>
                        <p className="font-headline text-[10px] tracking-[0.2em] text-on-surface-variant">AES-256-GCM HARDWARE ENCRYPTION</p>
                    </div>

                    <div className="bg-surface-container-lowest border border-outline-variant/20 p-6 flex flex-col gap-6 shadow-inner">
                        {/* OpenAI Key Input */}
                        <div className="flex flex-col gap-2">
                            <div className="flex justify-between items-center">
                                <label className="text-[10px] font-mono text-secondary-container tracking-widest font-bold">OPENAI_API_KEY</label>
                                <span className={`text-[9px] font-bold tracking-widest ${keyStatus.openai === 'SEALED' ? 'text-primary-container' : keyStatus.openai === 'FAILED' ? 'text-error' : 'text-on-surface-variant'}`}>
                                    [{keyStatus.openai}]
                                </span>
                            </div>
                            <div className="flex gap-2">
                                <input
                                    type="password"
                                    value={keys.openai}
                                    onChange={(e) => setKeys(prev => ({...prev, openai: e.target.value}))}
                                    placeholder="sk-proj-..."
                                    className="flex-1 bg-[#1a1a1c] border border-outline-variant/30 focus:border-secondary-container text-on-surface font-mono text-[12px] p-3 outline-none"
                                />
                                <button
                                    onClick={() => handleSaveKey('openai')}
                                    disabled={!keys.openai || keyStatus.openai === 'ENCRYPTING...'}
                                    className="bg-secondary-container/10 border border-secondary-container text-secondary-container font-headline font-bold text-[10px] tracking-widest px-6 uppercase hover:bg-secondary-container hover:text-black transition-colors disabled:opacity-30 disabled:cursor-not-allowed">
                                    SEAL_KEY
                                </button>
                            </div>
                        </div>

                        {/* Anthropic Key Input */}
                        <div className="flex flex-col gap-2">
                            <div className="flex justify-between items-center">
                                <label className="text-[10px] font-mono text-secondary-container tracking-widest font-bold">ANTHROPIC_API_KEY</label>
                                <span className={`text-[9px] font-bold tracking-widest ${keyStatus.anthropic === 'SEALED' ? 'text-primary-container' : keyStatus.anthropic === 'FAILED' ? 'text-error' : 'text-on-surface-variant'}`}>
                                    [{keyStatus.anthropic}]
                                </span>
                            </div>
                            <div className="flex gap-2">
                                <input
                                    type="password"
                                    value={keys.anthropic}
                                    onChange={(e) => setKeys(prev => ({...prev, anthropic: e.target.value}))}
                                    placeholder="sk-ant-..."
                                    className="flex-1 bg-[#1a1a1c] border border-outline-variant/30 focus:border-secondary-container text-on-surface font-mono text-[12px] p-3 outline-none"
                                />
                                <button
                                    onClick={() => handleSaveKey('anthropic')}
                                    disabled={!keys.anthropic || keyStatus.anthropic === 'ENCRYPTING...'}
                                    className="bg-secondary-container/10 border border-secondary-container text-secondary-container font-headline font-bold text-[10px] tracking-widest px-6 uppercase hover:bg-secondary-container hover:text-black transition-colors disabled:opacity-30 disabled:cursor-not-allowed">
                                    SEAL_KEY
                                </button>
                            </div>
                        </div>

                        {/* GEMINI Key Input */}
                        <div className="flex flex-col gap-2">
                            <div className="flex justify-between items-center">
                                <label className="text-[10px] font-mono text-secondary-container tracking-widest font-bold">GEMINI_API_KEY</label>
                                <span className={`text-[9px] font-bold tracking-widest ${keyStatus.gemini === 'SEALED' ? 'text-primary-container' : keyStatus.gemini === 'FAILED' ? 'text-error' : 'text-on-surface-variant'}`}>
                                    [{keyStatus.gemini}]
                                </span>
                            </div>
                            <div className="flex gap-2">
                                <input
                                    type="password"
                                    value={keys.gemini}
                                    onChange={(e) => setKeys(prev => ({...prev, gemini: e.target.value}))}
                                    placeholder="AIzaSy..."
                                    className="flex-1 bg-[#1a1a1c] border border-outline-variant/30 focus:border-secondary-container text-on-surface font-mono text-[12px] p-3 outline-none"
                                />
                                <button
                                    onClick={() => handleSaveKey('gemini')}
                                    disabled={!keys.gemini || keyStatus.gemini === 'ENCRYPTING...'}
                                    className="bg-secondary-container/10 border border-secondary-container text-secondary-container font-headline font-bold text-[10px] tracking-widest px-6 uppercase hover:bg-secondary-container hover:text-black transition-colors disabled:opacity-30 disabled:cursor-not-allowed">
                                    SEAL_KEY
                                </button>
                            </div>
                        </div>

                        <div className="text-[10px] text-on-surface-variant/50 font-mono mt-4 italic">
                            * Keys are encrypted instantly. Raw plaintext is purged from memory immediately upon transmission to the Rust core.
                        </div>
                    </div>
                </div>

                {/* Pillar 2: FinOps Governor */}
                <div className="w-1/2 flex flex-col gap-6">
                    <div>
                        <h1 className="font-headline text-4xl font-black uppercase mb-1">FINOPS_GOVERNOR</h1>
                        <p className="font-headline text-[10px] tracking-[0.2em] text-on-surface-variant">SWARM SPEND LIMITS</p>
                    </div>

                    <div className="bg-surface-container-lowest border border-outline-variant/20 p-6 shadow-inner flex flex-col h-full">
                        <div className="flex justify-between items-end mb-8 border-b border-outline-variant/20 pb-4">
                            <span className="text-[10px] font-mono text-primary-container tracking-widest font-bold">MAX_TASK_BUDGET</span>
                            <span className="text-3xl font-black text-on-surface font-headline">${budget.toFixed(2)}</span>
                        </div>

                        <input
                            type="range"
                            min="0.01" max="5.00" step="0.01"
                            value={budget}
                            onChange={(e) => {
                                setBudget(parseFloat(e.target.value));
                                setBudgetStatus("UNSAVED");
                            }}
                            className="w-full accent-primary-container mb-8 cursor-pointer"
                        />

                        <div className="mt-auto flex justify-between items-center">
                            <span className={`font-mono text-[10px] tracking-widest ${budgetStatus === 'SYNCED' ? 'text-primary-container' : 'text-on-surface-variant animate-pulse'}`}>
                                STATUS: {budgetStatus}
                            </span>
                            <button
                                onClick={handleSaveBudget}
                                disabled={budgetStatus === "SYNCED" || budgetStatus === "SYNCING..."}
                                className="bg-primary-container text-black font-headline font-bold text-[10px] tracking-widest px-8 py-3 uppercase hover:brightness-110 active:scale-95 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-[0_0_15px_rgba(0,243,255,0.4)]">
                                OVERWRITE_YAML_CONFIG
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        )}

        {/* --- SYSTEM HEALTH HUB --- */}
        {activeTab === "SYSTEM_HEALTH" && (
            <div className="flex-1 flex flex-col h-full">
                <div className="flex justify-between items-end mb-4">
                    <div>
                        <h1 className="font-headline text-4xl font-black uppercase mb-1">DOCKER_DAEMON_LOGS</h1>
                        <p className="font-headline text-[10px] tracking-[0.2em] text-on-surface-variant uppercase">LIVE INFRASTRUCTURE TELEMETRY</p>
                    </div>
                    <div className="flex gap-2">
                        {["api", "oubliette", "worker", "mnemosyne", "aethelgard"].map(svc => (
                            <button
                                key={svc}
                                onClick={() => fetchHealthLogs(svc)}
                                className={`px-4 py-2 text-[10px] font-headline font-bold tracking-widest uppercase transition-colors ${activeLogService === svc ? 'bg-primary-container text-black' : 'border border-outline-variant text-on-surface-variant hover:text-white'}`}>
                                {svc}
                            </button>
                        ))}
                    </div>
                </div>
                <div className="flex-1 bg-[#08080a] border border-outline-variant/30 p-4 shadow-inner overflow-hidden flex flex-col">
                    <div className="flex justify-between border-b border-outline-variant/20 pb-2 mb-2">
                        <span className="text-secondary-container font-mono text-[10px] font-bold">CONTAINER: deanos_{activeLogService}</span>
                        <button onClick={() => fetchHealthLogs(activeLogService)} className="text-primary-container hover:text-white text-[10px] font-mono">↻ REFRESH</button>
                    </div>
                    <pre className="flex-1 overflow-y-auto terminal-scrollbar font-mono text-[11px] text-on-surface-variant whitespace-pre-wrap leading-relaxed">
                        {healthLogs || "No logs available."}
                    </pre>
                </div>
            </div>
        )}

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

        {/* --- TIER 2: FACTORY FLOOR (Formerly Staging) --- */}
        {activeTab === "FACTORY_FLOOR" && (
            <div className="flex-1 flex flex-col h-full">
                <div className="flex justify-between items-end mb-4">
                    <div>
                        <h1 className="font-headline text-4xl font-black text-on-surface tracking-tighter uppercase mb-1">FACTORY_FLOOR</h1>
                        <p className="font-headline text-[10px] tracking-[0.2em] text-on-surface-variant uppercase">SWARM_ORCHESTRATION_AND_QA</p>
                    </div>
                    <div className="flex gap-3">
                        <button onClick={handlePurge} className="bg-error/10 border border-error text-error font-headline font-bold text-[10px] tracking-widest px-4 py-2 uppercase hover:bg-error hover:text-black transition-colors">
                            PURGE DRAFTS
                        </button>
                        <button onClick={handleKill} className="bg-error/10 border border-error text-error font-headline font-bold text-[10px] tracking-widest px-4 py-2 uppercase hover:bg-error hover:text-black transition-colors">
                            KILL SWARM
                        </button>
                        <div className="w-px h-8 bg-outline-variant/50 mx-2 self-center"></div>
                        <button onClick={fetchOutputTree} className="border border-outline-variant px-6 py-2 text-[10px] font-headline font-bold text-on-surface-variant hover:text-white uppercase tracking-widest transition-colors">
                            REFRESH VIEW
                        </button>
                    </div>
                </div>

                <div className="flex-1 flex gap-4 h-[calc(100%-4rem)] overflow-hidden">
                    <div className="w-1/4 flex flex-col gap-4">
                        <div className="flex-1 bg-surface-container-lowest border border-outline-variant/20 p-4 overflow-y-auto terminal-scrollbar shadow-inner">
                            <h2 className="text-primary-container font-headline font-bold text-[10px] tracking-widest mb-3 border-b border-outline-variant/20 pb-2">ACTIVE_DRAFTS</h2>
                            {outputFiles.length === 0 ? (
                                <div className="text-on-surface-variant/50 italic font-mono text-[10px]">No active tasks.</div>
                            ) : renderOutputTree(outputFiles, "staging")}
                        </div>

                        <div className="h-1/3 bg-[#1a1111] border border-error/30 p-4 overflow-y-auto terminal-scrollbar shadow-inner flex flex-col">
                            <h2 className="text-error font-headline font-bold text-[10px] tracking-widest mb-3 border-b border-error/20 pb-2 flex justify-between items-center">
                                QUARANTINE_ZONE
                                <span className="text-[8px] bg-error/20 text-error px-1.5 py-0.5 rounded-sm">{quarantineFiles.length} FILES</span>
                            </h2>
                            {quarantineFiles.length === 0 ? (
                                <div className="text-error/50 italic font-mono text-[10px] mt-4 text-center">No manual intervention required.</div>
                            ) : (
                                <div className="flex flex-col gap-2 flex-1 overflow-y-auto terminal-scrollbar">
                                    {quarantineFiles.map((qFile, i) => (
                                        <div key={i} onClick={() => handleLoadFile(qFile.filename, "staging", qFile.error_traceback)} className={`p-2 border cursor-pointer font-mono text-[10px] transition-all ${activeFilePath === qFile.filename ? 'bg-error/20 border-error' : 'bg-black border-error/30 hover:border-error/60 text-error'}`}>
                                            <div className="font-bold flex items-center gap-1">⚠️ {qFile.filename}</div>
                                            <div className="text-error/70 text-[9px] truncate">Failed Attempt {qFile.attempt}</div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>

                    <div className="w-1/2 flex flex-col bg-[#0c0c0e] border border-outline-variant/30 shadow-2xl relative">
                        <div className="bg-[#18181b] p-2 px-4 border-b border-outline-variant/30 flex justify-between items-center">
                            <span className="text-primary-container font-mono text-[11px] font-bold">{activeFilePath ? `📝 ${activeFilePath}` : "NO_FILE_SELECTED"}</span>
                            <button onClick={handleSaveFile} disabled={!activeFilePath || isSaving} className={`text-[9px] font-headline tracking-widest px-4 py-1.5 font-bold uppercase transition-all ${isSaving ? 'bg-secondary-container text-black' : 'bg-primary-container text-black hover:brightness-110 active:scale-95'} disabled:opacity-50 disabled:cursor-not-allowed`}>
                                {isSaving ? "SAVING..." : "SAVE_FIX"}
                            </button>
                        </div>
                        {activeError && (
                            <div className="bg-error/10 border-b border-error/30 p-3 max-h-32 overflow-y-auto terminal-scrollbar">
                                <span className="text-error font-bold text-[9px] uppercase tracking-widest block mb-1">Swarm Traceback:</span>
                                <code className="text-error/90 font-mono text-[10px] whitespace-pre-wrap block leading-tight">{activeError}</code>
                            </div>
                        )}
                        <textarea className="flex-1 bg-transparent p-6 font-mono text-[13px] text-on-surface-variant outline-none resize-none terminal-scrollbar leading-relaxed" value={activeFileContent} onChange={(e) => setActiveFileContent(e.target.value)} spellCheck="false" placeholder={activeFilePath ? "Loading..." : "Select a drafted asset or quarantined file to view/edit code."} disabled={!activeFilePath} />
                    </div>

                    <div className="w-1/4 bg-[#08080a] border border-outline-variant/20 p-4 overflow-y-auto terminal-scrollbar flex flex-col shadow-inner">
                        <h2 className="text-secondary-container font-headline font-bold text-[10px] tracking-widest mb-3 border-b border-outline-variant/20 pb-2 flex justify-between">SWARM_MONOLOGUE<span className="animate-pulse text-secondary-container text-lg leading-none">●</span></h2>
                        <div className="space-y-3 mt-2">
                            {validationLogs.length === 0 ? (
                                <div className="text-on-surface-variant/50 italic font-mono text-[10px]">Awaiting telemetry...</div>
                            ) : (
                                validationLogs.map((log, i) => (
                                    <div key={i} className={`font-mono text-[10px] bg-white/5 p-2 border-l-2 ${log.status === 'error' ? 'border-error' : 'border-secondary-container/50'}`}>
                                        <div className="opacity-70 mb-1 flex justify-between"><span className="text-on-surface-variant">[{log.time}]</span><span className={`font-bold ${log.status === 'error' ? 'text-error' : 'text-secondary-container'}`}>{log.agent}</span></div>
                                        <div className={log.status === 'error' ? 'text-error' : 'text-primary-container'}>{log.action}</div>
                                    </div>
                                ))
                            )}
                            <div ref={validationLogEndRef} />
                        </div>
                    </div>
                </div>
            </div>
        )}

        {/* --- TIER 3: RELEASE VAULT (NEW) --- */}
        {activeTab === "RELEASE_VAULT" && (
            <div className="flex-1 flex flex-col h-full">
                <div className="flex justify-between items-end mb-4">
                    <div>
                        <h1 className="font-headline text-4xl font-black text-on-surface tracking-tighter uppercase mb-1 text-[#00ff9d]">RELEASE_VAULT</h1>
                        <p className="font-headline text-[10px] tracking-[0.2em] text-[#00ff9d]/70 uppercase">VERIFIED_PRODUCTION_CODE</p>
                    </div>
                    <button onClick={fetchVaultTree} className="border border-[#00ff9d]/50 text-[#00ff9d] px-6 py-2 text-[10px] font-headline font-bold hover:bg-[#00ff9d]/10 uppercase tracking-widest transition-colors">
                        REFRESH VAULT
                    </button>
                </div>

                <div className="flex-1 flex gap-4 h-[calc(100%-4rem)] overflow-hidden">
                    <div className="w-1/3 bg-surface-container-lowest border border-[#00ff9d]/20 p-4 overflow-y-auto terminal-scrollbar shadow-inner">
                        <h2 className="text-[#00ff9d] font-headline font-bold text-[10px] tracking-widest mb-3 border-b border-[#00ff9d]/20 pb-2">VERIFIED_MODULES</h2>
                        {vaultFiles.length === 0 ? (
                            <div className="text-on-surface-variant/50 italic font-mono text-[10px]">Vault is currently empty. Awaiting agent promotion.</div>
                        ) : renderOutputTree(vaultFiles, "vault")}
                    </div>
                    <div className="w-2/3 flex flex-col bg-[#0c0c0e] border border-[#00ff9d]/30 shadow-2xl relative">
                        <div className="bg-[#18181b] p-2 px-4 border-b border-[#00ff9d]/30 flex justify-between items-center">
                            <span className="text-[#00ff9d] font-mono text-[11px] font-bold">{activeFilePath ? `🔒 ${activeFilePath}` : "NO_FILE_SELECTED"}</span>
                        </div>
                        <textarea className="flex-1 bg-transparent p-6 font-mono text-[13px] text-[#00ff9d]/80 outline-none resize-none terminal-scrollbar leading-relaxed selection:bg-[#00ff9d]/30" value={activeFileContent} readOnly spellCheck="false" placeholder={activeFilePath ? "Loading..." : "Select a verified module to view source."} />
                    </div>
                </div>
            </div>
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
                            <div className="flex gap-4 text-on-surface-variant mb-2"><span>[{new Date(log.timestamp).toLocaleString()}]</span> <span>ID: {log.trace_id}</span><span className="text-primary-container font-bold">{log.agent_name}</span></div>
                            <div className={`text-sm ${log.status === 'error' ? 'text-error' : 'text-on-surface'}`}>{log.action}</div>
                            {log.logs && <pre className="mt-3 p-4 bg-[#08080a] text-secondary-container">{log.logs}</pre>}
                        </div>
                    ))}
                </div>
            </div>
        )}

        {/* --- TIER 1: WORKSPACE (The Library) --- */}
        {activeTab === "WORKSPACE" && (
            <div className="flex-1 flex gap-8 h-full">
                <div className="w-1/2 flex flex-col">
                    <div className="flex justify-between items-end mb-4">
                        <div>
                            <h1 className="font-headline text-4xl font-black uppercase mb-1">SOURCE_LIBRARY</h1>
                            <p className="font-headline text-[10px] tracking-[0.2em] text-on-surface-variant">READ_ONLY_CONTEXT</p>
                        </div>
                    </div>
                    {workspaceFiles.length > 0 && (
                        <div className="flex gap-4 mb-4 bg-surface-container-lowest p-3 border border-outline-variant/20 shadow-sm items-center justify-between">
                            <div className="flex items-center gap-3">
                                <span className="text-[10px] font-mono text-on-surface-variant tracking-widest">{selectedPaths.size} SELECTED</span>
                                <button onClick={handleDeleteSelected} disabled={selectedPaths.size === 0 || isDeleting} className="bg-error/20 text-error border border-error/50 font-headline font-bold text-[10px] tracking-widest px-4 py-2 uppercase transition-all hover:bg-error hover:text-white disabled:opacity-30 active:scale-95">{isDeleting ? "DELETING..." : "DELETE SELECTED"}</button>
                                {/* --- NEW PRUNE BUTTON --- */}
                                <button onClick={handlePruneVenv} disabled={isDeleting} className="bg-secondary-container/20 text-secondary-container border border-secondary-container/50 font-headline font-bold text-[10px] tracking-widest px-4 py-2 uppercase transition-all hover:bg-secondary-container hover:text-black active:scale-95 disabled:opacity-30">
                                    PRUNE_VIRTUAL_ENV
                                </button>
                            </div>
                            <button onClick={handleGenerateWorkspaceMap} disabled={isMapping} className="bg-primary-container text-[#131315] font-headline font-black text-[12px] tracking-widest px-6 py-2 uppercase transition-all hover:brightness-110 active:scale-95 disabled:opacity-50 shadow-[0_0_15px_rgba(0,243,255,0.4)]">{isMapping ? "MAPPING..." : "GENERATE AST MAP"}</button>
                        </div>
                    )}
                    <div className="flex-1 overflow-y-auto bg-surface-container-lowest border border-outline-variant/20 p-4 terminal-scrollbar">
                        {workspaceFiles.length === 0 ? <div className="text-on-surface-variant/50 italic font-mono text-[11px]">Workspace is empty. Drop a ZIP to begin context extraction.</div> : renderWorkspaceTree(workspaceFiles)}
                    </div>
                </div>
                <div className="w-1/2 flex flex-col">
                    <div className="mb-4">
                        <h1 className="font-headline text-4xl font-black mb-1">INTAKE_FORGE</h1>
                        <p className="font-headline text-[10px] tracking-[0.2em] text-on-surface-variant">RAG_VECTORIZATION_ENGINE</p>
                    </div>
                    <div onDragOver={(e) => {e.preventDefault(); setIsDragging(true);}} onDragLeave={() => setIsDragging(false)} onDrop={handleDrop} className={`flex-1 flex flex-col items-center justify-center border-2 border-dashed transition-all ${isDragging ? 'border-primary-container bg-primary-container/10' : 'border-outline-variant/50 bg-surface-container-lowest'} ${isUploading ? 'opacity-50' : ''}`}>
                        {isUploading ? <div className="text-center animate-pulse"><h2 className="font-headline text-lg font-bold text-primary-container uppercase">Extracting & Vectorizing...</h2></div> : <div className="text-center pointer-events-none"><div className="text-outline-variant text-4xl mb-4">📥</div><h2 className="font-headline text-lg font-bold text-on-surface-variant uppercase tracking-widest">Drop Codebase (.ZIP)</h2></div>}
                    </div>
                </div>
            </div>
        )}
      </main>
      <aside className="fixed right-0 top-14 bottom-32 w-80 bg-[#08080a] border-l border-[#3a494b]/30 flex flex-col z-40 shadow-[-10px_0_30px_rgba(0,0,0,0.5)]">
          <div className="bg-[#131315] border-b border-outline-variant/10 p-4 flex flex-col gap-1">
              <div className="flex items-center gap-2 text-secondary-container">
                  <span className="text-xl">👁️</span>
                  <h2 className="font-headline font-black text-lg tracking-widest uppercase">THE_ORACLE</h2>
              </div>
              <div className="font-mono text-[9px] text-on-surface-variant uppercase flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-secondary-container animate-pulse"></span>
                  CONTEXT: {activeTab.replace("_", " ")}
              </div>
          </div>
          <div className="flex-1 overflow-y-auto terminal-scrollbar p-4 space-y-4">
              {chatHistory.map((msg, i) => (
                  <div key={i} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                      <div className={`max-w-[85%] p-3 rounded-md text-[11px] font-mono leading-relaxed ${msg.role === 'user' ? 'bg-primary-container/20 text-primary-container border border-primary-container/30' : 'bg-surface-container-low text-on-surface border border-outline-variant/20'}`}>{msg.text}</div>
                      <span className="text-[8px] text-on-surface-variant/50 mt-1 uppercase tracking-widest">{msg.role === 'user' ? 'HUMAN' : 'ORACLE'}</span>
                  </div>
              ))}
              <div ref={chatEndRef} />
          </div>
          <div className="p-4 border-t border-outline-variant/10 bg-[#131315]">
              <form onSubmit={handleChatSubmit} className="flex gap-2">
                  <input type="text" value={chatInput} onChange={(e) => setChatInput(e.target.value)} placeholder="Ask the Oracle..." className="flex-1 bg-surface-container-lowest border border-outline-variant/30 rounded-sm px-3 py-2 text-[10px] font-mono text-on-surface outline-none focus:border-secondary-container transition-colors" />
                  <button type="submit" disabled={!chatInput.trim()} className="bg-secondary-container/20 text-secondary-container border border-secondary-container/50 px-3 py-2 rounded-sm hover:bg-secondary-container hover:text-black transition-colors disabled:opacity-30">➔</button>
              </form>
          </div>
      </aside>

      <footer className="fixed bottom-0 left-0 right-0 h-32 bg-[#0c0c0e]/95 border-t border-[#3a494b]/50 z-50 p-0 flex flex-col backdrop-blur-md">
        <div className="flex items-center justify-between border-b border-outline-variant/20 py-1.5 px-4 bg-[#131315]">
          <span className="font-headline text-[10px] font-bold text-primary-container tracking-widest uppercase flex items-center gap-2"><div className="w-1.5 h-1.5 bg-primary-container rounded-full animate-pulse"></div>WATERFALL_TRACE</span>
          <span className="text-[9px] font-mono text-on-surface-variant/50 uppercase pr-80">Live Pipeline Execution Ledger</span>
        </div>
        <div className="flex-1 overflow-y-auto terminal-scrollbar font-mono text-[11px] space-y-1.5 p-4 pl-8 pr-80">
          {traceLogs.length === 0 ? <div className="text-on-surface-variant/50 italic">Awaiting pipeline execution...</div> : traceLogs.map((log, i) => (
                <div key={i} className={`flex gap-3 ${log.status === 'error' ? 'text-secondary-container font-bold bg-secondary-container/5 py-0.5 border-l-2 border-secondary-container px-2 -ml-[10px]' : 'text-primary-container'}`}>
                  <span className="opacity-50 min-w-[75px]">[{new Date(log.timestamp || Date.now()).toLocaleTimeString()}]</span>
                  <span className="opacity-50 min-w-[140px] truncate">[TASK: {log.trace_id}]</span>
                  <span className="min-w-[100px] font-bold">[AGENT: {log.agent}]</span>
                  <span className="flex-1 break-words leading-tight">{log.action}</span>
                </div>
          ))}
          <div ref={traceEndRef} className="text-primary-container animate-pulse mt-2">_</div>
        </div>
      </footer>
    </div>
  );
}
