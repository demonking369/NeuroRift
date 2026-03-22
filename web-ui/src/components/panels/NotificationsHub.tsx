'use client';

import React, { useState, useEffect } from 'react';
import { useWS } from '@/contexts/WebSocketContext';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8888';

interface NotifEvent {
    type: string;
    channel: string;
    message: string;
    status: string;
    ts: number;
}

const CHANNELS = [
    { id: 'discord',  label: 'Discord',  icon: '💬' },
    { id: 'telegram', label: 'Telegram', icon: '✈️' },
    { id: 'slack',    label: 'Slack',    icon: '📨' },
    { id: 'whatsapp', label: 'WhatsApp', icon: '📱' },
    { id: 'email',    label: 'Email',    icon: '📧' },
    { id: 'matrix',   label: 'Matrix',   icon: '🔲' },
];

export function NotificationsHub() {
    const { subscribe } = useWS();
    const [feed, setFeed] = useState<NotifEvent[]>([]);
    const [channelStates, setChannelStates] = useState<Record<string, boolean>>({});
    const [testing, setTesting] = useState<string | null>(null);

    useEffect(() => {
        const unsub1 = subscribe('notification_feed', (msg) => {
            setFeed(prev => [msg.data, ...prev].slice(0, 100));
        });
        const unsub2 = subscribe('initial_state', (msg) => {
            setFeed(msg.data.notifications || []);
        });
        return () => { unsub1(); unsub2(); };
    }, [subscribe]);

    const testChannel = async (channel: string) => {
        setTesting(channel);
        try {
            await fetch(`${API}/api/notifications/test`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ channel }),
            });
        } catch (e) {
            console.error('Test failed:', e);
        }
        setTimeout(() => setTesting(null), 1500);
    };

    const toggleChannel = async (channel: string, enabled: boolean) => {
        setChannelStates(prev => ({ ...prev, [channel]: enabled }));
        try {
            await fetch(`${API}/api/notifications/toggle`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ channel, enabled }),
            });
        } catch (e) {
            console.error('Toggle failed:', e);
        }
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {/* Channel controls */}
            <div className="card">
                <div className="card-header">
                    <span className="card-title">Channels</span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {CHANNELS.map(ch => (
                        <div key={ch.id} style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: 12,
                            padding: '8px 12px',
                            borderRadius: 8,
                            background: 'var(--bg-secondary)',
                            border: '1px solid var(--border-primary)',
                        }}>
                            <span style={{ fontSize: 18 }}>{ch.icon}</span>
                            <span style={{ flex: 1, fontWeight: 500 }}>{ch.label}</span>
                            <button
                                className="btn btn-ghost btn-sm"
                                onClick={() => testChannel(ch.id)}
                                disabled={testing === ch.id}
                            >
                                {testing === ch.id ? '✓ Sent' : 'Test'}
                            </button>
                            <div
                                className={`toggle ${channelStates[ch.id] !== false ? 'active' : ''}`}
                                onClick={() => toggleChannel(ch.id, channelStates[ch.id] === false)}
                            />
                        </div>
                    ))}
                </div>
            </div>

            {/* Live feed */}
            <div className="card">
                <div className="card-header">
                    <span className="card-title">Live Feed</span>
                    <span className="font-mono text-muted" style={{ fontSize: 11 }}>
                        {feed.length} events
                    </span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 4, maxHeight: 400, overflowY: 'auto' }}>
                    {feed.length === 0 ? (
                        <div style={{ textAlign: 'center', padding: 24, color: 'var(--text-muted)' }}>
                            No notifications yet
                        </div>
                    ) : (
                        feed.map((ev, i) => (
                            <div key={i} style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: 8,
                                padding: '6px 8px',
                                borderRadius: 4,
                                background: 'var(--bg-secondary)',
                                fontSize: 13,
                            }}>
                                <span className="font-mono text-muted" style={{ fontSize: 10, flexShrink: 0 }}>
                                    {ev.ts ? new Date(ev.ts * 1000).toLocaleTimeString() : '—'}
                                </span>
                                <span className={`severity-badge severity-${ev.status === 'sent' ? 'low' : 'medium'}`}
                                    style={{ fontSize: 9 }}>
                                    {ev.type}
                                </span>
                                <span style={{ flex: 1, color: 'var(--text-secondary)' }}>{ev.message}</span>
                                <span className="font-mono text-cyan" style={{ fontSize: 11 }}>{ev.channel}</span>
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>
    );
}
