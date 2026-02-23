'use client';

import { useState } from 'react';
import { panelDefinitions, layoutZones } from '@/lib/webmode/schema';
import { evaluatePanelPolicy } from '@/lib/webmode/policy';
import { PanelRenderer } from '@/components/webmode/PanelRenderer';
import { useNeuroRift } from '@/lib/hooks';
import { useWebModeContext } from '@/components/webmode/WebModeProvider';
import { cn } from '@/lib/utils';
import { PanelCategory } from '@/lib/webmode/types';
import { Activity, Shield, Terminal, Settings, Cpu, Database, LayoutGrid } from 'lucide-react';

const CATEGORIES: { id: PanelCategory; label: string; icon: any }[] = [
    { id: 'AI_CONTROL', label: 'AI Control Plane', icon: Cpu },
    { id: 'OPERATOR', label: 'Operator Plane', icon: Terminal },
    { id: 'SYSTEM', label: 'System & Config', icon: Settings },
];

export function CommandCenterSurface() {
    const { session } = useNeuroRift();
    const { deviceTier, controlMode, phase, lastSignal, adapterMode } = useWebModeContext();
    const [activeCategory, setActiveCategory] = useState<PanelCategory>('AI_CONTROL');

    const policyContext = {
        deviceTier,
        controlMode,
        sessionActive: Boolean(session),
    };

    // Filter relevant panels for the current category
    const panels = panelDefinitions.filter(
        panel => panel.category === activeCategory && evaluatePanelPolicy(panel, policyContext)
    );
    const panelMap = new Map(panels.map(panel => [panel.id, panel]));

    // Distribute into zones based on filtered set
    const primaryPanels = layoutZones.primary.map(id => panelMap.get(id)).filter(Boolean);
    const secondaryPanels = layoutZones.secondary.map(id => panelMap.get(id)).filter(Boolean);
    const tertiaryPanels = layoutZones.tertiary.map(id => panelMap.get(id)).filter(Boolean);
    const dockPanels = layoutZones.dock.map(id => panelMap.get(id)).filter(Boolean);

    return (
        <div className="h-full flex flex-col overflow-hidden bg-neuro-bg">
            {/* Header / Nav */}
            <div className="px-6 py-4 border-b border-neuro-border/40 bg-neuro-bg/50 backdrop-blur-sm shrink-0 flex items-center justify-between">
                <div className="flex items-center gap-6">
                    <div className="flex items-center gap-3">
                        <Activity className="w-5 h-5 text-cyan-400" />
                        <h1 className="text-sm font-bold uppercase tracking-[0.2em] text-cyan-50">NeuroRift <span className="text-neuro-text-muted font-normal">v2.1</span></h1>
                    </div>

                    <div className="h-6 w-px bg-neuro-border/50" />

                    <div className="flex gap-2">
                        {CATEGORIES.map(cat => (
                            <button
                                key={cat.id}
                                onClick={() => setActiveCategory(cat.id)}
                                className={cn(
                                    "px-4 py-2 rounded-lg text-xs font-medium transition-all flex items-center gap-2",
                                    activeCategory === cat.id
                                        ? "bg-cyan-500/10 text-cyan-300 border border-cyan-500/30 shadow-[0_0_15px_rgba(6,182,212,0.15)]"
                                        : "text-neuro-text-muted hover:text-neuro-text-primary hover:bg-white/5"
                                )}
                            >
                                <cat.icon className="w-3.5 h-3.5" />
                                <span className="uppercase tracking-wider">{cat.label}</span>
                            </button>
                        ))}
                    </div>
                </div>

                <div className="flex items-center gap-3 text-[10px] uppercase font-mono">
                    <span className={cn(
                        "px-2 py-1 rounded bg-black/30 border border-white/5",
                        adapterMode === 'REAL' ? "text-emerald-400 border-emerald-500/20" : "text-amber-400 border-amber-500/20"
                    )}>
                        {adapterMode} MODE
                    </span>
                    <span className="text-neuro-text-muted">{lastSignal || 'System Ready'}</span>
                </div>
            </div>

            {/* Scrollable Content */}
            <div className="flex-1 overflow-y-auto p-6">
                <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,2fr)_minmax(0,1fr)] gap-6 max-w-[1920px] mx-auto">

                    {/* Main Column */}
                    <div className="space-y-6">
                        {/* Primary Panels (Full Width in Col 1) */}
                        {primaryPanels.length > 0 && (
                            <div className="space-y-6">
                                {primaryPanels.map(panel => (
                                    panel ? <PanelRenderer key={panel.id} panel={panel} /> : null
                                ))}
                            </div>
                        )}

                        {/* Secondary Panels (Grid in Col 1 if generic) */}
                        {secondaryPanels.length > 0 && (
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                {secondaryPanels.map(panel => (
                                    panel ? <PanelRenderer key={panel.id} panel={panel} /> : null
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Side Column / Tertiary & Dock (if vertical) */}
                    <div className="space-y-6 flex flex-col">
                        {tertiaryPanels.map(panel => (
                            panel ? <PanelRenderer key={panel.id} panel={panel} /> : null
                        ))}

                        {/* Dock Panels here for vertical layout? Or specific component? */}
                        {dockPanels.map(panel => (
                            panel ? <PanelRenderer key={panel.id} panel={panel} /> : null
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}
