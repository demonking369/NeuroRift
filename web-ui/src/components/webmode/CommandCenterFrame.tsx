'use client';

import { Activity, ShieldCheck, Wifi, Signal } from 'lucide-react';
import { useNeuroRift } from '@/lib/hooks';
import { cn } from '@/lib/utils';

export function CommandCenterFrame({ children }: { children: React.ReactNode }) {
    const { session, systemHealth, torConnected, metrics } = useNeuroRift();

    return (
        <div className="min-h-screen bg-neuro-void text-neuro-text-primary">
            <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(circle_at_top,_rgba(34,211,238,0.12),_transparent_50%),radial-gradient(circle_at_bottom,_rgba(99,102,241,0.12),_transparent_55%)]" />
            <div className="pointer-events-none fixed inset-0 bg-[linear-gradient(to_right,_rgba(15,23,42,0.35)_1px,_transparent_1px),linear-gradient(to_bottom,_rgba(15,23,42,0.35)_1px,_transparent_1px)] bg-[size:32px_32px] opacity-30" />
            <div className="relative flex min-h-screen flex-col">
                <header className="flex items-center justify-between px-6 py-4 border-b border-neuro-border/60 backdrop-blur">
                    <div className="flex items-center gap-3">
                        <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-cyan-500 via-blue-600 to-purple-600 flex items-center justify-center shadow-lg shadow-cyan-500/30">
                            <Signal className="h-5 w-5 text-white" />
                        </div>
                        <div>
                            <p className="text-xs uppercase tracking-[0.4em] text-neuro-text-muted">NeuroRift Web Mode</p>
                            <h1 className="text-lg font-semibold">Command Interface</h1>
                        </div>
                    </div>
                    <div className="hidden lg:flex items-center gap-4 text-xs text-neuro-text-muted">
                        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-neuro-surface/60 border border-neuro-border/60">
                            <ShieldCheck className="w-3.5 h-3.5 text-emerald-300" />
                            <span>{session ? session.name : 'No active session'}</span>
                        </div>
                        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-neuro-surface/60 border border-neuro-border/60">
                            <Wifi className={cn('w-3.5 h-3.5', torConnected ? 'text-emerald-300' : 'text-rose-400')} />
                            <span>{torConnected ? 'Secure Relay' : 'Relay Offline'}</span>
                        </div>
                        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-neuro-surface/60 border border-neuro-border/60">
                            <Activity className="w-3.5 h-3.5 text-cyan-300" />
                            <span>CPU {systemHealth.cpu.toFixed(0)}%</span>
                            <span>MEM {systemHealth.memory.toFixed(0)}%</span>
                            <span>LAT {systemHealth.latency.toFixed(0)}ms</span>
                        </div>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-neuro-text-muted">
                        <span className="px-2 py-1 rounded-full bg-neuro-surface/60 border border-neuro-border/60">Tasks {metrics.activeTasks}</span>
                        <span className="px-2 py-1 rounded-full bg-neuro-surface/60 border border-neuro-border/60">Approvals {metrics.pendingApprovals}</span>
                    </div>
                </header>
                <div className="flex-1 overflow-hidden">{children}</div>
                <footer className="px-6 py-3 border-t border-neuro-border/60 text-xs text-neuro-text-muted flex items-center justify-between backdrop-blur">
                    <span>Policy-driven routing • Deterministic execution enforced</span>
                    <span>Web Mode vNext</span>
                </footer>
            </div>
        </div>
    );
}
