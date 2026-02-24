'use client';

import { useMemo } from 'react';
import { configSchema } from '@/lib/webmode/config-schema';
import { useWebModeContext } from '@/components/webmode/WebModeProvider';

function getValue(source: any, path: string) {
    return path.split('.').reduce((acc, key) => (acc ? acc[key] : undefined), source);
}

export function ConfigMatrixPanel() {
    const { config, updateConfig } = useWebModeContext();

    const sections = useMemo(() => configSchema, []);

    return (
        <div className="space-y-6">
            {sections.map(section => (
                <div key={section.id} className="rounded-xl border border-neuro-border/60 bg-neuro-bg/60 p-4">
                    <div className="mb-3">
                        <h4 className="text-xs uppercase tracking-[0.4em] text-neuro-text-muted">{section.title}</h4>
                        <p className="text-xs text-neuro-text-secondary mt-1">{section.description}</p>
                    </div>
                    <div className="space-y-4">
                        {section.fields.map(field => {
                            const value = getValue(config, field.path as string);
                            return (
                                <div key={field.path} className="flex flex-col gap-2">
                                    <div className="flex items-center justify-between text-xs text-neuro-text-secondary">
                                        <span className="uppercase tracking-[0.3em]">{field.label}</span>
                                        <span>{typeof value === 'number' ? value.toFixed(2) : String(value)}</span>
                                    </div>
                                    <p className="text-xs text-neuro-text-muted">{field.description}</p>
                                    {field.type === 'toggle' && (
                                        <button
                                            type="button"
                                            onClick={() => updateConfig(field.path as string, !value)}
                                            className="w-full rounded-lg border border-neuro-border/60 bg-neuro-surface/70 px-3 py-2 text-xs text-neuro-text-primary"
                                        >
                                            {value ? 'Enabled' : 'Disabled'}
                                        </button>
                                    )}
                                    {field.type === 'slider' && (
                                        <input
                                            type="range"
                                            min={field.min}
                                            max={field.max}
                                            step={field.step}
                                            value={value}
                                            onChange={event => updateConfig(field.path as string, Number(event.target.value))}
                                            className="w-full accent-cyan-400"
                                        />
                                    )}
                                    {field.type === 'select' && (
                                        <select
                                            value={value}
                                            onChange={event => updateConfig(field.path as string, event.target.value)}
                                            className="w-full rounded-lg border border-neuro-border/60 bg-neuro-surface/70 px-3 py-2 text-xs text-neuro-text-primary"
                                        >
                                            {field.options?.map(option => (
                                                <option key={option.value} value={option.value}>
                                                    {option.label}
                                                </option>
                                            ))}
                                        </select>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                </div>
            ))}
        </div>
    );
}
