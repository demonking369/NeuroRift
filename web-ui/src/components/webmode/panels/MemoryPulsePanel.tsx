'use client';

import { useNeuroRift } from '@/lib/hooks';
import { cn } from '@/lib/utils';
import { BrainCircuit, Activity, Zap } from 'lucide-react';

export function MemoryPulsePanel() {
    // We now use the extended systemHealth which contains simulated memory_metrics
    const { systemHealth } = useNeuroRift();
    const metrics = systemHealth.memory_metrics || { usage: 0, reinforcement: 0, decay: 0, type: 'episodic' };

    return (
        <div className="space-y-4">
            {/* Header with Organic Pulse Indicator */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-neuro-text-muted">
                    <BrainCircuit className={cn(
                        "w-4 h-4",
                        metrics.usage > 0.8 ? "text-rose-400 animate-pulse" : "text-cyan-400"
                    )} />
                    <span>Cognitive State</span>
                </div>
                <div className="flex items-center gap-1 text-[10px] uppercase tracking-wider text-neuro-text-muted">
                    <Activity className="w-3 h-3 text-emerald-400" />
                    <span>Active</span>
                </div>
            </div>

            {/* Split Memory Visualization */}
            <div className="grid grid-cols-2 gap-3">
                {/* Episodic Memory (Short Term / Volatile) */}
                <div className="rounded-lg border border-cyan-500/20 bg-cyan-950/10 p-3 relative overflow-hidden group">
                    <div className="absolute inset-0 bg-cyan-400/5 opacity-0 group-hover:opacity-100 transition-opacity" />
                    <div className="text-[10px] uppercase tracking-wider text-cyan-200 mb-1">Episodic Trace</div>
                    <div className="text-2xl font-light text-cyan-100 tabular-nums">
                        {Math.round(metrics.usage * 100)}<span className="text-sm opacity-50">%</span>
                    </div>
                    {/* Visual Decay Bar */}
                    <div className="mt-2 h-1.5 w-full bg-cyan-900/40 rounded-full overflow-hidden">
                        <div
                            className="h-full bg-cyan-400 transition-all duration-700 ease-out"
                            style={{ width: `${metrics.usage * 100}%` }}
                        />
                    </div>
                </div>

                {/* Preference Memory (Long Term / Crystallized) */}
                <div className="rounded-lg border border-purple-500/20 bg-purple-950/10 p-3 relative overflow-hidden group">
                    <div className="absolute inset-0 bg-purple-400/5 opacity-0 group-hover:opacity-100 transition-opacity" />
                    <div className="text-[10px] uppercase tracking-wider text-purple-200 mb-1">Reinforcement</div>
                    <div className="text-2xl font-light text-purple-100 tabular-nums">
                        {Math.round(metrics.reinforcement * 100)}<span className="text-sm opacity-50">%</span>
                    </div>
                    {/* Reinforcement Sparkline */}
                    <div className="mt-2 h-1.5 w-full bg-purple-900/40 rounded-full overflow-hidden flex items-center">
                        <div
                            className="h-full bg-purple-400 transition-all duration-1000 ease-in-out"
                            style={{
                                width: `${metrics.reinforcement * 100}%`,
                                opacity: Math.max(0.3, metrics.reinforcement)
                            }}
                        />
                    </div>
                </div>
            </div>

            {/* Decay / Stability Metric */}
            <div className="rounded-lg bg-neuro-surface/50 p-2 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <Zap className="w-3 h-3 text-amber-400" />
                    <span className="text-[10px] uppercase text-neuro-text-muted">Decay Rate</span>
                </div>
                <div className="text-xs text-neuro-text-primary font-mono">
                    {(metrics.decay * 0.1).toFixed(4)} / sec
                </div>
            </div>

            <div className="text-[10px] text-neuro-text-muted leading-relaxed">
                <span className="text-cyan-400">Episodic traces</span> decay naturally. High reinforcement crystallizes patterns into <span className="text-purple-400">long-term preference</span>.
            </div>
        </div>
    );
}
