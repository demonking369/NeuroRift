'use client';

import React, { useState, useEffect } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8888';

type ConfigTab = 'models' | 'notifications';

export function SettingsPanel() {
    const [activeTab, setActiveTab] = useState<ConfigTab>('models');
    const [content, setContent] = useState('');
    const [loading, setLoading] = useState(false);
    const [saved, setSaved] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        loadConfig(activeTab);
    }, [activeTab]);

    const loadConfig = async (name: ConfigTab) => {
        setLoading(true);
        setError(null);
        setSaved(false);
        try {
            const res = await fetch(`${API}/api/config/${name}`);
            const data = await res.json();
            setContent(data.content || '');
        } catch (e) {
            setError('Failed to load configuration');
        }
        setLoading(false);
    };

    const saveConfig = async () => {
        setError(null);
        setSaved(false);
        try {
            const res = await fetch(`${API}/api/config/${activeTab}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content }),
            });
            if (!res.ok) {
                const data = await res.json();
                setError(data.detail || 'Save failed');
                return;
            }
            setSaved(true);
            setTimeout(() => setSaved(false), 3000);
        } catch (e) {
            setError('Failed to save configuration');
        }
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div className="card">
                <div className="card-header">
                    <span className="card-title">Configuration Editor</span>
                </div>

                {/* Tabs */}
                <div style={{ display: 'flex', gap: 4, marginBottom: 16 }}>
                    {(['models', 'notifications'] as const).map(tab => (
                        <button
                            key={tab}
                            className={`btn ${activeTab === tab ? 'btn-primary' : 'btn-ghost'} btn-sm`}
                            onClick={() => setActiveTab(tab)}
                        >
                            {tab}.yaml
                        </button>
                    ))}
                </div>

                {/* Editor */}
                {loading ? (
                    <div style={{ textAlign: 'center', padding: 24, color: 'var(--text-muted)' }}>
                        Loading...
                    </div>
                ) : (
                    <>
                        <textarea
                            value={content}
                            onChange={(e) => setContent(e.target.value)}
                            className="input font-mono"
                            style={{
                                minHeight: 400,
                                resize: 'vertical',
                                lineHeight: 1.6,
                                fontSize: 13,
                                tabSize: 2,
                            }}
                            spellCheck={false}
                        />

                        {error && (
                            <div style={{
                                marginTop: 8,
                                padding: '8px 12px',
                                borderRadius: 6,
                                background: '#ff174415',
                                border: '1px solid #ff174440',
                                color: 'var(--severity-critical)',
                                fontSize: 13,
                            }}>
                                {error}
                            </div>
                        )}

                        <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
                            <button className="btn btn-primary" onClick={saveConfig}>
                                {saved ? '✓ Saved' : 'Save Changes'}
                            </button>
                            <button className="btn btn-ghost" onClick={() => loadConfig(activeTab)}>
                                Revert
                            </button>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
}
