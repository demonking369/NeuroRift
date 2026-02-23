'use client';

import { useSignalStream } from '@/lib/webmode/stream';
import { cn } from '@/lib/utils';

export function ActivityStreamPanel() {
    const events = useSignalStream();

    return (
        <div className="space-y-3 max-h-[320px] overflow-y-auto pr-2">
            {events.map((event: any) => (
                <div
                    key={event.id}
                    className={cn(
                        'rounded-lg border px-3 py-2 text-xs',
                        event.tone === 'warning'
                            ? 'border-rose-400/40 bg-rose-500/10 text-rose-100'
                            : 'border-neuro-border/60 bg-neuro-bg/60 text-neuro-text-secondary'
                    )}
                >
                    <div className="flex items-center justify-between text-[10px] uppercase tracking-[0.3em] text-neuro-text-muted">
                        <span>{event.time}</span>
                        <span>{event.tone}</span>
                    </div>
                    <p className="mt-2 text-sm text-neuro-text-primary">{event.label}</p>
                </div>
            ))}
        </div>
    );
}
