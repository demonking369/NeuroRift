'use client';

import React, { useState, useEffect } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8888';

interface Report {
    name: string;
    size_bytes: number;
    modified: number;
}

export function ReportsPanel() {
    const [reports, setReports] = useState<Report[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchReports();
    }, []);

    const fetchReports = async () => {
        setLoading(true);
        try {
            const res = await fetch(`${API}/api/reports`);
            const data = await res.json();
            setReports(data.reports || []);
        } catch (e) {
            console.error('Failed to fetch reports:', e);
        }
        setLoading(false);
    };

    const formatSize = (bytes: number) => {
        if (bytes < 1024) return `${bytes} B`;
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    };

    const formatDate = (ts: number) => {
        return new Date(ts * 1000).toLocaleString();
    };

    const download = (name: string) => {
        window.open(`${API}/api/reports/${name}`, '_blank');
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div className="card">
                <div className="card-header">
                    <span className="card-title">Generated Reports</span>
                    <button className="btn btn-ghost btn-sm" onClick={fetchReports}>
                        ↻ Refresh
                    </button>
                </div>

                {loading ? (
                    <div style={{ textAlign: 'center', padding: 24, color: 'var(--text-muted)' }}>
                        Loading...
                    </div>
                ) : reports.length === 0 ? (
                    <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>
                        No reports generated yet — complete a scan first
                    </div>
                ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                        {reports.map(r => (
                            <div key={r.name} style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: 12,
                                padding: '10px 12px',
                                borderRadius: 8,
                                background: 'var(--bg-secondary)',
                                border: '1px solid var(--border-primary)',
                            }}>
                                <span style={{ fontSize: 18 }}>📄</span>
                                <div style={{ flex: 1 }}>
                                    <div className="font-mono" style={{ fontWeight: 500, fontSize: 14 }}>{r.name}</div>
                                    <div style={{ display: 'flex', gap: 16, fontSize: 11, color: 'var(--text-muted)' }}>
                                        <span>{formatSize(r.size_bytes)}</span>
                                        <span>{formatDate(r.modified)}</span>
                                    </div>
                                </div>
                                <button
                                    className="btn btn-ghost btn-sm"
                                    onClick={() => download(r.name)}
                                >
                                    ⬇ Download
                                </button>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
