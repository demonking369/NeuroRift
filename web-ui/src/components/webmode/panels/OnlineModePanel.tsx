'use client';

import { useMemo } from 'react';
import { Globe, ShieldAlert } from 'lucide-react';
import { useWebModeContext } from '@/components/webmode/WebModeProvider';
import { cn } from '@/lib/utils';

export function OnlineModePanel() {
    const { config, updateConfig } = useWebModeContext();

    const publicUrl = useMemo(() => {
        if (!config.onlineMode.enabled) return null;
        return `https://nr-${Math.floor(Math.random() * 9999)}.tunnel.neurorift.ai`;
    }, [config.onlineMode.enabled]);

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs uppercase tracking-[0.3em] text-neuro-text-muted">
                    <Globe className="w-4 h-4 text-cyan-300" />
                    Share Web Interface
                </div>
                <button
                    onClick={() => updateConfig('onlineMode.enabled', !config.onlineMode.enabled)}
                    className={cn(
                        'px-3 py-1 rounded-full text-xs border',
                        config.onlineMode.enabled
                            ? 'border-emerald-400/50 text-emerald-200'
                            : 'border-neuro-border/60 text-neuro-text-muted'
                    )}
                >
                    {config.onlineMode.enabled ? 'Enabled' : 'Disabled'}
                </button>
            </div>

            <div className="rounded-xl border border-neuro-border/60 bg-neuro-bg/60 p-4 space-y-3">
                <div className="text-xs text-neuro-text-secondary">Online mode creates an encrypted tunnel for remote access. OFF by default.</div>
                <div className="flex items-center justify-between">
                    <span className="text-xs uppercase tracking-[0.3em] text-neuro-text-muted">Access Level</span>
                    <select
                        value={config.onlineMode.access}
                        onChange={event => updateConfig('onlineMode.access', event.target.value)}
                        className="rounded-lg border border-neuro-border/60 bg-neuro-surface/70 px-3 py-2 text-xs text-neuro-text-primary"
                    >
                        <option value="read">Read-only</option>
                        <option value="control">Control</option>
                    </select>
                </div>
                {publicUrl && (
                    <div className="rounded-lg border border-emerald-400/30 bg-emerald-500/10 px-3 py-2 text-xs text-emerald-100">
                        <div className="uppercase tracking-[0.3em] text-[10px] text-emerald-200">Public URL</div>
                        <div>{publicUrl}</div>
                    </div>
                )}
                <div className="flex items-start gap-2 text-xs text-rose-200">
                    <ShieldAlert className="w-4 h-4 mt-0.5" />
                    <span>Remote exposure requires explicit approval and never bypasses NeuroRift enforcement.</span>
                </div>
            </div>
        </div>
    );
}
