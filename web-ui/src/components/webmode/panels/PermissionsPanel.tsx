'use client';

import { useNeuroRift } from '@/lib/hooks';
import { cn } from '@/lib/utils';

export function PermissionsPanel() {
    const { approvals } = useNeuroRift();

    return (
        <div className="space-y-3">
            {approvals.map(approval => (
                <div key={approval.id} className="rounded-xl border border-neuro-border/60 bg-neuro-bg/70 p-4">
                    <div className="flex items-center justify-between text-xs uppercase tracking-[0.3em] text-neuro-text-muted">
                        <span>{approval.status}</span>
                        <span className={cn(
                            approval.risk === 'high' && 'text-rose-200',
                            approval.risk === 'medium' && 'text-amber-200',
                            approval.risk === 'low' && 'text-emerald-200'
                        )}>
                            {approval.risk} risk
                        </span>
                    </div>
                    <p className="mt-2 text-sm text-neuro-text-primary">{approval.label}</p>
                    <div className="mt-3 flex items-center gap-2 text-[10px] uppercase tracking-[0.3em] text-neuro-text-muted">
                        <span className="px-2 py-1 rounded-full bg-neuro-surface/70 border border-neuro-border/60">Approve</span>
                        <span className="px-2 py-1 rounded-full bg-neuro-surface/70 border border-neuro-border/60">Reject</span>
                    </div>
                </div>
            ))}
        </div>
    );
}
