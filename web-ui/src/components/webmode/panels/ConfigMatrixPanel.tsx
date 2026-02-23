'use client';

import { useMemo, useState } from 'react';
import { configSchema } from '@/lib/webmode/config-schema';
import { useWebModeContext } from '@/components/webmode/WebModeProvider';
import { cn } from '@/lib/utils';
import { FileJson, Sliders, Lock, Cpu, icons } from 'lucide-react';

function getValue(source: any, path: string) {
    return path.split('.').reduce((acc, key) => (acc ? acc[key] : undefined), source);
}

export function ConfigMatrixPanel() {
    const { config, updateConfig } = useWebModeContext();
    const sections = useMemo(() => configSchema, []);
    const [activeSectionId, setActiveSectionId] = useState(sections[0].id);
    const [showCompiler, setShowCompiler] = useState(false);

    // Simulate "Policy Compilation" - a live JSON view of the effective policy
    const effectivePolicy = useMemo(() => {
        return {
            policy_version: "v2.1.0-alpha",
            enforcement_level: config.stealth.level > 0.7 ? "STRICT" : "PERMISSIVE",
            constraints: {
                max_memory_usage: config.memory.usage,
                network_egress: config.onlineMode.enabled ? "TUNNELED" : "LOCAL_ONLY",
                scan_depth: config.stealth.scanDepth,
            },
            signature: "generated-neuro-rift-policy-8f7a"
        };
    }, [config]);

    const activeSection = sections.find(s => s.id === activeSectionId) || sections[0];

    return (
        <div className="flex flex-col h-[400px] gap-4">
            {/* Header / Mode Switch */}
            <div className="flex items-center justify-between shrink-0">
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-neuro-bg/40 border border-neuro-border/60">
                    <Sliders className="w-4 h-4 text-cyan-300" />
                    <span className="text-xs uppercase tracking-[0.3em] text-neuro-text-muted">Configuration Matrix</span>
                </div>
                <button
                    onClick={() => setShowCompiler(!showCompiler)}
                    className={cn(
                        "flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs uppercase tracking-wider transition-all",
                        showCompiler
                            ? "bg-emerald-500/10 text-emerald-300 border border-emerald-500/30"
                            : "bg-neuro-surface text-neuro-text-muted hover:text-neuro-text-primary border border-transparent"
                    )}
                >
                    <FileJson className="w-3 h-3" />
                    {showCompiler ? 'View Matrix' : 'View Policy'}
                </button>
            </div>

            {showCompiler ? (
                <div className="flex-1 rounded-xl border border-neuro-border/60 bg-[#0d1117] p-4 font-mono text-xs overflow-hidden animate-in fade-in slide-in-from-right-2 duration-300 relative">
                    <div className="flex items-center justify-between mb-3 text-neuro-text-muted uppercase tracking-widest text-[10px]">
                        <span>Effective Policy Preview</span>
                        <Lock className="w-3 h-3 text-emerald-400" />
                    </div>
                    <pre className="text-cyan-100/80 leading-relaxed overflow-y-auto h-[calc(100%-24px)] custom-scrollbar">
                        {JSON.stringify(effectivePolicy, null, 2)}
                    </pre>
                </div>
            ) : (
                <div className="flex flex-1 gap-4 overflow-hidden animate-in fade-in slide-in-from-left-2 duration-300">
                    {/* Sidebar Tabs */}
                    <div className="w-1/3 flex flex-col gap-1 overflow-y-auto pr-1">
                        {sections.map(section => (
                            <button
                                key={section.id}
                                onClick={() => setActiveSectionId(section.id)}
                                className={cn(
                                    "text-left px-3 py-3 rounded-lg text-xs transition-all duration-200 border",
                                    activeSectionId === section.id
                                        ? "bg-neuro-surface border-cyan-500/30 text-cyan-100 shadow-[0_0_10px_-4px_rgba(34,211,238,0.3)]"
                                        : "bg-transparent border-transparent text-neuro-text-muted hover:text-neuro-text-secondary hover:bg-white/5"
                                )}
                            >
                                <div className="font-medium uppercase tracking-wider mb-0.5">{section.title}</div>
                                <div className="text-[9px] opacity-60 line-clamp-1">{section.description}</div>
                            </button>
                        ))}
                    </div>

                    {/* Active Section Content */}
                    <div className="flex-1 rounded-xl border border-neuro-border/60 bg-neuro-bg/60 p-5 overflow-y-auto custom-scrollbar relative">
                        <div className="absolute top-0 right-0 w-20 h-20 bg-gradient-to-bl from-cyan-500/5 to-transparent rounded-tr-xl pointer-events-none" />

                        <div className="mb-6">
                            <h3 className="text-sm font-light text-cyan-100 uppercase tracking-widest mb-1">{activeSection.title}</h3>
                            <p className="text-xs text-neuro-text-muted">{activeSection.description}</p>
                        </div>

                        <div className="space-y-6">
                            {activeSection.fields.map(field => {
                                const value = getValue(config, field.path as string);
                                return (
                                    <div key={field.path} className="group">
                                        <div className="flex items-center justify-between text-xs text-neuro-text-secondary mb-2">
                                            <span className="uppercase tracking-[0.2em]">{field.label}</span>
                                            <span className="font-mono text-[10px] opacity-70 bg-black/20 px-1.5 py-0.5 rounded border border-white/5">
                                                {typeof value === 'number' ? value.toFixed(2) : String(value)}
                                            </span>
                                        </div>

                                        {field.type === 'toggle' && (
                                            <button
                                                type="button"
                                                onClick={() => updateConfig(field.path as string, !value)}
                                                className={cn(
                                                    "w-full flex items-center justify-between px-3 py-2 rounded-lg border transition-all duration-300 text-xs",
                                                    value
                                                        ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-200"
                                                        : "bg-neuro-surface/40 border-neuro-border/60 text-neuro-text-muted"
                                                )}
                                            >
                                                <span>{value ? 'Active' : 'Inactive'}</span>
                                                <div className={cn(
                                                    "w-2 h-2 rounded-full shadow-[0_0_8px_currentColor]",
                                                    value ? "bg-emerald-400" : "bg-neuro-text-muted opacity-50"
                                                )} />
                                            </button>
                                        )}

                                        {field.type === 'slider' && (
                                            <div className="relative h-6 flex items-center">
                                                <div className="absolute w-full h-1 bg-neuro-border/40 rounded-full overflow-hidden">
                                                    <div
                                                        className="h-full bg-cyan-500/50 transition-all duration-100"
                                                        style={{ width: `${((Number(value) - (field.min || 0)) / ((field.max || 1) - (field.min || 0))) * 100}%` }}
                                                    />
                                                </div>
                                                <input
                                                    type="range"
                                                    min={field.min}
                                                    max={field.max}
                                                    step={field.step}
                                                    value={value}
                                                    onChange={event => updateConfig(field.path as string, Number(event.target.value))}
                                                    className="absolute w-full opacity-0 cursor-ew-resize z-10"
                                                />
                                                <div
                                                    className="absolute w-3 h-3 bg-cyan-400 rounded-full shadow-[0_0_10px_rgba(34,211,238,0.5)] pointer-events-none transition-all duration-100 border border-white/20"
                                                    style={{ left: `calc(${((Number(value) - (field.min || 0)) / ((field.max || 1) - (field.min || 0))) * 100}% - 6px)` }}
                                                />
                                            </div>
                                        )}

                                        {field.type === 'select' && (
                                            <select
                                                value={value}
                                                onChange={event => updateConfig(field.path as string, event.target.value)}
                                                className="w-full rounded-lg border border-neuro-border/60 bg-neuro-surface/70 px-3 py-2 text-xs text-neuro-text-primary focus:border-cyan-400/50 focus:outline-none transition-colors appearance-none"
                                            >
                                                {field.options?.map(option => (
                                                    <option key={option.value} value={option.value}>
                                                        {option.label}
                                                    </option>
                                                ))}
                                            </select>
                                        )}

                                        <div className="mt-1 text-[10px] text-neuro-text-muted opacity-0 group-hover:opacity-60 transition-opacity">
                                            {field.description}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
