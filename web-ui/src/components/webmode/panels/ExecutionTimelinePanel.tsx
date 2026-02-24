'use client';

import { useNeuroRift } from '@/lib/hooks';
import { cn } from '@/lib/utils';

export function ExecutionTimelinePanel() {
    const { tasks } = useNeuroRift();

    return (
        <div className="space-y-3">
            {tasks.map(task => (
                <div key={task.id} className="rounded-xl border border-neuro-border/60 bg-neuro-bg/70 p-4">
                    <div className="flex items-center justify-between text-xs text-neuro-text-muted">
                        <span className="uppercase tracking-[0.3em]">{task.status}</span>
                        <span>{task.progress.toFixed(0)}%</span>
                    </div>
                    <p className="mt-2 text-sm text-neuro-text-primary">{task.label}</p>
                    <div className="mt-3 h-2 rounded-full bg-neuro-border/60 overflow-hidden">
                        <div
                            className={cn(
                                'h-full rounded-full transition-all',
                                task.status === 'running' && 'bg-gradient-to-r from-cyan-400 to-blue-500',
                                task.status === 'queued' && 'bg-gradient-to-r from-slate-500 to-slate-400',
                                task.status === 'blocked' && 'bg-gradient-to-r from-rose-400 to-rose-500',
                                task.status === 'complete' && 'bg-gradient-to-r from-emerald-400 to-emerald-500'
                            )}
                            style={{ width: `${task.progress}%` }}
                        />
                    </div>
                </div>
            ))}
        </div>
    );
}
