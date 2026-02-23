'use client';

import { useState, useEffect } from 'react';
import { useWebModeContext } from '@/components/webmode/WebModeProvider';
import { Archive, Clock, Trash2, ArrowRight } from 'lucide-react';
import { Session } from '@/lib/webmode/adapter/interface';
import { cn } from '@/lib/utils';

export function SessionManagerPanel() {
    const { adapter } = useWebModeContext();
    const [sessions, setSessions] = useState<Session[]>([]);
    const [loading, setLoading] = useState(false);

    const refresh = async () => {
        setLoading(true);
        try {
            const list = await adapter.listSessions();
            setSessions(list);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        refresh();
    }, [adapter]);

    const handleDelete = async (id: string, e: React.MouseEvent) => {
        e.stopPropagation();
        if (confirm('Delete session?')) {
            await adapter.deleteSession(id);
            refresh();
        }
    };

    return (
        <div className="h-full flex flex-col space-y-3">
            <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2">
                    <Archive className="w-4 h-4 text-cyan-400" />
                    <h3 className="text-xs uppercase tracking-widest text-cyan-100 font-semibold">Sessions</h3>
                </div>
                <button onClick={refresh} className="text-[10px] text-cyan-400 hover:text-cyan-300">REFRESH</button>
            </div>

            <div className="flex-1 overflow-y-auto space-y-2 pr-1 custom-scrollbar">
                {sessions.length === 0 ? (
                    <div className="text-center py-8 text-neuro-text-muted text-xs">No active sessions.</div>
                ) : (
                    sessions.map(s => (
                        <div key={s.id} className="group flex flex-col gap-1 p-3 rounded-lg bg-neuro-surface/50 border border-neuro-border/50 hover:border-cyan-500/30 transition-colors cursor-pointer">
                            <div className="flex justify-between items-start">
                                <span className="text-sm text-neuro-text-primary font-medium">{s.target}</span>
                                <span className={cn(
                                    "text-[9px] px-1.5 py-0.5 rounded border uppercase",
                                    s.status === 'active' ? "border-emerald-500/30 text-emerald-400 bg-emerald-500/10" : "border-neuro-border text-neuro-text-muted"
                                )}>{s.status}</span>
                            </div>
                            <div className="flex justify-between items-center text-[10px] text-neuro-text-secondary mt-1">
                                <span className="flex items-center gap-1">
                                    <Clock className="w-3 h-3" />
                                    {new Date(s.timestamp).toLocaleDateString()}
                                </span>
                                <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                    <button
                                        className="p-1 hover:text-red-400"
                                        onClick={(e) => handleDelete(s.id, e)}
                                    >
                                        <Trash2 className="w-3 h-3" />
                                    </button>
                                    <button className="p-1 hover:text-cyan-400">
                                        <ArrowRight className="w-3 h-3" />
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}
