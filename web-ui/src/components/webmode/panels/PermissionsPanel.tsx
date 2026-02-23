'use client';

import { useNeuroRift } from '@/lib/hooks';
import { cn } from '@/lib/utils';
import { Shield, ShieldAlert, CheckCircle, XCircle, FileDiff } from 'lucide-react';

export function PermissionsPanel() {
    const { approvals } = useNeuroRift();

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-neuro-text-muted">
                    <Shield className="w-4 h-4 text-amber-400" />
                    <span>Decision Gates</span>
                </div>
                <div className="text-[10px] uppercase tracking-wider text-rose-300 bg-rose-950/20 px-2 py-0.5 rounded border border-rose-500/20">
                    Enforcement Active
                </div>
            </div>

            {approvals.map(approval => {
                const isHighRisk = approval.risk === 'high' || approval.risk === 'critical';

                return (
                    <div key={approval.id} className="rounded-xl border border-neuro-border/60 bg-neuro-bg/70 overflow-hidden">
                        {/* Header */}
                        <div className="p-4 border-b border-neuro-border/40">
                            <div className="flex items-center justify-between text-xs uppercase tracking-[0.3em] text-neuro-text-muted mb-2">
                                <span className={cn(
                                    approval.status === 'pending' && "text-amber-400 animate-pulse",
                                    approval.status === 'approved' && "text-emerald-400",
                                    approval.status === 'rejected' && "text-rose-400"
                                )}>{approval.status}</span>
                                <span className={cn(
                                    isHighRisk ? 'text-rose-200 bg-rose-500/10 px-2 py-0.5 rounded' : 'text-emerald-200'
                                )}>
                                    {approval.risk} risk
                                </span>
                            </div>
                            <p className="text-sm text-neuro-text-primary font-medium">{approval.label}</p>
                        </div>

                        {/* Analysis / Delta View */}
                        <div className="bg-neuro-surface/30 p-3 space-y-3">
                            <div className="flex items-start gap-3">
                                <FileDiff className="w-4 h-4 text-neuro-text-muted mt-0.5" />
                                <div className="space-y-1 w-full">
                                    <div className="text-[10px] uppercase tracking-wider text-neuro-text-muted">Projected Policy Delta</div>
                                    <div className="text-xs font-mono bg-black/20 p-2 rounded border border-white/5 space-y-1">
                                        <div className="text-emerald-400/90">+ allow tcp/443 egress</div>
                                        <div className="text-rose-400/90">- deny ptrace (temporary)</div>
                                    </div>
                                </div>
                            </div>

                            {isHighRisk && (
                                <div className="flex items-start gap-3 bg-rose-950/10 p-2 rounded border border-rose-500/10">
                                    <ShieldAlert className="w-4 h-4 text-rose-400 mt-0.5" />
                                    <span className="text-xs text-rose-200/90">
                                        Action exceeds standard Rules of Engagement. Interactive override required.
                                    </span>
                                </div>
                            )}
                        </div>

                        {/* Controls */}
                        {approval.status === 'pending' && (
                            <div className="p-3 bg-neuro-surface/50 flex gap-2">
                                <button className="flex-1 py-2 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-200 text-xs hover:bg-emerald-500/20 transition flex items-center justify-center gap-2">
                                    <CheckCircle className="w-3 h-3" /> Approve
                                </button>
                                <button className="flex-1 py-2 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-200 text-xs hover:bg-rose-500/20 transition flex items-center justify-center gap-2">
                                    <XCircle className="w-3 h-3" /> Reject
                                </button>
                            </div>
                        )}
                    </div>
                );
            })}
        </div>
    );
}
