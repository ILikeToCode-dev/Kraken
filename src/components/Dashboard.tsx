import React, { useState, useEffect, useRef } from 'react';
import { 
  ShieldAlert, ShieldCheck, Activity, Globe, Crosshair, 
  Server, Zap, Terminal as TerminalIcon, History, Link as LinkIcon, Link2Off
} from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

export default function Dashboard() {
  const [backendUrl, setBackendUrl] = useState("http://127.0.0.1:5000");
  const [isConnected, setIsConnected] = useState(false);
  
  const [data, setData] = useState<any[]>([]);
  const [logs, setLogs] = useState<string[]>([
    "[" + new Date().toISOString() + "] KRAKEN SYSTEM INITIALIZED (FRONTEND)",
    "[" + new Date().toISOString() + "] Waiting for connection to Kraken Core...",
  ]);
  
  const [state, setState] = useState({
    current_ip: "UNKNOWN",
    pps: 0,
    bandwidth: 0,
    active_traps: 0,
    status: "DISCONNECTED",
    rotations: [] as any[]
  });
  
  const endRef = useRef<HTMLDivElement>(null);

  // Auto-scroll logs
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  // Real API Fetch Loop
  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await fetch(`${backendUrl}/api/stats`);
        if (!response.ok) throw new Error("Network response was not ok");
        const json = await response.json();
        
        setIsConnected(true);
        setState({
          current_ip: json.current_ip || "UNKNOWN",
          pps: json.pps || 0,
          bandwidth: json.bandwidth || 0,
          active_traps: json.active_traps || 0,
          status: json.status || "SECURE",
          rotations: json.rotations || []
        });

        if (json.logs && json.logs.length > 0) {
           setLogs(json.logs);
        }

        // Update Chart Data
        setData(d => {
          const newEl = { time: new Date().toLocaleTimeString().split(' ')[0], pps: json.pps || 0 };
          let res = [...d, newEl];
          if (res.length > 20) res = res.slice(1);
          return res;
        });

      } catch (error) {
        setIsConnected(false);
        setState(prev => ({ ...prev, status: "DISCONNECTED", pps: 0, bandwidth: 0 }));
      }
    };

    fetchStats(); // initial fetch
    const interval = setInterval(fetchStats, 1000); // Poll every second
    return () => clearInterval(interval);
  }, [backendUrl]);

  const isAlert = state.status !== "SECURE" && state.status !== "DISCONNECTED";

  return (
    <div className="h-screen w-full bg-black text-white font-sans flex flex-col overflow-hidden select-none">
      
      {/* HEADER SECTION */}
      <header className="p-4 md:p-8 border-b border-white/10 flex flex-col md:flex-row justify-between items-start md:items-end gap-4 shrink-0">
        <div className="flex items-center gap-3">
          <div className="flex flex-col">
            <span className="text-xs tracking-[0.4em] uppercase opacity-50 mb-1 flex items-center gap-2">
              <Crosshair className="w-3 h-3" /> Science Exhibition 2026
            </span>
            <h1 className="text-4xl md:text-5xl font-black tracking-tighter leading-none italic">PROJECT KRAKEN</h1>
          </div>
        </div>
        
        <div className="flex gap-6 md:gap-12 text-right">
          <div className="flex flex-col text-left md:text-right">
            <span className="text-[10px] uppercase tracking-widest opacity-40">Core Backend Node</span>
            <div className="flex items-center gap-2 md:justify-end mt-1 text-white/80 bg-white/5 border border-white/10 rounded px-2 py-1">
              {isConnected ? <LinkIcon className="w-3 h-3 text-emerald-400" /> : <Link2Off className="w-3 h-3 text-slate-500" />}
              <input 
                type="text" 
                value={backendUrl}
                onChange={(e) => setBackendUrl(e.target.value)}
                className="bg-transparent border-none outline-none text-xs font-mono text-white/80 w-32 focus:w-48 transition-all"
                placeholder="http://127.0.0.1:5000"
              />
            </div>
          </div>
          <div className="flex flex-col text-left md:text-right">
            <span className="text-[10px] uppercase tracking-widest opacity-40">System Status</span>
            <div className={`flex items-center gap-2 md:justify-end mt-1 ${isAlert ? 'text-red-500' : isConnected ? 'text-emerald-400' : 'text-slate-500'}`}>
              {!isConnected && <Server className="w-4 h-4" />}
              {isConnected && (isAlert ? <ShieldAlert className="w-4 h-4 animate-pulse" /> : <ShieldCheck className="w-4 h-4" />)}
              <span className="text-sm font-mono font-bold uppercase">{state.status}</span>
            </div>
          </div>
        </div>
      </header>

      {/* DASHBOARD GRIDS */}
      <main className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-px bg-white/10 overflow-hidden min-h-0">
        
        {/* LEFT COLUMN - STATS & CHART */}
        <section className="col-span-1 lg:col-span-8 bg-black flex flex-col justify-between relative border-r border-white/10 overflow-hidden">
          
          <div className="absolute -left-4 top-0 text-[12rem] md:text-[20rem] font-black leading-none opacity-5 pointer-events-none select-none">
            KRAKEN
          </div>
          
          <div className="flex flex-col relative z-10 p-6 md:p-10 flex-1 min-h-0">
            <div className="flex justify-between items-start mb-4">
               <div>
                  <span className={`text-xs uppercase tracking-[0.3em] font-semibold flex items-center gap-2 ${isAlert ? 'text-red-400' : 'text-emerald-400'}`}>
                    <Activity className="w-4 h-4" /> Live Traffic Analysis
                  </span>
                  <div className="flex items-baseline gap-4 mt-4">
                    <span className="text-7xl md:text-[140px] font-light leading-none tracking-tighter">{state.pps}</span>
                    <span className="text-2xl font-mono opacity-60">PPS</span>
                  </div>
               </div>
               
               <div className="text-right flex flex-col justify-end mt-2 md:mt-0">
                  <span className="text-[10px] uppercase tracking-widest opacity-40 flex items-center gap-2 justify-end">
                    <Zap className="w-3 h-3" /> Bandwidth (Rx)
                  </span>
                  <span className="text-xl md:text-3xl font-mono opacity-80 mt-2">{state.bandwidth} <span className="text-sm">Mbps</span></span>
               </div>
            </div>
            
            <div className="flex-1 w-full relative mt-4 min-h-[100px]">
              <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data} margin={{ top: 10, right: 0, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorPps" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={isAlert ? '#ef4444' : '#10b981'} stopOpacity={0.3}/>
                    <stop offset="95%" stopColor={isAlert ? '#ef4444' : '#10b981'} stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis dataKey="time" stroke="#334155" fontSize={10} tickMargin={10} axisLine={false} tickLine={false} />
                <YAxis stroke="#334155" fontSize={10} axisLine={false} tickLine={false} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#000', borderColor: '#333', fontSize: '12px', borderRadius: 0 }}
                  itemStyle={{ color: isAlert ? '#ef4444' : '#10b981' }}
                />
                <Area 
                  type="step" 
                  dataKey="pps" 
                  stroke={isAlert ? '#ef4444' : '#10b981'} 
                  strokeWidth={2}
                  fillOpacity={1} 
                  fill="url(#colorPps)" 
                  isAnimationActive={false}
                />
              </AreaChart>
            </ResponsiveContainer>
            </div>
          </div>

          <div className="grid grid-cols-2 lg:grid-cols-3 gap-6 md:gap-8 border-t border-white/10 p-6 md:p-10 bg-black shrink-0">
            <div className="flex flex-col gap-2">
              <span className="text-[10px] uppercase tracking-widest opacity-40 flex items-center gap-2">
                <Globe className="w-3 h-3" /> Active Identity (IP)
              </span>
              <span className="text-xl md:text-2xl font-mono tracking-tight text-white">{state.current_ip}</span>
              <div className="h-1 bg-emerald-500 w-full mt-2"></div>
            </div>
            <div className="flex flex-col gap-2">
              <span className="text-[10px] uppercase tracking-widest opacity-40 flex items-center gap-2">
                <History className="w-3 h-3" /> Rotation Epoch
              </span>
              <span className="text-xl md:text-2xl font-mono tracking-tight text-white">{state.rotations.length} shifts</span>
              <div className="h-1 bg-white/20 w-1/2 mt-2"></div>
            </div>
            <div className="col-span-2 lg:col-span-1 flex flex-col gap-2">
              <span className="text-[10px] uppercase tracking-widest opacity-40 flex items-center gap-2">
                <TerminalIcon className="w-3 h-3" /> Bots Frozen (Tar-Pit)
              </span>
              <span className="text-xl md:text-2xl font-mono tracking-tight text-red-500">{state.active_traps} units</span>
              <div className="h-1 bg-red-500 w-3/4 mt-2 hover:w-full transition-all duration-1000"></div>
            </div>
          </div>
        </section>

        {/* RIGHT COLUMN - LOGS */}
        <section className="col-span-1 lg:col-span-4 bg-[#0a0a0a] flex flex-col overflow-hidden">
          
          <div className="flex flex-col flex-1 min-h-[50%] overflow-hidden">
            <div className="p-4 md:p-6 border-b border-white/10 shrink-0">
              <h3 className="text-xs uppercase tracking-[0.3em] font-semibold flex items-center gap-2 text-white">
                <span className="w-2 h-2 bg-red-600 rounded-full animate-pulse"></span> System Logs
              </h3>
            </div>
            <div className="flex-1 p-4 md:p-6 font-mono text-[11px] leading-relaxed overflow-y-auto opacity-80 custom-scrollbar flex flex-col gap-2">
              {logs.map((log, i) => (
                <p key={i} className={`${log.includes('WARNING') || log.includes('CRITICAL') || log.includes('REDIRECT') ? 'text-red-500 font-bold' : log.includes('OCI') || log.includes('DNS') ? 'text-yellow-400' : 'text-emerald-400'}`}>
                  {log}
                </p>
              ))}
              <div ref={endRef} />
            </div>
          </div>

          <div className="flex flex-col flex-1 min-h-[30%] overflow-hidden border-t border-white/10 bg-[#000]">
             <div className="p-4 md:p-6 border-b border-white/10 flex items-center justify-between shrink-0">
              <h3 className="text-xs uppercase tracking-[0.3em] font-semibold text-white/50 flex items-center gap-2">
                <History className="w-3 h-3" /> Target Rotation History
              </h3>
            </div>
            <div className="flex-1 p-4 md:p-6 overflow-y-auto w-full flex flex-col gap-4 custom-scrollbar">
              {state.rotations.length === 0 ? (
                <div className="text-xs font-mono text-slate-500 italic h-full flex items-center justify-center">
                  NO ROTATIONS RECORDED
                </div>
              ) : (
                state.rotations.map((r, i) => (
                  <div key={i} className="flex flex-col pb-3 border-b border-white/10 last:border-0 text-xs gap-1 font-mono">
                    <div className="flex justify-between items-center text-[10px] text-slate-400">
                      <span>{r.timestamp}</span>
                      <span className="text-red-400">Peak: {r.trigger_pps} pps</span>
                    </div>
                    <div className="flex flex-wrap items-center gap-2 text-slate-300 mt-1">
                      <span className="line-through opacity-50">{r.from_ip}</span>
                      <span className="text-emerald-500 font-bold">→</span>
                      <span className="text-white font-bold">{r.to_ip}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="p-6 md:p-8 bg-white text-black shrink-0 relative overflow-hidden group border-t border-white/10">
            <div className="absolute inset-0 bg-red-500/10 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none"></div>
            <div className="flex flex-col gap-1 relative z-10">
              <span className="text-[10px] uppercase font-bold tracking-widest text-black/60 flex items-center gap-2">
                <ShieldCheck className="w-3 h-3" /> Trap Status
              </span>
              <div className="flex justify-between items-baseline mt-1">
                <span className="text-3xl font-black italic">TAR-PIT</span>
                <span className="font-mono font-bold text-red-600">80/443</span>
              </div>
              <p className="text-[10px] mt-2 opacity-70 leading-tight uppercase font-medium">Responding with TCP Window Size 0 to exhaustive bot signatures</p>
            </div>
          </div>
        </section>

      </main>
    </div>
  );
}
