'use client';

import { useWebModeContext } from '@/components/webmode/WebModeProvider';

export function MemoryPulsePanel() {
    const { config } = useWebModeContext();

    const meters = [
        { label: 'Short-term', value: config.memory.usage },
        { label: 'Episodic', value: config.memory.reinforcement },
        { label: 'Preference', value: config.memory.decay },
        { label: 'Risk Profile', value: config.stealth.level },
    ];

    return (
        <div className="space-y-3">
            {meters.map(meter => (
                <div key={meter.label}>
                    <div className="flex items-center justify-between text-xs text-neuro-text-muted">
                        <span className="uppercase tracking-[0.3em]">{meter.label}</span>
                        <span>{Math.round(meter.value * 100)}%</span>
                    </div>
                    <div className="mt-2 h-2 rounded-full bg-neuro-border/60 overflow-hidden">
                        <div
                            className="h-full bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-500"
                            style={{ width: `${meter.value * 100}%` }}
                        />
                    </div>
                </div>
            ))}
            <p className="text-xs text-neuro-text-muted mt-2">Memory is local-only and influences planning without transmission.</p>
        </div>
    );
}
