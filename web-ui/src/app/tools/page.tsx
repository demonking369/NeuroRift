'use client';

import { Wrench, Search, Play, Square, Terminal } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { getWebSocket } from '@/lib/websocket';
import { useNeuroRift } from '@/lib/hooks';

interface Tool {
    name: string;
    category: string;
    description: string;
    risk_level: 'low' | 'medium' | 'high';
    allowed_modes: string[];
}

const TOOL_CATALOG: Tool[] = [
    { name: 'nmap', category: 'Reconnaissance', description: 'Network exploration and security auditing', risk_level: 'low', allowed_modes: ['OFFENSIVE', 'DEFENSIVE'] },
    { name: 'nuclei', category: 'Scanning', description: 'Template-driven vulnerability scanner', risk_level: 'medium', allowed_modes: ['OFFENSIVE', 'DEFENSIVE'] },
    { name: 'sqlmap', category: 'Exploitation', description: 'SQL injection assessment utility', risk_level: 'high', allowed_modes: ['OFFENSIVE'] },
    { name: 'subfinder', category: 'Reconnaissance', description: 'Passive subdomain discovery', risk_level: 'low', allowed_modes: ['OFFENSIVE', 'DEFENSIVE'] },
    { name: 'httpx', category: 'Reconnaissance', description: 'Fast HTTP probing toolkit', risk_level: 'low', allowed_modes: ['OFFENSIVE', 'DEFENSIVE'] },
    { name: 'ffuf', category: 'Scanning', description: 'Web fuzzing and directory enumeration', risk_level: 'medium', allowed_modes: ['OFFENSIVE'] },
];

const CATEGORIES = ['All', 'Reconnaissance', 'Scanning', 'Exploitation'];
const RISK_COLORS = { low: 'text-severity-low', medium: 'text-severity-medium', high: 'text-severity-critical' };

export default function ToolsPage() {
    const { session, tasks } = useNeuroRift();
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedCategory, setSelectedCategory] = useState('All');
    const [target, setTarget] = useState('');
    const [liveOutput, setLiveOutput] = useState<Record<string, string>>({});

    useEffect(() => {
        const handler = (evt: Event) => {
            const event = evt as CustomEvent;
            const taskId = event.detail?.task_id;
            const chunk = event.detail?.chunk ?? '';
            if (!taskId) return;

            setLiveOutput(prev => ({
                ...prev,
                [taskId]: `${prev[taskId] ?? ''}${chunk}\n`,
            }));
        };

        window.addEventListener('neurorift:task_output', handler);
        return () => window.removeEventListener('neurorift:task_output', handler);
    }, []);

    const filteredTools = useMemo(() => TOOL_CATALOG.filter(tool => {
        const matchesSearch = tool.name.toLowerCase().includes(searchQuery.toLowerCase()) || tool.description.toLowerCase().includes(searchQuery.toLowerCase());
        const matchesCategory = selectedCategory === 'All' || tool.category === selectedCategory;
        const matchesMode = !session || tool.allowed_modes.includes(session.mode);
        return matchesSearch && matchesCategory && matchesMode;
    }), [searchQuery, selectedCategory, session]);

    const runTool = (tool: Tool) => {
        if (!session || !target.trim()) {
            alert('Load/create a session and provide a target.');
            return;
        }

        const ws = getWebSocket();
        ws.send({
            type: 'queue_task',
            tool_name: tool.name,
            target: target.trim(),
            args: {},
        });
    };

    const cancelTask = (taskId: string) => {
        getWebSocket().send({ type: 'cancel_task', task_id: taskId });
    };

    return (
        <div className="p-6 space-y-6">
            <div>
                <h1 className="text-3xl font-bold text-neuro-text-primary">Security Tools</h1>
                <p className="text-neuro-text-secondary mt-1">Manual tool execution through NeuroRift enforcement</p>
            </div>

            <div className="glass-card p-4 space-y-4">
                <div className="grid grid-cols-1 lg:grid-cols-[1fr_240px] gap-4">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neuro-text-muted" />
                        <input
                            type="text"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder="Search tools..."
                            className="w-full pl-10 pr-4 py-2 bg-neuro-surface border border-neuro-border rounded-lg text-neuro-text-primary placeholder-neuro-text-muted focus:outline-none focus:border-neuro-primary"
                        />
                    </div>
                    <input
                        type="text"
                        value={target}
                        onChange={(event) => setTarget(event.target.value)}
                        placeholder="Target (domain/IP)"
                        className="w-full px-3 py-2 bg-neuro-surface border border-neuro-border rounded-lg text-neuro-text-primary placeholder-neuro-text-muted focus:outline-none focus:border-neuro-primary"
                    />
                </div>

                <div className="flex items-center gap-2 overflow-x-auto">
                    {CATEGORIES.map((category) => (
                        <button
                            key={category}
                            onClick={() => setSelectedCategory(category)}
                            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors whitespace-nowrap ${selectedCategory === category ? 'bg-neuro-primary text-white' : 'bg-neuro-surface text-neuro-text-secondary hover:bg-neuro-bg'}`}
                        >
                            {category}
                        </button>
                    ))}
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredTools.map((tool) => (
                    <div key={tool.name} className="glass-card p-5 hover:border-neuro-primary/50 transition-all">
                        <div className="flex items-start justify-between mb-3">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-lg bg-neuro-primary/20 flex items-center justify-center">
                                    <Wrench className="w-5 h-5 text-neuro-primary" />
                                </div>
                                <div>
                                    <h3 className="font-semibold text-neuro-text-primary">{tool.name}</h3>
                                    <span className="text-xs text-neuro-text-muted">{tool.category}</span>
                                </div>
                            </div>
                            <span className={`text-xs font-medium capitalize ${RISK_COLORS[tool.risk_level]}`}>{tool.risk_level}</span>
                        </div>

                        <p className="text-sm text-neuro-text-secondary mb-4 line-clamp-2">{tool.description}</p>

                        <button onClick={() => runTool(tool)} className="w-full btn-primary flex items-center justify-center gap-2 text-sm py-2 disabled:opacity-50" disabled={!session || !target.trim()}>
                            <Play className="w-4 h-4" /> Execute
                        </button>
                    </div>
                ))}
            </div>

            <div className="glass-card p-5 space-y-3">
                <div className="flex items-center gap-2 text-neuro-text-primary"><Terminal className="w-4 h-4" /> Live Execution Stream</div>
                {tasks.length === 0 ? <p className="text-sm text-neuro-text-muted">No tool executions yet.</p> : tasks.map(task => (
                    <div key={task.id} className="rounded-lg border border-neuro-border bg-neuro-bg/50 p-3 space-y-2">
                        <div className="flex items-center justify-between text-xs">
                            <span className="text-neuro-text-secondary">{task.label}</span>
                            <span className="text-neuro-text-muted uppercase">{task.status}</span>
                        </div>
                        <div className="h-1.5 rounded bg-neuro-border/70 overflow-hidden"><div className="h-full bg-neuro-primary" style={{ width: `${task.progress}%` }} /></div>
                        <pre className="terminal-text whitespace-pre-wrap max-h-36 overflow-y-auto text-neuro-text-secondary">{liveOutput[task.id] || 'Awaiting output...'}</pre>
                        {task.status === 'running' && (
                            <button onClick={() => cancelTask(task.id)} className="text-xs px-3 py-1 rounded border border-severity-critical/40 text-severity-critical flex items-center gap-1">
                                <Square className="w-3 h-3" /> Cancel
                            </button>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
}
