'use client';

import React, { useState, useCallback, useRef, useEffect } from 'react';
import { useWS } from '@/contexts/WebSocketContext';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8888';

export function ScanControl() {
    const { isConnected, subscribe } = useWS();
    const [target, setTarget] = useState('');
    const [targetValid, setTargetValid] = useState<boolean | null>(null);
    const [scopeFile, setScopeFile] = useState<string | null>(null);
    const [uploading, setUploading] = useState(false);
    const [pipeline, setPipeline] = useState<any>({ status: 'idle', stage: '', target: '' });
    const [dragActive, setDragActive] = useState(false);
    const fileRef = useRef<HTMLInputElement>(null);

    // Subscribe to pipeline state
    useEffect(() => {
        const unsub1 = subscribe('pipeline_state', (msg) => setPipeline(msg.data));
        const unsub2 = subscribe('initial_state', (msg) => setPipeline(msg.data.pipeline));
        return () => { unsub1(); unsub2(); };
    }, [subscribe]);

    // Validate URL
    const validateTarget = (url: string) => {
        setTarget(url);
        if (!url) { setTargetValid(null); return; }
        try {
            const u = new URL(url.startsWith('http') ? url : `https://${url}`);
            setTargetValid(!!u.hostname && u.hostname.includes('.'));
        } catch {
            setTargetValid(false);
        }
    };

    // Upload scope file
    const handleUpload = async (file: File) => {
        setUploading(true);
        try {
            const form = new FormData();
            form.append('file', file);
            const res = await fetch(`${API}/api/scope/upload`, { method: 'POST', body: form });
            const data = await res.json();
            setScopeFile(data.filename);
        } catch (e) {
            console.error('Upload failed:', e);
        }
        setUploading(false);
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setDragActive(false);
        const file = e.dataTransfer.files[0];
        if (file) handleUpload(file);
    };

    // Start scan
    const startScan = async () => {
        try {
            await fetch(`${API}/api/scan/start`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ target, scope_file: scopeFile }),
            });
        } catch (e) {
            console.error('Failed to start scan:', e);
        }
    };

    // Stop scan
    const stopScan = async () => {
        try {
            await fetch(`${API}/api/scan/stop`, { method: 'POST' });
        } catch (e) {
            console.error('Failed to stop scan:', e);
        }
    };

    const isRunning = pipeline.status === 'running';
    const canStart = targetValid && isConnected && !isRunning;

    const STAGES = ['initializing', 'recon', 'planning', 'executing', 'reporting', 'complete'];
    const currentStageIdx = STAGES.indexOf(pipeline.stage);

    return (
        <div className="flex-col gap-4" style={{ display: 'flex' }}>
            {/* Target URL Input */}
            <div className="card">
                <div className="card-header">
                    <span className="card-title">Target</span>
                    {targetValid === true && <span style={{ color: 'var(--accent-green)', fontSize: 12 }}>✓ Valid</span>}
                    {targetValid === false && <span style={{ color: 'var(--severity-critical)', fontSize: 12 }}>✗ Invalid URL</span>}
                </div>
                <input
                    className="input"
                    type="text"
                    placeholder="https://example.com"
                    value={target}
                    onChange={(e) => validateTarget(e.target.value)}
                    disabled={isRunning}
                    style={{
                        borderColor: targetValid === false ? 'var(--severity-critical)' :
                                    targetValid === true ? 'var(--accent-green)' : undefined,
                    }}
                />
            </div>

            {/* Scope File Upload */}
            <div className="card">
                <div className="card-header">
                    <span className="card-title">Scope File</span>
                    {scopeFile && <span className="font-mono" style={{ color: 'var(--accent-cyan)', fontSize: 12 }}>{scopeFile}</span>}
                </div>
                <div
                    className={`drop-zone ${dragActive ? 'active' : ''}`}
                    onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
                    onDragLeave={() => setDragActive(false)}
                    onDrop={handleDrop}
                    onClick={() => fileRef.current?.click()}
                >
                    {uploading ? (
                        <span>Uploading...</span>
                    ) : scopeFile ? (
                        <span>✓ {scopeFile} — Drop another to replace</span>
                    ) : (
                        <span>Drop scope file here or click to browse</span>
                    )}
                </div>
                <input
                    ref={fileRef}
                    type="file"
                    accept=".txt,.scope,.yaml,.yml"
                    style={{ display: 'none' }}
                    onChange={(e) => e.target.files?.[0] && handleUpload(e.target.files[0])}
                />
            </div>

            {/* Start / Stop Controls */}
            <div className="card" style={{ display: 'flex', gap: 12 }}>
                {!isRunning ? (
                    <button
                        className="btn btn-primary"
                        style={{ flex: 1, padding: '14px 24px', fontSize: 16 }}
                        onClick={startScan}
                        disabled={!canStart}
                    >
                        🚀 Start Scan
                    </button>
                ) : (
                    <button
                        className="btn btn-danger"
                        style={{ flex: 1, padding: '14px 24px', fontSize: 16 }}
                        onClick={stopScan}
                    >
                        ⏹ Stop Scan
                    </button>
                )}
            </div>

            {/* Pipeline Progress */}
            {isRunning && (
                <div className="card">
                    <div className="card-header">
                        <span className="card-title">Pipeline Progress</span>
                        <span className="font-mono text-accent" style={{ fontSize: 12 }}>
                            {pipeline.stage?.toUpperCase()}
                        </span>
                    </div>
                    <div style={{ display: 'flex', gap: 4 }}>
                        {STAGES.map((stage, i) => (
                            <div
                                key={stage}
                                style={{
                                    flex: 1,
                                    height: 6,
                                    borderRadius: 3,
                                    background: i <= currentStageIdx
                                        ? 'var(--accent-green)'
                                        : 'var(--bg-input)',
                                    transition: 'background 0.3s ease',
                                    boxShadow: i === currentStageIdx ? 'var(--glow-green)' : 'none',
                                }}
                            />
                        ))}
                    </div>
                    <div style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        marginTop: 8,
                        fontSize: 10,
                        color: 'var(--text-muted)',
                        fontFamily: 'var(--font-mono)',
                    }}>
                        {STAGES.map(s => <span key={s}>{s}</span>)}
                    </div>
                </div>
            )}
        </div>
    );
}
