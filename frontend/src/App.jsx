import React, { useState, useEffect, useRef } from 'react';
import { 
  Plus, 
  Zap, 
  Globe, 
  Terminal, 
  Bug, 
  FileText, 
  Compass, 
  CheckCircle2, 
  AlertTriangle, 
  RefreshCw, 
  Sparkles, 
  Code, 
  Check, 
  Wrench, 
  Copy, 
  ShieldCheck,
  ArrowRight,
  Play,
  Sun,
  Moon,
  X
} from 'lucide-react';

export default function App() {
  const [runs, setRuns] = useState([]);
  const [selectedRunId, setSelectedRunId] = useState(null);
  const selectedRunIdRef = useRef(null);

  const [targetUrl, setTargetUrl] = useState('');
  const [maxDepth, setMaxDepth] = useState(3);
  const [maxPages, setMaxPages] = useState(25);
  const [isStarting, setIsStarting] = useState(false);
  const [activeTab, setActiveTab] = useState('stream');
  const [analyzingBugs, setAnalyzingBugs] = useState({});
  const [applyingFixes, setApplyingFixes] = useState({});
  const [copiedId, setCopiedId] = useState(null);
  const [lightTerminalMode, setLightTerminalMode] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  
  const chatEndRef = useRef(null);

  const selectedRun = runs.find(r => r.run_id === selectedRunId) || null;

  const selectRun = (runId) => {
    setSelectedRunId(runId);
    selectedRunIdRef.current = runId;
  };

  const fetchRuns = async () => {
    try {
      const res = await fetch('/api/runs');
      if (res.ok) {
        const data = await res.json();
        setRuns(data);
        if (data.length > 0 && selectedRunIdRef.current === null) {
          setSelectedRunId(data[0].run_id);
          selectedRunIdRef.current = data[0].run_id;
        }
      }
    } catch (e) {
      console.error('Failed to fetch runs:', e);
    }
  };

  useEffect(() => {
    fetchRuns();
    const interval = setInterval(fetchRuns, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleStartRun = async (e, overrideUrl = null) => {
    if (e) e.preventDefault();
    const urlToUse = overrideUrl || targetUrl;
    if (!urlToUse) return;
    setIsStarting(true);
    try {
      const res = await fetch('/api/runs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target_url: urlToUse, max_depth: maxDepth, max_pages: maxPages })
      });
      if (res.ok) {
        const newRun = await res.json();
        setTargetUrl('');
        setIsModalOpen(false);
        await fetchRuns();
        selectRun(newRun.run_id);
        setActiveTab('stream');
      }
    } catch (e) {
      console.error('Failed to start run:', e);
    } finally {
      setIsStarting(false);
    }
  };

  const handleAnalyzeBug = async (bugId) => {
    setAnalyzingBugs(prev => ({ ...prev, [bugId]: true }));
    try {
      const res = await fetch(`/api/bugs/${bugId}/analyze`, { method: 'POST' });
      if (res.ok) {
        await fetchRuns();
      }
    } catch (e) {
      console.error(`Failed to analyze bug ${bugId}:`, e);
    } finally {
      setAnalyzingBugs(prev => ({ ...prev, [bugId]: false }));
    }
  };

  const handleApplyFix = async (bugId) => {
    setApplyingFixes(prev => ({ ...prev, [bugId]: true }));
    try {
      const res = await fetch(`/api/bugs/${bugId}/apply-fix`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ approve: true })
      });
      if (res.ok) {
        await fetchRuns();
      }
    } catch (e) {
      console.error(`Failed to apply fix for bug ${bugId}:`, e);
    } finally {
      setApplyingFixes(prev => ({ ...prev, [bugId]: false }));
    }
  };

  const copyToClipboard = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'COMPLETED':
        return <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-[#34C759]/15 text-[#248A3D] border border-[#34C759]/30"><CheckCircle2 className="w-3.5 h-3.5 mr-1"/> Completed</span>;
      case 'FAILED':
        return <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-[#FF3B30]/15 text-[#D70015] border border-[#FF3B30]/30"><AlertTriangle className="w-3.5 h-3.5 mr-1"/> Failed</span>;
      case 'DISCOVERING':
        return <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-[#0071E3]/15 text-[#0071E3] border border-[#0071E3]/30 animate-pulse"><Compass className="w-3.5 h-3.5 mr-1"/> Discovering</span>;
      case 'PLANNING':
        return <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-[#AF52DE]/15 text-[#8944AB] border border-[#AF52DE]/30 animate-pulse"><FileText className="w-3.5 h-3.5 mr-1"/> Planning</span>;
      case 'EXECUTING':
        return <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-[#FF9500]/15 text-[#C27000] border border-[#FF9500]/30 animate-pulse"><Zap className="w-3.5 h-3.5 mr-1"/> Executing</span>;
      default:
        return <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-[#E5E5E7] text-[#1D1D1F] border border-[#D2D2D7]">{status}</span>;
    }
  };

  const getLogColorClass = (logText, isLight) => {
    if (isLight) {
      if (logText.includes('❌') || logText.includes('FAILED') || logText.includes('HTTP 500') || logText.includes('Error')) {
        return 'text-[#D70015] font-extrabold';
      }
      if (logText.includes('✅') || logText.includes('Discovered') || logText.includes('complete') || logText.includes('200')) {
        return 'text-[#248A3D] font-extrabold';
      }
      if (logText.includes('🔍') || logText.includes('ExplorerAgent')) {
        return 'text-[#0071E3] font-bold';
      }
      return 'text-[#1D1D1F] font-bold';
    } else {
      if (logText.includes('❌') || logText.includes('FAILED') || logText.includes('HTTP 500') || logText.includes('Error')) {
        return 'text-[#FF453A] font-extrabold';
      }
      if (logText.includes('✅') || logText.includes('Discovered') || logText.includes('complete') || logText.includes('200')) {
        return 'text-[#30D158] font-extrabold';
      }
      if (logText.includes('🔍') || logText.includes('ExplorerAgent')) {
        return 'text-[#64D2FF] font-bold';
      }
      return 'text-[#FFFFFF] font-bold';
    }
  };

  return (
    <div className="flex h-screen bg-[#FFFFFF] text-[#1D1D1F] font-sans antialiased">
      {/* Apple-Style Light Sidebar */}
      <aside className="w-[280px] bg-[#F5F5F7] border-r border-[#E5E5E7] flex flex-col flex-shrink-0 select-none">
        {/* Top Brand & New Run Button */}
        <div className="p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="w-7 h-7 rounded-lg bg-[#0071E3] text-white flex items-center justify-center font-bold text-sm shadow-sm">
                
              </div>
              <span className="font-bold text-base text-[#1D1D1F] tracking-tight">ChaosPilot <span className="text-xs font-normal text-[#6E6E73]">Pro</span></span>
            </div>
            <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-[#0071E3]/10 text-[#0071E3]">V2.0</span>
          </div>

          <button
            onClick={() => setIsModalOpen(true)}
            className="w-full flex items-center justify-between px-4 py-2.5 rounded-xl bg-[#0071E3] hover:bg-[#0077ED] text-white font-semibold text-xs transition duration-200 shadow-sm"
          >
            <div className="flex items-center space-x-2">
              <Plus className="w-4 h-4" />
              <span>New Chaos Run</span>
            </div>
            <Sparkles className="w-3.5 h-3.5 opacity-90" />
          </button>
        </div>

        {/* History Runs Stream List */}
        <div className="flex-1 overflow-y-auto px-3 space-y-1">
          <div className="px-3 py-2 text-[11px] font-bold text-[#6E6E73] uppercase tracking-wider">Test Runs History</div>
          {runs.length === 0 ? (
            <div className="px-3 py-6 text-xs text-[#6E6E73] text-center font-medium">No runs recorded yet.</div>
          ) : (
            runs.map((r) => (
              <div
                key={r.run_id}
                onClick={() => {
                  selectRun(r.run_id);
                  setActiveTab('stream');
                }}
                className={`group relative flex items-center justify-between px-3.5 py-3 rounded-xl text-xs cursor-pointer transition duration-150 ${
                  selectedRunId === r.run_id
                    ? 'bg-[#FFFFFF] text-[#1D1D1F] font-bold shadow-sm border border-[#E5E5E7]'
                    : 'text-[#424245] hover:bg-[#FFFFFF]/70 hover:text-[#1D1D1F]'
                }`}
              >
                <div className="flex items-center space-x-2.5 truncate">
                  <Globe className={`w-4 h-4 flex-shrink-0 ${selectedRunId === r.run_id ? 'text-[#0071E3]' : 'text-[#6E6E73]'}`} />
                  <span className="truncate font-bold text-[#1D1D1F]">{r.target_url.replace(/^https?:\/\//, '')}</span>
                </div>
                {r.discovered_bugs?.length > 0 && (
                  <span className="px-2 py-0.5 text-[10px] font-bold rounded-full bg-[#FF3B30]/15 text-[#D70015]">
                    {r.discovered_bugs.length}
                  </span>
                )}
              </div>
            ))
          )}
        </div>

        {/* Sidebar Footer Status */}
        <div className="p-4 border-t border-[#E5E5E7] bg-[#F5F5F7] flex items-center justify-between text-xs text-[#6E6E73]">
          <div className="flex items-center space-x-2">
            <div className="w-2.5 h-2.5 rounded-full bg-[#34C759]"></div>
            <span className="font-bold text-[#1D1D1F]">Autonomous Engine</span>
          </div>
          <ShieldCheck className="w-4 h-4 text-[#0071E3]" />
        </div>
      </aside>

      {/* Main Apple Workspace */}
      <main className="flex-1 flex flex-col h-full bg-[#FFFFFF] overflow-hidden relative">
        {/* Apple Translucent Navigation Bar */}
        <header className="h-16 border-b border-[#E5E5E7] px-8 flex items-center justify-between apple-glass z-10 select-none">
          <div className="flex items-center space-x-4">
            <h1 className="text-base font-bold text-[#1D1D1F] tracking-tight flex items-center space-x-2">
              <span>Autonomous QA Navigator</span>
            </h1>
            {selectedRun && getStatusBadge(selectedRun.status)}
          </div>

          {selectedRun && (
            <div className="flex items-center space-x-1 bg-[#F5F5F7] p-1 rounded-xl border border-[#E5E5E7] text-xs">
              <button
                onClick={() => setActiveTab('stream')}
                className={`px-4 py-1.5 rounded-lg font-bold transition ${
                  activeTab === 'stream' ? 'bg-[#FFFFFF] text-[#0071E3] shadow-sm' : 'text-[#6E6E73] hover:text-[#1D1D1F]'
                }`}
              >
                Agent Stream
              </button>
              <button
                onClick={() => setActiveTab('bugs')}
                className={`px-4 py-1.5 rounded-lg font-bold transition ${
                  activeTab === 'bugs' ? 'bg-[#FFFFFF] text-[#D70015] shadow-sm' : 'text-[#6E6E73] hover:text-[#1D1D1F]'
                }`}
              >
                Bugs & Fixes ({selectedRun.discovered_bugs?.length || 0})
              </button>
              <button
                onClick={() => setActiveTab('tests')}
                className={`px-4 py-1.5 rounded-lg font-bold transition ${
                  activeTab === 'tests' ? 'bg-[#FFFFFF] text-[#1D1D1F] shadow-sm' : 'text-[#6E6E73] hover:text-[#1D1D1F]'
                }`}
              >
                Test Plan
              </button>
              <button
                onClick={() => setActiveTab('sitemap')}
                className={`px-4 py-1.5 rounded-lg font-bold transition ${
                  activeTab === 'sitemap' ? 'bg-[#FFFFFF] text-[#1D1D1F] shadow-sm' : 'text-[#6E6E73] hover:text-[#1D1D1F]'
                }`}
              >
                Site Map
              </button>
            </div>
          )}
        </header>

        {/* Central Workspace Container */}
        <div className="flex-1 overflow-y-auto px-6 md:px-16 py-8 space-y-8">
          {!selectedRun ? (
            /* Pristine Apple Landing Screen */
            <div className="max-w-3xl mx-auto my-12 text-center space-y-8">
              <div className="w-16 h-16 rounded-3xl bg-[#0071E3]/10 border border-[#0071E3]/20 flex items-center justify-center mx-auto shadow-md">
                <Zap className="w-8 h-8 text-[#0071E3]" />
              </div>

              <div className="space-y-3">
                <h2 className="text-4xl font-extrabold tracking-tight text-[#1D1D1F]">
                  Autonomous Web App Testing.
                </h2>
                <p className="text-base text-[#424245] max-w-xl mx-auto font-semibold leading-relaxed">
                  ChaosPilot crawls your target application, builds risk-based test plans, intercepts unhandled exceptions, and proposes verified code fixes.
                </p>
              </div>

              {/* Quick Action Suggestion Cards */}
              <div className="grid grid-cols-2 gap-4 text-left pt-4">
                <div 
                  onClick={() => handleStartRun(null, 'http://127.0.0.1:8888')}
                  className="p-6 rounded-2xl bg-[#F5F5F7] border border-[#E5E5E7] hover:border-[#0071E3] hover:shadow-md cursor-pointer transition-all duration-200 group"
                >
                  <div className="flex items-center justify-between text-sm font-extrabold text-[#1D1D1F] group-hover:text-[#0071E3]">
                    <span>Test Local Vulnerable Shop</span>
                    <ArrowRight className="w-4 h-4 text-[#6E6E73] group-hover:text-[#0071E3] transform group-hover:translate-x-1 transition" />
                  </div>
                  <p className="text-xs text-[#424245] mt-2 font-bold">
                    Explore http://127.0.0.1:8888 for HTTP 500 errors and uncaught JS button crashes.
                  </p>
                </div>

                <div 
                  onClick={() => handleStartRun(null, 'https://example.com')}
                  className="p-6 rounded-2xl bg-[#F5F5F7] border border-[#E5E5E7] hover:border-[#0071E3] hover:shadow-md cursor-pointer transition-all duration-200 group"
                >
                  <div className="flex items-center justify-between text-sm font-extrabold text-[#1D1D1F] group-hover:text-[#0071E3]">
                    <span>Crawl Public Web Application</span>
                    <ArrowRight className="w-4 h-4 text-[#6E6E73] group-hover:text-[#0071E3] transform group-hover:translate-x-1 transition" />
                  </div>
                  <p className="text-xs text-[#424245] mt-2 font-bold">
                    Discover routes, extract forms, and map interactive links within domain guardrails.
                  </p>
                </div>
              </div>
            </div>
          ) : (
            /* Selected Run Execution Stream */
            <div className="max-w-4xl mx-auto space-y-8">
              {/* Target Header Card */}
              <div className="bg-[#F5F5F7] border border-[#E5E5E7] rounded-2xl p-6 shadow-sm flex items-center justify-between">
                <div>
                  <span className="text-xs font-extrabold text-[#6E6E73] uppercase tracking-wider">Target Application</span>
                  <h2 className="text-xl font-extrabold text-[#1D1D1F] mt-0.5 flex items-center space-x-2">
                    <Globe className="w-5 h-5 text-[#0071E3]" />
                    <span>{selectedRun.target_url}</span>
                  </h2>
                </div>
                <div className="flex items-center space-x-6 text-center">
                  <div>
                    <div className="text-xl font-extrabold text-[#1D1D1F]">{Object.keys(selectedRun.site_map || {}).length}</div>
                    <div className="text-[10px] text-[#6E6E73] uppercase font-bold">Routes</div>
                  </div>
                  <div>
                    <div className="text-xl font-extrabold text-[#1D1D1F]">{selectedRun.test_plan?.length || 0}</div>
                    <div className="text-[10px] text-[#6E6E73] uppercase font-bold">Tests</div>
                  </div>
                  <div>
                    <div className="text-xl font-extrabold text-[#D70015]">{selectedRun.discovered_bugs?.length || 0}</div>
                    <div className="text-[10px] text-[#6E6E73] uppercase font-bold">Bugs</div>
                  </div>
                </div>
              </div>

              {/* Stream Tab View */}
              {activeTab === 'stream' && (
                <div className="bg-[#F5F5F7] border border-[#E5E5E7] rounded-2xl p-6 shadow-sm space-y-4 font-mono text-xs">
                  <div className="flex items-center justify-between pb-3 border-b border-[#E5E5E7] font-sans">
                    <span className="font-extrabold text-sm text-[#1D1D1F] flex items-center space-x-2">
                      <Terminal className="w-4 h-4 text-[#0071E3]" />
                      <span>Live Terminal Execution Stream</span>
                    </span>
                    
                    <div className="flex items-center space-x-3">
                      <button
                        onClick={() => setLightTerminalMode(!lightTerminalMode)}
                        className="px-2.5 py-1 rounded-lg bg-[#FFFFFF] border border-[#E5E5E7] text-xs font-bold text-[#1D1D1F] flex items-center space-x-1.5 shadow-sm hover:bg-[#F5F5F7] transition"
                        title="Toggle Terminal Contrast Mode"
                      >
                        {lightTerminalMode ? <Moon className="w-3.5 h-3.5 text-[#0071E3]" /> : <Sun className="w-3.5 h-3.5 text-[#FF9500]" />}
                        <span>{lightTerminalMode ? 'Dark Terminal' : 'Light Terminal'}</span>
                      </button>
                      <span className="text-xs text-[#1D1D1F] font-bold">{selectedRun.logs?.length || 0} events logged</span>
                    </div>
                  </div>
                  
                  {/* High-contrast Terminal Output Box */}
                  <div className={`p-5 rounded-xl border max-h-[480px] overflow-y-auto space-y-2.5 font-mono text-xs shadow-xl transition-all ${
                    lightTerminalMode 
                      ? 'bg-[#FFFFFF] text-[#1D1D1F] border-[#E5E5E7]' 
                      : 'bg-[#000000] text-[#FFFFFF] border-[#333333]'
                  }`}>
                    {selectedRun.logs && selectedRun.logs.length > 0 ? (
                      selectedRun.logs.map((log, i) => (
                        <div key={i} className={`leading-relaxed font-mono flex items-start space-x-3 text-xs ${getLogColorClass(log, lightTerminalMode)}`}>
                          <span className={`select-none flex-shrink-0 text-[11px] font-bold ${lightTerminalMode ? 'text-[#0071E3]' : 'text-[#FFD60A]'}`}>
                            [{i + 1}]
                          </span>
                          <span className="whitespace-pre-wrap">{log}</span>
                        </div>
                      ))
                    ) : (
                      <div className={`py-8 text-center flex items-center justify-center space-x-3 font-sans text-xs font-bold ${lightTerminalMode ? 'text-[#1D1D1F]' : 'text-[#FFFFFF]'}`}>
                        <RefreshCw className="w-4 h-4 animate-spin text-[#0071E3]" />
                        <span>Initializing agent exploration stream...</span>
                      </div>
                    )}
                    <div ref={chatEndRef} />
                  </div>
                </div>
              )}

              {/* Bugs & Auto-Fixes Tab View */}
              {activeTab === 'bugs' && (
                <div className="space-y-6">
                  {selectedRun.discovered_bugs?.length === 0 ? (
                    <div className="bg-[#F5F5F7] border border-[#E5E5E7] rounded-2xl p-10 text-center text-[#6E6E73]">
                      <CheckCircle2 className="w-12 h-12 text-[#34C759] mx-auto mb-3" />
                      <h3 className="text-base font-bold text-[#1D1D1F]">No Vulnerabilities Detected</h3>
                      <p className="text-xs text-[#424245] mt-1 font-semibold">Application executed test cases without throwing unhandled exceptions.</p>
                    </div>
                  ) : (
                    selectedRun.discovered_bugs?.map((b) => (
                      <div key={b.id} className="bg-[#F5F5F7] border border-[#E5E5E7] rounded-2xl p-6 space-y-5 shadow-sm">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-mono font-bold text-[#D70015]">{b.id}</span>
                          <span className="px-3 py-1 text-xs font-bold rounded-full bg-[#FF3B30]/15 text-[#D70015] border border-[#FF3B30]/30">
                            {b.severity}
                          </span>
                        </div>
                        <div>
                          <h3 className="text-lg font-extrabold text-[#1D1D1F]">{b.title}</h3>
                          <p className="text-xs text-[#1D1D1F] mt-1 font-semibold leading-relaxed">{b.description}</p>
                        </div>
                        
                        <div className="bg-[#FFFFFF] p-4 rounded-xl border border-[#E5E5E7] font-mono text-xs text-[#1D1D1F] flex items-center justify-between">
                          <div>
                            <span className="text-[#6E6E73] block text-[10px] font-sans font-bold">Reproduction Script Path:</span>
                            <code className="text-[#0071E3] font-bold">{b.reproduction_script_path}</code>
                          </div>
                          <button 
                            onClick={() => copyToClipboard(b.reproduction_script_path, b.id)}
                            className="p-2 hover:bg-[#F5F5F7] rounded-lg text-[#6E6E73] hover:text-[#1D1D1F] transition"
                            title="Copy Path"
                          >
                            {copiedId === b.id ? <Check className="w-4 h-4 text-[#34C759]" /> : <Copy className="w-4 h-4" />}
                          </button>
                        </div>

                        {/* Root Cause & Fix Section */}
                        {b.root_cause_analysis ? (
                          <div className="p-5 rounded-2xl bg-[#FFFFFF] border border-[#0071E3]/40 shadow-sm space-y-4">
                            <h4 className="text-xs font-bold text-[#0071E3] uppercase tracking-wider flex items-center space-x-2">
                              <Code className="w-4 h-4" />
                              <span>Root Cause Diagnosis</span>
                            </h4>
                            <p className="text-xs text-[#1D1D1F] font-semibold leading-relaxed">{b.root_cause_analysis.probable_root_cause}</p>

                            {b.root_cause_analysis.proposed_patches?.length > 0 && (
                              <div className="space-y-1">
                                <span className="text-xs font-bold text-[#1D1D1F] block">Proposed Code Patch:</span>
                                <pre className="bg-[#000000] text-[#30D158] p-4 rounded-xl text-xs font-mono border border-[#333333] overflow-x-auto font-bold">
                                  {b.root_cause_analysis.proposed_patches[0].diff || b.root_cause_analysis.proposed_patches[0].proposed_code}
                                </pre>
                              </div>
                            )}

                            {b.root_cause_analysis.status === 'VERIFIED' ? (
                              <div className="p-3 bg-[#34C759]/15 border border-[#34C759]/40 rounded-xl text-xs text-[#248A3D] font-bold flex items-center space-x-2">
                                <Check className="w-4 h-4" />
                                <span>Code Fix Approved & Applied in Repository</span>
                              </div>
                            ) : (
                              <button
                                onClick={() => handleApplyFix(b.id)}
                                disabled={applyingFixes[b.id]}
                                className="w-full bg-[#0071E3] hover:bg-[#0077ED] text-white font-bold py-3 rounded-xl text-xs transition flex items-center justify-center space-x-2 shadow-sm"
                              >
                                {applyingFixes[b.id] ? (
                                  <RefreshCw className="w-4 h-4 animate-spin" />
                                ) : (
                                  <>
                                    <Check className="w-4 h-4" />
                                    <span>Approve & Apply Code Fix (Human Approval Required)</span>
                                  </>
                                )}
                              </button>
                            )}
                          </div>
                        ) : (
                          <button
                            onClick={() => handleAnalyzeBug(b.id)}
                            disabled={analyzingBugs[b.id]}
                            className="w-full bg-[#FFFFFF] hover:bg-[#F5F5F7] border border-[#E5E5E7] text-[#1D1D1F] font-bold py-3 rounded-xl text-xs transition flex items-center justify-center space-x-2 shadow-sm"
                          >
                            {analyzingBugs[b.id] ? (
                              <RefreshCw className="w-4 h-4 animate-spin" />
                            ) : (
                              <>
                                <Wrench className="w-4 h-4 text-[#0071E3]" />
                                <span>Inspect Source Code & Diagnose Root Cause</span>
                              </>
                            )}
                          </button>
                        )}
                      </div>
                    ))
                  )}
                </div>
              )}

              {/* Test Plan Tab View */}
              {activeTab === 'tests' && (
                <div className="space-y-3">
                  {selectedRun.test_plan?.map((tc) => (
                    <div key={tc.id} className="bg-[#F5F5F7] border border-[#E5E5E7] rounded-2xl p-5 flex items-center justify-between shadow-sm">
                      <div>
                        <div className="flex items-center space-x-2">
                          <span className="text-xs font-mono text-[#0071E3] font-bold">{tc.id}</span>
                          <span className="text-xs px-2.5 py-0.5 bg-[#FFFFFF] text-[#1D1D1F] rounded-full border border-[#E5E5E7] font-bold">{tc.category}</span>
                        </div>
                        <h4 className="text-sm font-bold text-[#1D1D1F] mt-1">{tc.title}</h4>
                        <p className="text-xs text-[#424245] mt-0.5 font-semibold">{tc.description}</p>
                      </div>
                      <div className="text-xs text-[#6E6E73] font-mono font-bold">
                        {tc.steps?.length || 0} Steps
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Site Map Tab View */}
              {activeTab === 'sitemap' && (
                <div className="space-y-3">
                  {Object.entries(selectedRun.site_map || {}).map(([url, node]) => (
                    <div key={url} className="bg-[#F5F5F7] border border-[#E5E5E7] rounded-2xl p-5 shadow-sm">
                      <h4 className="text-sm font-bold text-[#1D1D1F] flex items-center space-x-2">
                        <Globe className="w-4 h-4 text-[#0071E3]" />
                        <span>{node.title || url}</span>
                      </h4>
                      <p className="text-xs text-[#424245] mt-1 font-mono font-bold">{url}</p>
                      <div className="mt-4 flex items-center space-x-6 text-xs text-[#6E6E73] font-bold">
                        <span>Depth: <strong className="text-[#1D1D1F]">{node.depth}</strong></span>
                        <span>Forms: <strong className="text-[#1D1D1F]">{node.forms?.length || 0}</strong></span>
                        <span>Interactive Links: <strong className="text-[#1D1D1F]">{node.interactive_selectors?.length || 0}</strong></span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Floating Apple-Style Input Controller */}
        <div className="max-w-3xl mx-auto w-full px-6 pb-6 select-none">
          <form onSubmit={handleStartRun} className="bg-[#F5F5F7] border border-[#E5E5E7] rounded-2xl p-3 shadow-lg transition space-y-3">
            <div className="flex items-center space-x-3 px-2">
              <Globe className="w-5 h-5 text-[#6E6E73]" />
              <input
                type="url"
                required
                placeholder="Enter Target Application URL (e.g. http://127.0.0.1:8888 or https://example.com)..."
                value={targetUrl}
                onChange={(e) => setTargetUrl(e.target.value)}
                className="flex-1 bg-transparent border-none text-sm text-[#1D1D1F] font-bold placeholder-[#86868B] focus:outline-none"
              />
              <button
                type="submit"
                disabled={isStarting || !targetUrl}
                className="w-10 h-10 rounded-xl bg-[#0071E3] hover:bg-[#0077ED] disabled:bg-[#86868B] text-white flex items-center justify-center transition shadow-sm flex-shrink-0"
              >
                {isStarting ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4 fill-current ml-0.5" />}
              </button>
            </div>

            {/* Parameter Pills */}
            <div className="flex items-center justify-between text-xs text-[#6E6E73] font-semibold pt-2 border-t border-[#E5E5E7] px-2">
              <div className="flex items-center space-x-6">
                <label className="flex items-center space-x-2 cursor-pointer">
                  <span>Max Depth:</span>
                  <select
                    value={maxDepth}
                    onChange={(e) => setMaxDepth(parseInt(e.target.value))}
                    className="bg-[#FFFFFF] border border-[#E5E5E7] rounded-md px-2 py-0.5 text-xs text-[#1D1D1F] font-bold focus:outline-none"
                  >
                    <option value={1}>1</option>
                    <option value={2}>2</option>
                    <option value={3}>3</option>
                    <option value={5}>5</option>
                  </select>
                </label>

                <label className="flex items-center space-x-2 cursor-pointer">
                  <span>Max Pages:</span>
                  <select
                    value={maxPages}
                    onChange={(e) => setMaxPages(parseInt(e.target.value))}
                    className="bg-[#FFFFFF] border border-[#E5E5E7] rounded-md px-2 py-0.5 text-xs text-[#1D1D1F] font-bold focus:outline-none"
                  >
                    <option value={10}>10</option>
                    <option value={25}>25</option>
                    <option value={50}>50</option>
                  </select>
                </label>
              </div>

              <div className="text-[11px] font-bold text-[#0071E3]">
                Designed for Apple-grade web applications
              </div>
            </div>
          </form>
        </div>
      </main>

      {/* New Chaos Workspace Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 apple-glass bg-black/40 z-50 flex items-center justify-center p-4">
          <div className="bg-[#FFFFFF] border border-[#E5E5E7] rounded-3xl p-8 max-w-lg w-full shadow-2xl space-y-6 animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between border-b border-[#E5E5E7] pb-4">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-2xl bg-[#0071E3]/10 text-[#0071E3] flex items-center justify-center font-bold">
                  <Zap className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-lg font-extrabold text-[#1D1D1F]">Create Chaos Workspace</h3>
                  <p className="text-xs text-[#6E6E73] font-semibold">Configure autonomous AI QA test parameters</p>
                </div>
              </div>
              <button 
                onClick={() => setIsModalOpen(false)}
                className="p-2 hover:bg-[#F5F5F7] rounded-full text-[#6E6E73] hover:text-[#1D1D1F] transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleStartRun} className="space-y-5">
              <div>
                <label className="block text-xs font-bold text-[#1D1D1F] mb-1.5">Target Application URL</label>
                <input
                  type="url"
                  required
                  placeholder="https://example.com or http://127.0.0.1:8888"
                  value={targetUrl}
                  onChange={(e) => setTargetUrl(e.target.value)}
                  className="w-full bg-[#F5F5F7] border border-[#E5E5E7] rounded-xl px-4 py-3 text-sm text-[#1D1D1F] font-bold focus:outline-none focus:border-[#0071E3] focus:bg-[#FFFFFF]"
                />
              </div>

              {/* Quick Preset Buttons */}
              <div className="space-y-1.5">
                <span className="text-[11px] font-bold text-[#6E6E73] uppercase tracking-wider block">Quick Presets</span>
                <div className="flex space-x-2">
                  <button
                    type="button"
                    onClick={() => setTargetUrl('http://127.0.0.1:8888')}
                    className="px-3 py-1.5 rounded-lg bg-[#F5F5F7] hover:bg-[#E5E5E7] text-xs font-bold text-[#0071E3] border border-[#E5E5E7] transition"
                  >
                    Local Shop (127.0.0.1:8888)
                  </button>
                  <button
                    type="button"
                    onClick={() => setTargetUrl('https://example.com')}
                    className="px-3 py-1.5 rounded-lg bg-[#F5F5F7] hover:bg-[#E5E5E7] text-xs font-bold text-[#1D1D1F] border border-[#E5E5E7] transition"
                  >
                    https://example.com
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-[#1D1D1F] mb-1.5">Max Crawl Depth</label>
                  <select
                    value={maxDepth}
                    onChange={(e) => setMaxDepth(parseInt(e.target.value))}
                    className="w-full bg-[#F5F5F7] border border-[#E5E5E7] rounded-xl px-3 py-2.5 text-xs text-[#1D1D1F] font-bold focus:outline-none"
                  >
                    <option value={1}>1 (Root Page Only)</option>
                    <option value={2}>2 (Secondary Subpages)</option>
                    <option value={3}>3 (Deep Discovery - Recommended)</option>
                    <option value={5}>5 (Full Crawl)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold text-[#1D1D1F] mb-1.5">Max Pages Cap</label>
                  <select
                    value={maxPages}
                    onChange={(e) => setMaxPages(parseInt(e.target.value))}
                    className="w-full bg-[#F5F5F7] border border-[#E5E5E7] rounded-xl px-3 py-2.5 text-xs text-[#1D1D1F] font-bold focus:outline-none"
                  >
                    <option value={10}>10 Pages</option>
                    <option value={25}>25 Pages (Recommended)</option>
                    <option value={50}>50 Pages</option>
                  </select>
                </div>
              </div>

              <button
                type="submit"
                disabled={isStarting || !targetUrl}
                className="w-full bg-[#0071E3] hover:bg-[#0077ED] disabled:bg-[#86868B] text-white font-bold py-3.5 rounded-xl text-sm transition flex items-center justify-center space-x-2 shadow-md"
              >
                {isStarting ? (
                  <RefreshCw className="w-5 h-5 animate-spin" />
                ) : (
                  <>
                    <Zap className="w-5 h-5" />
                    <span>Launch Chaos Workspace</span>
                  </>
                )}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
