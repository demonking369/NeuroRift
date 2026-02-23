'use client';

import { useMemo } from 'react';
import { Globe, ShieldAlert, Wifi, Lock, MapPin } from 'lucide-react';
import { useWebModeContext } from '@/components/webmode/WebModeProvider';
import { useNeuroRift } from '@/lib/hooks';
import { cn } from '@/lib/utils';

export function OnlineModePanel() {
    const { config, updateConfig } = useWebModeContext();
    const { systemHealth } = useNeuroRift();

    const publicUrl = useMemo(() => {
        if (!config.onlineMode.enabled) return null;
        return `https://nr-${Math.floor(Math.random() * 9999)}.tunnel.neurorift.ai`;
    }, [config.onlineMode.enabled]);

    return (
        <div className="space-y-4">
            {/* Header / Toggle */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs uppercase tracking-[0.3em] text-neuro-text-muted">
                    <Globe className="w-4 h-4 text-cyan-300" />
                    Secure Uplink
                </div>
                <button
                    onClick={() => updateConfig('onlineMode.enabled', !config.onlineMode.enabled)}
                    className={cn(
                        'px-3 py-1 rounded-full text-xs border transition-all duration-300',
                        config.onlineMode.enabled
                            ? 'border-emerald-400/50 text-emerald-200 bg-emerald-500/10 shadow-[0_0_10px_-2px_rgba(16,185,129,0.3)]'
                            : 'border-neuro-border/60 text-neuro-text-muted bg-neuro-surface/50'
                    )}
                >
                    {config.onlineMode.enabled ? 'Connected' : 'Offline'}
                </button>
            </div>

            {config.onlineMode.enabled ? (
                <div className="space-y-3 animate-in fade-in slide-in-from-top-2 duration-300">
                    {/* Tunnel Topology Visualization */}
                    <div className="relative h-24 rounded-xl border border-cyan-500/30 bg-cyan-950/20 overflow-hidden flex items-center justify-center p-4">
                        {/* Animated Connection Line */}
                        <div className="absolute top-1/2 left-4 right-4 h-[1px] bg-cyan-800">
                            <div className="absolute top-0 bottom-0 w-8 bg-cyan-400 blur-sm animate-connection-pulse" />
                        </div>

                        {/* Nodes */}
                        <div className="relative z-10 w-full flex justify-between items-center">
                            {/* Local Node */}
                            <div className="flex flex-col items-center gap-1 group cursor-help">
                                <div className="w-8 h-8 rounded-full bg-cyan-950 border border-cyan-400 flex items-center justify-center shadow-[0_0_15px_-2px_rgba(34,211,238,0.4)]">
                                    <Lock className="w-3 h-3 text-cyan-300" />
                                </div>
                                <span className="text-[9px] uppercase tracking-widest text-cyan-200 bg-black/40 px-1 rounded">Local</span>
                            </div>

                            {/* Relay (Decorative) */}
                            <div className="w-2 h-2 rounded-full bg-cyan-600 animate-ping" />

                            {/* Remote Node */}
                            <div className="flex flex-col items-center gap-1 group cursor-help">
                                <div className="w-8 h-8 rounded-full bg-cyan-950 border border-cyan-400 flex items-center justify-center shadow-[0_0_15px_-2px_rgba(34,211,238,0.4)]">
                                    <Globe className="w-3 h-3 text-cyan-300" />
                                </div>
                                <span className="text-[9px] uppercase tracking-widest text-cyan-200 bg-black/40 px-1 rounded">Tunnel</span>
                            </div>
                        </div>
                    </div>

                    {/* Metrics & Info */}
                    <div className="grid grid-cols-2 gap-3">
                        <div className="rounded-lg border border-neuro-border/60 bg-neuro-bg/40 p-3 flex flex-col gap-1">
                            <span className="text-[10px] uppercase text-neuro-text-muted flex items-center gap-1">
                                <Wifi className="w-3 h-3" /> Latency
                            </span>
                            <span className="text-xl font-light text-neuro-text-primary tabular-nums">
                                {systemHealth.latency} <span className="text-xs text-neuro-text-muted">ms</span>
                            </span>
                        </div>
                        <div className="rounded-lg border border-neuro-border/60 bg-neuro-bg/40 p-3 flex flex-col gap-1">
                            <span className="text-[10px] uppercase text-neuro-text-muted flex items-center gap-1">
                                <MapPin className="w-3 h-3" /> Region
                            </span>
                            <span className="text-xs font-mono text-cyan-300">us-east-4</span>
                        </div>
                    </div>

                    {/* Controls & URL */}
                    <div className="rounded-xl border border-neuro-border/60 bg-neuro-bg/60 p-4 space-y-3">
                        <div className="flex items-center justify-between">
                            <span className="text-xs uppercase tracking-[0.3em] text-neuro-text-muted">Access Level</span>
                            <select
                                value={config.onlineMode.access}
                                onChange={event => updateConfig('onlineMode.access', event.target.value)}
                                className="rounded-lg border border-neuro-border/60 bg-neuro-surface/70 px-3 py-2 text-xs text-neuro-text-primary"
                            >
                                <option value="read">Read-only</option>
                                <option value="control">Control</option>
                            </select>
                        </div>
                        {publicUrl && (
                            <div className="rounded-lg border border-emerald-400/30 bg-emerald-500/10 px-3 py-2 text-xs text-emerald-100 break-all font-mono">
                                <div className="uppercase tracking-[0.3em] text-[10px] text-emerald-200 mb-1">Public Endpoint</div>
                                {publicUrl}
                            </div>
                        )}
                        <div className="flex items-start gap-2 text-xs text-rose-200 opacity-80">
                            <ShieldAlert className="w-4 h-4 mt-0.5 shrink-0" />
                            <span>Remote exposure logged. Access restricted to whitelisted IPs.</span>
                        </div>
                    </div>
                </div>
            ) : (
                <div className="p-8 border border-dashed border-neuro-border/40 rounded-xl flex flex-col items-center text-center text-neuro-text-muted bg-neutral-900/20">
                    <Globe className="w-8 h-8 mb-2 opacity-20" />
                    <p className="text-xs">Uplink disabled. Interface is air-gapped.</p>
                </div>
            )}
        </div>
    );
}
