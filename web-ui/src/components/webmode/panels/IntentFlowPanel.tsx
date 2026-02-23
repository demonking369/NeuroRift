'use client';

import { ArrowRight, Shield, Wand2, Layers } from 'lucide-react';

const steps = [
    { label: 'Intent Capture', icon: Wand2, detail: 'NL + Command synthesis' },
    { label: 'Plan Negotiation', icon: Layers, detail: 'Agents critique + score' },
    { label: 'Policy Gate', icon: Shield, detail: 'OpenClaw + NeuroRift' },
    { label: 'Execution', icon: ArrowRight, detail: 'Deterministic tooling' },
];

export function IntentFlowPanel() {
    return (
        <div className="space-y-4">
            <div className="flex flex-wrap items-center gap-3">
                {steps.map((step, index) => (
                    <div key={step.label} className="flex items-center gap-3">
                        <div className="rounded-xl border border-cyan-400/30 bg-cyan-500/10 px-3 py-2 text-xs text-neuro-text-primary flex items-center gap-2">
                            <step.icon className="w-4 h-4 text-cyan-200" />
                            <div>
                                <div className="uppercase tracking-[0.3em] text-[10px] text-neuro-text-muted">{step.label}</div>
                                <div className="text-xs text-neuro-text-primary">{step.detail}</div>
                            </div>
                        </div>
                        {index < steps.length - 1 && (
                            <ArrowRight className="w-4 h-4 text-neuro-text-muted" />
                        )}
                    </div>
                ))}
            </div>
            <div className="rounded-xl border border-neuro-border/60 bg-neuro-bg/60 p-4 text-sm text-neuro-text-secondary">
                Intent routing is declarative and policy-driven. Execution is triggered only after negotiation, scoring, and enforcement checks succeed.
            </div>
        </div>
    );
}
