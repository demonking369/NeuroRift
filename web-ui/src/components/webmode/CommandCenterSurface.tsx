'use client';

import { panelDefinitions, layoutZones } from '@/lib/webmode/schema';
import { evaluatePanelPolicy } from '@/lib/webmode/policy';
import { PanelRenderer } from '@/components/webmode/PanelRenderer';
import { useNeuroRift } from '@/lib/hooks';
import { useWebModeContext } from '@/components/webmode/WebModeProvider';
import { cn } from '@/lib/utils';

export function CommandCenterSurface() {
    const { session } = useNeuroRift();
    const { deviceTier, controlMode, phase, lastSignal } = useWebModeContext();

    const policyContext = {
        deviceTier,
        controlMode,
        sessionActive: Boolean(session),
    };

    const panels = panelDefinitions.filter(panel => evaluatePanelPolicy(panel, policyContext));

    const panelMap = new Map(panels.map(panel => [panel.id, panel]));

    const primaryPanels = layoutZones.primary.map(id => panelMap.get(id)).filter(Boolean);
    const secondaryPanels = layoutZones.secondary.map(id => panelMap.get(id)).filter(Boolean);
    const tertiaryPanels = layoutZones.tertiary.map(id => panelMap.get(id)).filter(Boolean);
    const dockPanels = layoutZones.dock.map(id => panelMap.get(id)).filter(Boolean);

    return (
        <div className="h-full overflow-y-auto px-6 py-6">
            <div className="mb-6 flex flex-col gap-3">
                <div className="flex flex-wrap items-center gap-3">
                    <span className="text-xs uppercase tracking-[0.4em] text-neuro-text-muted">Phase</span>
                    <span className="px-3 py-1 rounded-full bg-neuro-surface/70 border border-neuro-border/60 text-xs">{phase}</span>
                    <span className="px-3 py-1 rounded-full bg-neuro-surface/70 border border-neuro-border/60 text-xs">{controlMode.toUpperCase()} MODE</span>
                    <span className={cn(
                        'px-3 py-1 rounded-full border text-xs',
                        deviceTier === 'mobile' && 'border-cyan-400/60 text-cyan-200',
                        deviceTier === 'tablet' && 'border-indigo-400/60 text-indigo-200',
                        deviceTier === 'desktop' && 'border-emerald-400/60 text-emerald-200',
                        deviceTier === 'wide' && 'border-purple-400/60 text-purple-200'
                    )}>
                        {deviceTier.toUpperCase()} TIER
                    </span>
                </div>
                <div className="text-sm text-neuro-text-secondary">{lastSignal}</div>
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,2fr)_minmax(0,1fr)] gap-6">
                <div className="space-y-6">
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {primaryPanels.map(panel => (
                            panel ? <PanelRenderer key={panel.id} panel={panel} /> : null
                        ))}
                    </div>
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {secondaryPanels.map(panel => (
                            panel ? <PanelRenderer key={panel.id} panel={panel} /> : null
                        ))}
                    </div>
                </div>
                <div className="space-y-6">
                    {tertiaryPanels.map(panel => (
                        panel ? <PanelRenderer key={panel.id} panel={panel} /> : null
                    ))}
                    <div className="grid grid-cols-1 gap-6">
                        {dockPanels.map(panel => (
                            panel ? <PanelRenderer key={panel.id} panel={panel} /> : null
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}
