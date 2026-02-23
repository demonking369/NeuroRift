'use client';

import { useNeuroRift } from '@/lib/hooks';
import { cn } from '@/lib/utils';
import { useRef, useEffect, useState } from 'react';

// Topology definitions for visual layout
const AGENT_POSITIONS: Record<string, { x: number, y: number }> = {
    Planner: { x: 50, y: 15 },
    Operator: { x: 20, y: 55 },
    Analyst: { x: 80, y: 55 },
    Navigator: { x: 50, y: 90 },
    Scribe: { x: 90, y: 15 }, // Peripheral
};

export function AgentGraphPanel() {
    const { agents } = useNeuroRift();
    const containerRef = useRef<HTMLDivElement>(null);
    const [dimensions, setDimensions] = useState({ w: 0, h: 0 });

    useEffect(() => {
        if (!containerRef.current) return;
        const obs = new ResizeObserver(entries => {
            const { width, height } = entries[0].contentRect;
            setDimensions({ w: width, h: height });
        });
        obs.observe(containerRef.current);
        return () => obs.disconnect();
    }, []);

    // Helper to get absolute coordinates based on percentage positions
    const getCoords = (agent: string) => {
        const pos = AGENT_POSITIONS[agent] || { x: 50, y: 50 };
        return {
            x: (pos.x / 100) * dimensions.w,
            y: (pos.y / 100) * dimensions.h
        };
    };

    return (
        <div ref={containerRef} className="relative h-[240px] w-full bg-neuro-bg/30 rounded-xl border border-neuro-border/40 overflow-hidden">

            {/* 1. Dependency Links (SVG Layer) */}
            <svg className="absolute inset-0 pointer-events-none w-full h-full">
                <defs>
                    <linearGradient id="signal-pulse" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" stopColor="transparent" />
                        <stop offset="50%" stopColor="#22d3ee" stopOpacity="0.8" />
                        <stop offset="100%" stopColor="transparent" />
                    </linearGradient>
                </defs>
                {Object.entries(agents).map(([name, status]) => {
                    if (!status.dependencies?.length) return null;
                    const start = getCoords(name);

                    return status.dependencies.map(dep => {
                        const end = getCoords(dep);
                        return (
                            <g key={`${name}-${dep}`}>
                                {/* Static Line */}
                                <line
                                    x1={start.x} y1={start.y}
                                    x2={end.x} y2={end.y}
                                    stroke="#334155"
                                    strokeWidth="1"
                                    strokeDasharray="4 4"
                                />
                                {/* Active Signal Pulse - Only if signal is strong */}
                                {(status.signal_strength || 0) > 0.5 && (
                                    <circle r="2" fill="#22d3ee">
                                        <animateMotion
                                            dur={`${2 - (status.signal_strength || 0)}s`}
                                            repeatCount="indefinite"
                                            path={`M${start.x},${start.y} L${end.x},${end.y}`}
                                        />
                                    </circle>
                                )}
                            </g>
                        );
                    });
                })}
            </svg>

            {/* 2. Agent Nodes (DOM Layer) */}
            {Object.entries(agents).map(([name, status]) => {
                const pos = AGENT_POSITIONS[name] || { x: 50, y: 50 };
                const isActive = status.state === 'executing' || status.state === 'planning';
                const isError = status.state === 'error';

                return (
                    <div
                        key={name}
                        className={cn(
                            "absolute transform -translate-x-1/2 -translate-y-1/2 transition-all duration-500",
                            "flex flex-col items-center justify-center p-2 rounded-lg border backdrop-blur-sm cursor-help z-10",
                            isActive ? "bg-neuro-surface/90 border-cyan-400/50 shadow-[0_0_15px_-3px_rgba(34,211,238,0.2)]" : "bg-neuro-bg/80 border-neuro-border/60",
                            isError && "border-rose-500/80 shadow-[0_0_10px_rgba(244,63,94,0.3)]"
                        )}
                        style={{ left: `${pos.x}%`, top: `${pos.y}%` }}
                    >
                        <div className="text-[10px] uppercase tracking-widest text-neuro-text-muted mb-1">{name}</div>

                        {/* Status Indicator */}
                        <div className="flex items-center gap-2">
                            <div className={cn(
                                "w-1.5 h-1.5 rounded-full",
                                status.state === 'executing' && "bg-emerald-400 animate-pulse",
                                status.state === 'planning' && "bg-cyan-400 animate-pulse",
                                status.state === 'error' && "bg-rose-500",
                                status.state === 'idle' && "bg-slate-600"
                            )} />
                            <span className={cn(
                                "text-xs font-medium",
                                isActive ? "text-neuro-text-primary" : "text-neuro-text-muted",
                                isError && "text-rose-300"
                            )}>
                                {status.state}
                            </span>
                        </div>

                        {/* Hover Info (Introspection) */}
                        <div className="absolute top-full mt-2 w-48 opacity-0 hover:opacity-100 transition-opacity pointer-events-none bg-black/90 border border-neuro-border text-[10px] p-2 rounded shadow-xl z-20 text-neuro-text-secondary">
                            <div>Task: {status.current_task || 'Idle'}</div>
                            <div>Queue: {status.queue_depth}</div>
                            <div>Signal: {(status.signal_strength || 0).toFixed(2)}</div>
                        </div>
                    </div>
                );
            })}
        </div>
    );
}
