'use client';

import { cn } from '@/lib/utils';
import type { PanelDefinition } from '@/lib/webmode/types';
import { PanelRegistry } from '@/components/webmode/PanelRegistry';

interface PanelRendererProps {
    panel: PanelDefinition;
}

export function PanelRenderer({ panel }: PanelRendererProps) {
    const Component = PanelRegistry[panel.id];

    return (
        <section
            className={cn(
                'relative rounded-2xl border border-neuro-border/60 bg-neuro-surface/70 backdrop-blur-xl shadow-[0_0_30px_rgba(34,211,238,0.08)] overflow-hidden',
                panel.tone === 'signal' && 'ring-1 ring-cyan-400/30',
                panel.tone === 'warning' && 'ring-1 ring-rose-400/30'
            )}
        >
            <div className="px-5 py-4 border-b border-neuro-border/50 flex items-center justify-between">
                <div>
                    <h3 className="text-sm font-semibold text-neuro-text-primary tracking-[0.15em] uppercase">{panel.title}</h3>
                    <p className="text-xs text-neuro-text-muted mt-1">{panel.description}</p>
                </div>
                <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.2em] text-neuro-text-muted">
                    <span className="px-2 py-1 rounded-full bg-neuro-bg/70">{panel.slot}</span>
                </div>
            </div>
            <div className="p-5">
                {Component ? <Component /> : <p className="text-neuro-text-muted">Panel unavailable.</p>}
            </div>
            <div className="absolute inset-x-0 bottom-0 h-1 bg-gradient-to-r from-transparent via-cyan-400/40 to-transparent" />
        </section>
    );
}
