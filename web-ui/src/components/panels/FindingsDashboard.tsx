'use client';

import React, { useState, useEffect } from 'react';
import { useWS } from '@/contexts/WebSocketContext';

interface Finding {
    tool: string;
    severity: string;
    affected_url: string;
    parameter: string;
    confidence: string;
    cvss_score: string;
    evidence?: string;
    impact?: string;
    [key: string]: any;
}

const SEVERITY_ORDER = ['critical', 'high', 'medium', 'low', 'info'];

function formatH1Report(f: Finding): string {
    return `## ${f.severity?.toUpperCase()} — ${f.tool}

**Affected URL:** ${f.affected_url || 'N/A'}
**Parameter:** ${f.parameter || 'N/A'}
**Severity:** ${f.severity}
**CVSS Score:** ${f.cvss_score || 'N/A'}
**Confidence:** ${f.confidence || 'N/A'}

### Description
A ${f.severity} severity ${f.tool} vulnerability was identified.

### Steps to Reproduce
1. Navigate to: ${f.affected_url}
2. Parameter: ${f.parameter}

### Impact
${f.impact || 'Refer to CVSS score for impact assessment.'}

### Evidence
\`\`\`
${f.evidence || 'See attached evidence.'}
\`\`\`
`;
}

export function FindingsDashboard() {
    const { subscribe } = useWS();
    const [findings, setFindings] = useState<Finding[]>([]);
    const [expanded, setExpanded] = useState<Set<number>>(new Set());
    const [filter, setFilter] = useState<string>('all');
    const [copied, setCopied] = useState<number | null>(null);

    useEffect(() => {
        const unsub1 = subscribe('finding', (msg) => {
            setFindings(prev => [msg.data, ...prev]);
        });
        const unsub2 = subscribe('initial_state', (msg) => {
            setFindings(msg.data.findings || []);
        });
        return () => { unsub1(); unsub2(); };
    }, [subscribe]);

    const toggleExpand = (idx: number) => {
        setExpanded(prev => {
            const next = new Set(prev);
            next.has(idx) ? next.delete(idx) : next.add(idx);
            return next;
        });
    };

    const copyH1 = (f: Finding, idx: number) => {
        navigator.clipboard.writeText(formatH1Report(f));
        setCopied(idx);
        setTimeout(() => setCopied(null), 2000);
    };

    const filtered = filter === 'all'
        ? findings
        : findings.filter(f => f.severity?.toLowerCase() === filter);

    const counts = SEVERITY_ORDER.reduce((acc, s) => {
        acc[s] = findings.filter(f => f.severity?.toLowerCase() === s).length;
        return acc;
    }, {} as Record<string, number>);

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {/* Summary cards */}
            <div className="grid-3" style={{ gridTemplateColumns: 'repeat(5, 1fr)' }}>
                {SEVERITY_ORDER.map(sev => (
                    <button
                        key={sev}
                        className="card"
                        style={{
                            cursor: 'pointer',
                            textAlign: 'center',
                            borderColor: filter === sev ? `var(--severity-${sev})` : undefined,
                            padding: '12px',
                        }}
                        onClick={() => setFilter(f => f === sev ? 'all' : sev)}
                    >
                        <div className="font-mono" style={{
                            fontSize: 24,
                            fontWeight: 700,
                            color: `var(--severity-${sev})`,
                        }}>
                            {counts[sev] || 0}
                        </div>
                        <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                            {sev}
                        </div>
                    </button>
                ))}
            </div>

            {/* Findings list */}
            {filtered.length === 0 ? (
                <div className="card" style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>
                    {findings.length === 0 ? 'No findings yet — start a scan' : 'No findings match filter'}
                </div>
            ) : (
                filtered.map((f, idx) => (
                    <div key={idx} className="card" style={{ padding: 0, overflow: 'hidden' }}>
                        {/* Finding header */}
                        <div
                            style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: 12,
                                padding: '14px 16px',
                                cursor: 'pointer',
                            }}
                            onClick={() => toggleExpand(idx)}
                        >
                            <span className={`severity-badge severity-${f.severity?.toLowerCase()}`}>
                                {f.severity}
                            </span>
                            <span style={{ flex: 1, fontWeight: 500 }}>{f.tool}</span>
                            <span className="font-mono text-muted" style={{ fontSize: 12 }}>
                                {f.affected_url}
                            </span>
                            <button
                                className="btn btn-ghost btn-sm"
                                onClick={(e) => { e.stopPropagation(); copyH1(f, idx); }}
                                title="Copy as H1 report"
                            >
                                {copied === idx ? '✓ Copied' : '📋 H1'}
                            </button>
                            <span style={{ color: 'var(--text-muted)' }}>
                                {expanded.has(idx) ? '▲' : '▼'}
                            </span>
                        </div>

                        {/* Expanded evidence */}
                        {expanded.has(idx) && (
                            <div style={{
                                borderTop: '1px solid var(--border-primary)',
                                padding: 16,
                                background: 'var(--bg-secondary)',
                            }}>
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 12 }}>
                                    <div>
                                        <span className="text-muted" style={{ fontSize: 11 }}>Parameter</span>
                                        <div className="font-mono">{f.parameter || 'N/A'}</div>
                                    </div>
                                    <div>
                                        <span className="text-muted" style={{ fontSize: 11 }}>CVSS Score</span>
                                        <div className="font-mono">{f.cvss_score || 'N/A'}</div>
                                    </div>
                                    <div>
                                        <span className="text-muted" style={{ fontSize: 11 }}>Confidence</span>
                                        <div className="font-mono">{f.confidence || 'N/A'}</div>
                                    </div>
                                </div>

                                {f.evidence && (
                                    <div>
                                        <span className="text-muted" style={{ fontSize: 11 }}>Evidence</span>
                                        <pre className="terminal-log" style={{ marginTop: 4 }}>
                                            {f.evidence}
                                        </pre>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                ))
            )}
        </div>
    );
}
