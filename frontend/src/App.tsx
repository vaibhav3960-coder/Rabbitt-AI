import { useState, useRef, useEffect, useMemo } from 'react';

type Step = {
  role: string;
  content: string;
  type?: 'thought' | 'action' | 'observation' | 'decision'; // Added 'type' property
  tool?: string;
  args?: any;
};

export default function App() {
  const [icp, setIcp] = useState('We sell high-end cybersecurity training to Series B startups.');
  const [task, setTask] = useState('Find companies with recent growth signals and send a personalized outreach email to candidate@example.com that connects their expansion to our security training.');
  const [targetEmail, setTargetEmail] = useState('candidate@example.com');
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  const [history, setHistory] = useState<Step[]>([]);
  const [finalResult, setFinalResult] = useState<string | null>(null);
  const [isApproving, setIsApproving] = useState(false);
  const [isApproved, setIsApproved] = useState(false);
  const [stats, setStats] = useState({ signals_detected: 0, emails_generated: 0, emails_sent: 0 });
  
  const consoleEndRef = useRef<HTMLDivElement>(null);

  const fetchStats = async () => {
    try {
      const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_BASE_URL}/api/stats`);
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (e) {}
  };

  useEffect(() => {
    fetchStats();
  }, []);

  useEffect(() => {
    consoleEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [history]);

  const runAgent = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsRunning(true);
    setError(null);
    setSuccess(null);
    setHistory([]);
    setFinalResult(null);

    try {
      const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_BASE_URL}/api/run-agent`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ icp, task, target_email: targetEmail }),
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const data = await response.json();
      
      if (data.error) {
        throw new Error(data.error);
      }

      setHistory(data.history || []);
      setFinalResult(data.final_result || 'Agent execution completed successfully.');
      setIsApproved(false);
      fetchStats();
      
    } catch (err: any) {
      setError(err.message || 'An error occurred.');
    } finally {
      setIsRunning(false);
    }
  };

  const handleApproveSend = async () => {
    setIsApproving(true);
    setError(null);
    try {
      const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const emailCopy = finalResult?.replace(/\\n/g, '\n').replace(/^["']|["']$/g, '').replace('--- DRAFTED EMAIL ---', '') || "";

       // Extract target company from history (tool_signal_harvester content usually has it)
       const harvesterStep = history.find(s => s.tool === 'tool_signal_harvester' && s.role === 'assistant');
       let targetCompany = "Unknown";
       if (harvesterStep && harvesterStep.args) {
         try {
           const args = typeof harvesterStep.args === 'string' ? JSON.parse(harvesterStep.args) : harvesterStep.args;
           targetCompany = args.target || "Unknown";
         } catch (e) {}
       }
 
       const response = await fetch(`${API_BASE_URL}/api/approve-send`, {
         method: 'POST',
         headers: { 'Content-Type': 'application/json' },
         body: JSON.stringify({ 
           email_copy: emailCopy, 
           target_email: targetEmail,
           target_company: targetCompany
         }),
       });

      if (!response.ok) throw new Error('Failed to send approval');
      
      const data = await response.json();
      setSuccess(data.message);
      setIsApproved(true);
      fetchStats();
    } catch (err: any) {
      setError(err.message || 'Failed to approve and send.');
    } finally {
      setIsApproving(false);
    }
  };

  const harvestedSignals = history.find(s => s.tool === 'tool_signal_harvester' && s.role === 'tool')?.content;
  let parsedSignals = null;
  if (harvestedSignals) {
    try {
      parsedSignals = JSON.parse(harvestedSignals);
    } catch (e) {}
  }

  // Transform history into granular steps for display
  const steps = useMemo(() => {
    const transformedSteps: Step[] = [];
    history.forEach(step => {
      if (step.role === 'assistant') {
        // Assistant messages can be thoughts or actions
        const thoughtMatch = step.content.match(/^Thought:\s*(.*)/s);
        if (thoughtMatch) {
          transformedSteps.push({
            ...step,
            type: 'thought',
            content: thoughtMatch[1].trim(),
          });
        }
        if (step.tool) {
          transformedSteps.push({
            ...step,
            type: 'action',
            content: `Calling tool: ${step.tool}`,
          });
        }
      } else if (step.role === 'tool') {
        // Tool messages are observations
        transformedSteps.push({
          ...step,
          type: 'observation',
          content: step.content,
        });
      }
    });
    if (finalResult) {
      transformedSteps.push({
        role: 'assistant',
        type: 'decision',
        content: finalResult.replace(/\\n/g, '\n').replace(/^["']|["']$/g, '').replace('--- DRAFTED EMAIL ---', ''),
      });
    }
    return transformedSteps;
  }, [history, finalResult]);

  // The getAgentStep function is no longer directly used for the main execution log display
  // but might be kept if other parts of the UI still rely on it.
  const getAgentStep = (step: Step) => {
    if (step.tool === 'tool_signal_harvester') return { num: 1, label: "Harvesting signals..." };
    if (step.tool === 'tool_research_analyst') return { num: 2, label: "Generating research brief..." };
    if (step.tool === 'tool_outreach_automated_sender') return { num: 3, label: "Drafting outreach email..." };
    return null;
  };

  return (
    <div className="min-h-screen bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-900 via-[#0b1120] to-black p-4 md:p-8 flex flex-col items-center">
      
      <div className="w-full max-w-6xl flex flex-col gap-6 shadow-[0_0_100px_rgba(79,70,229,0.15)] rounded-[2.5rem] p-10 border border-white/5 bg-slate-900/40 backdrop-blur-2xl">
        <header className="flex flex-col items-center justify-center mb-8 text-center">
          <div className="inline-flex items-center gap-2 rounded-full px-4 py-1.5 text-xs font-bold tracking-widest uppercase text-indigo-400 bg-indigo-500/10 mb-6 border border-indigo-500/20 shadow-[0_0_20px_rgba(99,102,241,0.1)]">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
            </span>
            Autonomous Engine 2.0
          </div>
          <h1 className="text-6xl font-black tracking-tight text-white mb-4">
            Fire<span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-500">Reach</span>
          </h1>
          <p className="text-slate-400 mt-2 max-w-xl text-lg leading-relaxed font-medium">
            The next-generation autonomous SDR. Capture signals, reason through context, and orchestrate outreach at scale.
          </p>
        </header>

        {/* Phase 6: Campaign Stats Dashboard */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
          {[
            { label: "Signals Detected", value: stats.signals_detected, color: "from-blue-500 to-indigo-600" },
            { label: "Emails Generated", value: stats.emails_generated, color: "from-purple-500 to-pink-600" },
            { label: "Emails Sent", value: stats.emails_sent, color: "from-emerald-500 to-teal-600" }
          ].map((stat, i) => (
            <div key={i} className="relative group overflow-hidden bg-white/5 border border-white/10 rounded-3xl p-6 transition-all hover:border-white/20 hover:bg-white/10">
              <div className={`absolute -right-4 -top-4 w-24 h-24 bg-gradient-to-br ${stat.color} opacity-10 blur-2xl group-hover:opacity-20 transition-opacity`}></div>
              <p className="text-slate-400 text-sm font-bold uppercase tracking-wider mb-2">{stat.label}</p>
              <h3 className="text-4xl font-black text-white">{stat.value}</h3>
            </div>
          ))}
        </div>

        {success && (
          <div className="bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 px-6 py-4 rounded-2xl flex items-center gap-3 animate-in fade-in zoom-in duration-300 shadow-[0_0_40px_rgba(16,185,129,0.1)]">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M5 13l4 4L19 7"></path></svg>
            <span className="font-bold">{success}</span>
          </div>
        )}

        {error && (
          <div className="bg-red-500/10 border border-red-500/30 text-red-400 px-6 py-4 rounded-2xl flex items-center gap-3 animate-in fade-in zoom-in duration-300">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M6 18L18 6M6 6l12 12"></path></svg>
            <span className="font-bold">{error}</span>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
          
          <div className="lg:col-span-5 flex flex-col gap-6">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-black text-white flex items-center gap-3">
                Parameters
              </h2>
            </div>
            
            <form onSubmit={runAgent} className="flex flex-col gap-6 bg-white/5 p-6 rounded-3xl border border-white/5">
              <div className="flex flex-col gap-3">
                <label className="text-sm font-bold text-slate-400 uppercase tracking-wider">Ideal Customer Profile</label>
                <textarea 
                  value={icp}
                  onChange={(e) => setIcp(e.target.value)}
                  className="w-full bg-black/40 border border-slate-800 rounded-2xl px-5 py-4 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50 transition-all resize-none font-medium leading-relaxed shadow-inner"
                  rows={3}
                  required
                />
              </div>
              <div className="flex flex-col gap-3">
                <label className="text-sm font-bold text-slate-400 uppercase tracking-wider">Task Objective</label>
                <textarea 
                  value={task}
                  onChange={(e) => setTask(e.target.value)}
                  className="w-full bg-black/40 border border-slate-800 rounded-2xl px-5 py-4 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50 transition-all resize-none font-medium leading-relaxed shadow-inner"
                  rows={3}
                  required
                />
              </div>
              <div className="flex flex-col gap-3">
                <label className="text-sm font-bold text-slate-400 uppercase tracking-wider">Candidate Email</label>
                <input 
                  type="email"
                  value={targetEmail}
                  onChange={(e) => setTargetEmail(e.target.value)}
                  className="w-full bg-black/40 border border-slate-800 rounded-2xl px-5 py-4 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50 transition-all font-medium shadow-inner"
                  required
                />
              </div>

              <button 
                type="submit" 
                disabled={isRunning}
                className="group relative w-full flex justify-center py-5 px-6 border border-transparent text-lg font-black rounded-2xl text-white bg-indigo-600 hover:bg-indigo-500 focus:outline-none transition-all duration-300 overflow-hidden shadow-[0_20px_40px_rgba(79,70,229,0.3)] disabled:opacity-50 active:scale-95"
              >
                {isRunning ? (
                  <span className="flex items-center gap-3">
                    <svg className="animate-spin h-6 w-6 text-white" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    ORCHESTRATING...
                  </span>
                ) : (
                  'INITIATE DEPLOYMENT'
                )}
              </button>
            </form>
          </div>

          <div className="lg:col-span-7 flex flex-col gap-8">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-black text-white flex items-center gap-3">
                Execution Engine
              </h2>
            </div>
            
                            {agentStep.num}
                          </div>
                          <div className="pt-2">
                            <h4 className="text-white font-bold leading-none mb-1">Step {agentStep.num}: {agentStep.label}</h4>
                            <p className="text-slate-500 text-xs font-mono">Dispatched tool: {step.tool}</p>
                          </div>
                        </div>
                      );
                    }
                    return null;
                  })}
                  
                  {isRunning && (
                    <div className="flex gap-4 items-start animate-pulse">
                      <div className="w-10 h-10 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center shrink-0">
                        <div className="w-2 h-2 bg-indigo-400 rounded-full animate-ping"></div>
                      </div>
                      <div className="pt-2">
                        <h4 className="text-slate-400 font-bold leading-none">Processing intent...</h4>
                      </div>
                    </div>
                  )}
                  <div ref={consoleEndRef} />
                </div>
              </div>

              {parsedSignals && (
                <div className="mt-6 pt-6 border-t border-white/5 animate-in fade-in zoom-in duration-700">
                   <h3 className="text-xs font-black text-indigo-400 uppercase tracking-[0.2em] mb-4">Signals Harvested</h3>
                   <div className="bg-indigo-500/5 rounded-2xl border border-indigo-500/10 p-5 space-y-4">
                     {Object.entries(parsedSignals).map(([company, data]: any) => (
                       <div key={company}>
                         <h4 className="text-white font-bold mb-3 flex items-center justify-between">
                           <div className="flex items-center gap-2">
                            <div className="w-2 h-2 bg-green-400 rounded-full shadow-[0_0_8px_rgba(74,222,128,0.5)]"></div>
                            {company}
                           </div>
                           <span className="text-[10px] bg-indigo-500/20 text-indigo-400 px-2 py-0.5 rounded-full border border-indigo-500/30 uppercase tracking-tighter">Verified Signals</span>
                         </h4>
                         <ul className="grid grid-cols-1 gap-4">
                           {data.signals?.map((sig: any, i: number) => (
                             <li key={i} className="group/sig flex flex-col gap-2 bg-black/30 p-4 rounded-2xl border border-white/5 hover:border-indigo-500/30 transition-all">
                               <div className="flex items-start justify-between gap-3">
                                 <h5 className="text-slate-200 font-bold text-sm leading-tight flex-1 line-clamp-1">{sig.title || "Untitled Signal"}</h5>
                                 {sig.link && (
                                   <div className="flex flex-col items-end gap-1">
                                     <a 
                                       href={sig.link} 
                                       target="_blank" 
                                       rel="noopener noreferrer" 
                                       className="text-[10px] text-indigo-400 hover:text-indigo-300 flex items-center gap-1 shrink-0 bg-indigo-500/10 px-2 py-1 rounded-lg border border-indigo-500/20"
                                     >
                                       View Source
                                       <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path></svg>
                                     </a>
                                     <span className="text-[9px] text-slate-500 uppercase tracking-widest font-medium">Source: {new URL(sig.link).hostname.replace('www.', '')}</span>
                                   </div>
                                 )}
                               </div>
                               {sig.snippet && (
                                 <p className="text-slate-500 text-xs leading-relaxed line-clamp-2">
                                   {sig.snippet}
                                 </p>
                               )}
                             </li>
                           ))}
                         </ul>
                       </div>
                     ))}
                   </div>
                </div>
              )}
            </div>
            
            {finalResult && (
              <div className="animate-in fade-in slide-in-from-bottom-8 duration-1000">
                <div className="bg-gradient-to-br from-indigo-600 to-purple-700 p-[1px] rounded-[2rem] shadow-2xl">
                  <div className="bg-[#0b1120] rounded-[1.95rem] p-8">
                    <h3 className="text-xl font-black text-white mb-6 flex items-center gap-3">
                      Automated Outreach Draft
                    </h3>
                    <div className="text-sm font-medium text-slate-300 whitespace-pre-wrap bg-slate-900/50 p-6 rounded-2xl border border-white/5 leading-loose shadow-inner">
                      {finalResult.replace(/\\n/g, '\n').replace(/^["']|["']$/g, '').replace('--- DRAFTED EMAIL ---', '')}
                    </div>

                    {!isApproved && (
                      <button
                        onClick={handleApproveSend}
                        disabled={isApproving}
                        className="mt-6 w-full py-4 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-2xl transition-all shadow-[0_10px_30px_rgba(16,185,129,0.3)] flex items-center justify-center gap-3 active:scale-95 disabled:opacity-50"
                      >
                        {isApproving ? (
                          <>
                            <svg className="animate-spin h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            DISPATCHING...
                          </>
                        ) : (
                          <>
                            <svg className="w-5 h-5 font-bold" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M5 13l4 4L19 7"></path>
                            </svg>
                            APPROVE & SEND
                          </>
                        )}
                      </button>
                    )}
                  </div>
                </div>
              </div>
            )}

          </div>
        </div>
      </div>

      <style>{`
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #334155; border-radius: 10px; }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #475569; }
      `}</style>
    </div>
  );
}
