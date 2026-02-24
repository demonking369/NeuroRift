'use client';

import { useNeuroRift } from '@/lib/hooks';
import { cn } from '@/lib/utils';

const agentOrder = ['Planner', 'Operator', 'Navigator', 'Analyst', 'Scribe'];

export function AgentGraphPanel() {
    const { agents } = useNeuroRift();

    return (
        <div className="grid grid-cols-2 gap-4">
            {agentOrder.map(agent => {
                const status = agents[agent];
                return (
                    <div
                        key={agent}
                        className={cn(
                            'rounded-xl border px-4 py-3 bg-neuro-bg/70 text-sm',
                            status?.state === 'executing' && 'border-emerald-400/40',
                            status?.state === 'planning' && 'border-cyan-400/40',
                            status?.state === 'error' && 'border-rose-400/50'
                        )}
                    >
                        <div className="flex items-center justify-between">
                            <span className="text-xs uppercase tracking-[0.3em] text-neuro-text-muted">{agent}</span>
                            <span className={cn(
                                'text-[10px] uppercase tracking-[0.2em]',
                                status?.state === 'executing' && 'text-emerald-200',
                                status?.state === 'planning' && 'text-cyan-200',
                                status?.state === 'error' && 'text-rose-200',
                                status?.state === 'idle' && 'text-neuro-text-muted'
                            )}>
                                {status?.state || 'idle'}
                            </span>
                        </div>
                        <p className="mt-2 text-neuro-text-primary text-sm">
                            {status?.current_task || 'Awaiting orchestration signals.'}
                        </p>
                        <div className="mt-3 flex items-center justify-between text-[10px] uppercase tracking-[0.2em] text-neuro-text-muted">
                            <span>Queue {status?.queue_depth ?? 0}</span>
                            <span>{new Date(status?.last_update ?? Date.now()).toLocaleTimeString()}</span>
                        </div>
                    </div>
                );
            })}
        </div>
    );
}
