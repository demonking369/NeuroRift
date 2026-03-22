'use client';

import React, { useState, useEffect } from 'react';
import { useWS } from '@/contexts/WebSocketContext';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8888';

interface ModelInfo {
    loaded_model: string | null;
    active_role: string | null;
    vram_used_mb: number;
    vram_total_mb: number;
    models: Record<string, any>;
}

const ROLES = [
    { role: 'vuln_planning',       model: 'hermes-2-pro',      icon: '🎯' },
    { role: 'tool_calling',        model: 'hermes-2-pro',      icon: '🔧' },
    { role: 'exploit_generation',  model: 'deepseek-coder',    icon: '⚡' },
    { role: 'recon_analysis',      model: 'mistral-instruct',  icon: '🔍' },
    { role: 'context_compression', model: 'phi-3-mini',        icon: '📦' },
    { role: 'report_writing',      model: 'hermes-2-pro',      icon: '📝' },
];

export function NeuroCoreMonitor() {
    const { subscribe } = useWS();
    const [status, setStatus] = useState<ModelInfo>({
        loaded_model: null,
        active_role: null,
        vram_used_mb: 0,
        vram_total_mb: 4096,
        models: {},
    });
    const [loading, setLoading] = useState<string | null>(null);

    useEffect(() => {
        const unsub1 = subscribe('neurocore_status', (msg) => {
            setStatus(msg.data);
            setLoading(null);
        });
        const unsub2 = subscribe('initial_state', (msg) => {
            setStatus(msg.data.neurocore);
        });
        return () => { unsub1(); unsub2(); };
    }, [subscribe]);

    const loadModel = async (role: string) => {
        setLoading(role);
        try {
            await fetch(`${API}/api/neurocore/load`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ role }),
            });
        } catch (e) {
            console.error('Failed to load model:', e);
            setLoading(null);
        }
    };

    const unloadModel = async () => {
        try {
            await fetch(`${API}/api/neurocore/unload`, { method: 'POST' });
        } catch (e) {
            console.error('Failed to unload model:', e);
        }
    };

    const vramPct = status.vram_total_mb > 0
        ? (status.vram_used_mb / status.vram_total_mb) * 100
        : 0;

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {/* Status Overview */}
            <div className="card">
                <div className="card-header">
                    <span className="card-title">Engine Status</span>
                    {status.loaded_model ? (
                        <span className="pulse" />
                    ) : (
                        <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>IDLE</span>
                    )}
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16 }}>
                    <div>
                        <div className="text-muted" style={{ fontSize: 11, marginBottom: 4 }}>Loaded Model</div>
                        <div className="font-mono" style={{
                            fontSize: 16,
                            fontWeight: 600,
                            color: status.loaded_model ? 'var(--accent-green)' : 'var(--text-muted)',
                        }}>
                            {status.loaded_model || '—'}
                        </div>
                    </div>
                    <div>
                        <div className="text-muted" style={{ fontSize: 11, marginBottom: 4 }}>Active Role</div>
                        <div className="font-mono" style={{ fontSize: 16, fontWeight: 600, color: 'var(--accent-cyan)' }}>
                            {status.active_role || '—'}
                        </div>
                    </div>
                    <div>
                        <div className="text-muted" style={{ fontSize: 11, marginBottom: 4 }}>VRAM</div>
                        <div className="font-mono" style={{ fontSize: 14 }}>
                            {status.vram_used_mb} / {status.vram_total_mb} MB
                        </div>
                    </div>
                </div>

                {/* VRAM Bar */}
                <div style={{ marginTop: 16 }}>
                    <div className="vram-bar">
                        <div className="vram-bar-fill" style={{ width: `${vramPct}%` }} />
                    </div>
                </div>

                {/* Unload button */}
                {status.loaded_model && (
                    <button
                        className="btn btn-ghost btn-sm"
                        style={{ marginTop: 12 }}
                        onClick={unloadModel}
                    >
                        Unload Model
                    </button>
                )}
            </div>

            {/* Model Roles Grid */}
            <div className="card">
                <div className="card-header">
                    <span className="card-title">Model Roles</span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {ROLES.map(({ role, model, icon }) => {
                        const isActive = status.active_role === role;
                        const isLoading = loading === role;
                        return (
                            <div
                                key={role}
                                style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: 12,
                                    padding: '10px 12px',
                                    borderRadius: 8,
                                    border: `1px solid ${isActive ? 'var(--accent-green)' : 'var(--border-primary)'}`,
                                    background: isActive ? 'var(--accent-green-dim)' : 'var(--bg-secondary)',
                                }}
                            >
                                <span style={{ fontSize: 18 }}>{icon}</span>
                                <div style={{ flex: 1 }}>
                                    <div style={{ fontWeight: 500, fontSize: 14 }}>{role}</div>
                                    <div className="font-mono text-muted" style={{ fontSize: 11 }}>{model}</div>
                                </div>
                                {isActive ? (
                                    <span className="pulse" />
                                ) : (
                                    <button
                                        className="btn btn-ghost btn-sm"
                                        onClick={() => loadModel(role)}
                                        disabled={!!loading}
                                    >
                                        {isLoading ? '...' : 'Load'}
                                    </button>
                                )}
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
}
