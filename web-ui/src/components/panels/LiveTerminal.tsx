'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useWS } from '@/contexts/WebSocketContext';

interface LogEntry {
    id: string;
    type: string;       // system | tool | model | error | finding
    message: string;
    severity?: string;
    ts: number;
}

export function LiveTerminal() {
    const { subscribe } = useWS();
    const [entries, setEntries] = useState<LogEntry[]>([]);
    const [autoScroll, setAutoScroll] = useState(true);
    const logRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const unsub1 = subscribe('scan_terminal', (msg) => {
            setEntries(prev => [...prev, msg.data].slice(-500));
        });
        const unsub2 = subscribe('initial_state', (msg) => {
            setEntries(msg.data.scan_log || []);
        });
        return () => { unsub1(); unsub2(); };
    }, [subscribe]);

    // Auto-scroll
    useEffect(() => {
        if (autoScroll && logRef.current) {
            logRef.current.scrollTop = logRef.current.scrollHeight;
        }
    }, [entries, autoScroll]);

    const formatTime = (ts: number) => {
        if (!ts) return '--:--:--';
        return new Date(ts * 1000).toLocaleTimeString('en-US', { hour12: false });
    };

    const getTypePrefix = (type: string) => {
        switch (type) {
            case 'system': return '▸ SYS';
            case 'tool':   return '▸ TOOL';
            case 'model':  return '▸ MODEL';
            case 'error':  return '✗ ERR';
            case 'finding': return '◆ FIND';
            default: return '▸';
        }
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
                {/* Terminal header */}
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '10px 16px',
                    borderBottom: '1px solid var(--border-primary)',
                    background: 'var(--bg-secondary)',
                }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span style={{ color: 'var(--severity-critical)', fontSize: 10 }}>●</span>
                        <span style={{ color: 'var(--severity-medium)', fontSize: 10 }}>●</span>
                        <span style={{ color: 'var(--accent-green)', fontSize: 10 }}>●</span>
                        <span className="font-mono text-muted" style={{ fontSize: 12, marginLeft: 8 }}>
                            neurorift — scan terminal
                        </span>
                    </div>
                    <div style={{ display: 'flex', gap: 8 }}>
                        <button
                            className="btn btn-ghost btn-sm"
                            onClick={() => setAutoScroll(a => !a)}
                            style={{ fontSize: 11 }}
                        >
                            {autoScroll ? '⏸ Pause scroll' : '▶ Auto scroll'}
                        </button>
                        <button
                            className="btn btn-ghost btn-sm"
                            onClick={() => setEntries([])}
                            style={{ fontSize: 11 }}
                        >
                            Clear
                        </button>
                    </div>
                </div>

                {/* Log body */}
                <div ref={logRef} className="terminal-log" style={{
                    borderRadius: 0,
                    minHeight: 300,
                    maxHeight: 600,
                }}>
                    {entries.length === 0 ? (
                        <div style={{ color: 'var(--text-muted)', padding: 20, textAlign: 'center' }}>
                            Waiting for scan activity...
                        </div>
                    ) : (
                        entries.map((entry, i) => (
                            <div key={entry.id || i} className="log-entry">
                                <span className="log-ts">{formatTime(entry.ts)}</span>
                                <span className={`log-type-${entry.type}`} style={{ fontWeight: 600, minWidth: 60 }}>
                                    {getTypePrefix(entry.type)}
                                </span>
                                <span>{entry.message}</span>
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>
    );
}
