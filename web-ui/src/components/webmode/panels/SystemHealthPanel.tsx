'use client';

import { useEffect, useState } from 'react';
import { useWebModeContext } from '@/components/webmode/WebModeProvider';
import { Activity, Cpu, HardDrive, Server, RefreshCw } from 'lucide-react';
import { SystemMetrics, SystemState } from '@/lib/webmode/adapter/interface';
import { cn } from '@/lib/utils';

export function SystemHealthPanel() {
    const { adapter } = useWebModeContext();
    const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
    const [state, setState] = useState<SystemState | null>(null);
    const [loading, setLoading] = useState(false);

    const refresh = async () => {
        setLoading(true);
        try {
            const [m, s] = await Promise.all([
                adapter.getSystemMetrics(),
                adapter.getSystemState()
            ]);
            setMetrics(m);
            setState(s);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        refresh();
        const interval = setInterval(refresh, 5000);
        return () => clearInterval(interval);
    }, [adapter]);

    if (!metrics || !state) return (
        <div className="flex items-center justify-center h-full text-neuro-text-muted text-xs animate-pulse">
            Initializing System Telemetry...
        </div>
    );

    return (
        <div className="h-full flex flex-col gap-4 p-2">
            <div className="flex items-center justify-between shrink-0">
                <div className="flex items-center gap-2">
                    <Activity className="w-4 h-4 text-emerald-400" />
                    <span className="text-xs font-medium uppercase tracking-wider text-cyan-100">System Health</span>
                </div>
                <button onClick={refresh} className={cn("text-neuro-text-muted hover:text-cyan-300 transition-colors", loading && "animate-spin")}>
                    <RefreshCw className="w-3 h-3" />
                </button>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
                {/* CPU */}
                <div className="p-3 bg-neuro-surface/40 rounded-lg border border-neuro-border/30 backdrop-blur-sm">
                    <div className="flex items-center gap-2 mb-2 text-neuro-text-secondary">
                        <Cpu className="w-3 h-3" />
                        <span className="uppercase tracking-wide text-[10px]">CPU Load</span>
                    </div>
                    <div className="flex items-end justify-between">
                        <span className="text-lg font-mono text-cyan-100">{metrics.cpu.toFixed(1)}%</span>
                        <div className="h-1.5 w-16 bg-black/40 rounded-full overflow-hidden">
                            <div className="h-full bg-cyan-500 rounded-full transition-all duration-500" style={{ width: `${metrics.cpu}%` }} />
                        </div>
                    </div>
                </div>

                {/* RAM */}
                <div className="p-3 bg-neuro-surface/40 rounded-lg border border-neuro-border/30 backdrop-blur-sm">
                    <div className="flex items-center gap-2 mb-2 text-neuro-text-secondary">
                        <HardDrive className="w-3 h-3" />
                        <span className="uppercase tracking-wide text-[10px]">Memory</span>
                    </div>
                    <div className="flex items-end justify-between">
                        <span className="text-lg font-mono text-purple-200">{metrics.memory.toFixed(1)}%</span>
                        <div className="h-1.5 w-16 bg-black/40 rounded-full overflow-hidden">
                            <div className="h-full bg-purple-500 rounded-full transition-all duration-500" style={{ width: `${metrics.memory}%` }} />
                        </div>
                    </div>
                </div>

                {/* AI / Ollama */}
                <div className="col-span-2 p-3 bg-neuro-surface/40 rounded-lg border border-neuro-border/30 backdrop-blur-sm flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className={cn("w-2 h-2 rounded-full shadow-[0_0_8px_currentColor]",
                            state.ollama.status === 'connected' ? "bg-emerald-500 text-emerald-500" : "bg-red-500 text-red-500"
                        )} />
                        <div className="flex flex-col">
                            <span className="text-xs text-neuro-text-primary font-medium tracking-wide">AI Core (Ollama)</span>
                            <span className="text-[10px] text-neuro-text-muted font-mono">{state.ollama.model}</span>
                        </div>
                    </div>
                    <div className="text-[10px] bg-black/20 px-2 py-1 rounded border border-white/5 font-mono text-neuro-text-secondary uppercase">
                        {state.ollama.status}
                    </div>
                </div>

                {/* Network */}
                <div className="col-span-2 p-3 bg-neuro-surface/40 rounded-lg border border-neuro-border/30 backdrop-blur-sm">
                    <div className="flex items-center gap-2 mb-2 text-neuro-text-secondary">
                        <Server className="w-3 h-3" />
                        <span className="uppercase tracking-wide text-[10px]">Network I/O</span>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <span className="text-[9px] text-neuro-text-muted block mb-0.5">INBOUND</span>
                            <span className="font-mono text-emerald-300">{(metrics.network.rx / 1024).toFixed(1)} KB/s</span>
                        </div>
                        <div>
                            <span className="text-[9px] text-neuro-text-muted block mb-0.5">OUTBOUND</span>
                            <span className="font-mono text-cyan-300">{(metrics.network.tx / 1024).toFixed(1)} KB/s</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
