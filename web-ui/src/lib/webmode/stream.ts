'use client';

import { useEffect, useState } from 'react';

const signals = [
    'Planner: Negotiating scan lattice with Critic agent.',
    'Observer: Monitoring policy drift threshold.',
    'Operator: Awaiting execution consent token.',
    'Analyst: Correlating memory decay against risk profile.',
    'Meta: Scoring plan proposals + gating evolution.',
    'Navigator: Replaying session context for intent refinement.',
];

export interface StreamEvent {
    id: string;
    label: string;
    time: string;
    tone: 'signal' | 'neutral' | 'warning';
}

export function useSignalStream() {
    const [events, setEvents] = useState<StreamEvent[]>(() => [
        {
            id: 'seed-0',
            label: 'OpenClaw bus synchronized. Awaiting intents.',
            time: new Date().toLocaleTimeString(),
            tone: 'signal',
        },
        {
            id: 'seed-1',
            label: 'NeuroRift execution plane in deterministic mode.',
            time: new Date().toLocaleTimeString(),
            tone: 'neutral',
        }
    ]);

    useEffect(() => {
        const interval = window.setInterval(() => {
            const next = signals[Math.floor(Math.random() * signals.length)];
            setEvents(prev => [
                {
                    id: `evt-${Date.now()}`,
                    label: next,
                    time: new Date().toLocaleTimeString(),
                    tone: Math.random() > 0.8 ? 'warning' : 'signal',
                },
                ...prev
            ].slice(0, 12));
        }, 3200);

        return () => window.clearInterval(interval);
    }, []);

    return events;
}
