'use client';

import { useState, useRef, useEffect } from 'react';
import { useWebModeContext } from '@/components/webmode/WebModeProvider';
import { Terminal, Bug, Play, XCircle, RotateCw } from 'lucide-react';
import { cn } from '@/lib/utils';
import { ToolExecution } from '@/lib/webmode/adapter/interface';

export function ManualToolPanel() {
    const { adapter } = useWebModeContext();
    const [tool, setTool] = useState('nmap');
    const [args, setArgs] = useState('-sV -T4 localhost');
    const [executionId, setExecutionId] = useState<string | null>(null);
    const [output, setOutput] = useState('');
    const [status, setStatus] = useState<'idle' | 'running' | 'completed' | 'failed'>('idle');
    const outputRef = useRef<HTMLDivElement>(null);

    // Auto-scroll output
    useEffect(() => {
        if (outputRef.current) {
            outputRef.current.scrollTop = outputRef.current.scrollHeight;
        }
    }, [output]);

    // Poll execution status
    useEffect(() => {
        if (!executionId || status !== 'running') return;

        const interval = setInterval(async () => {
            try {
                const exec = await adapter.getToolStatus(executionId);
                const fullOutput = exec.stdout + (exec.stderr ? `\nERR: ${exec.stderr}` : '');

                // Only update if output changed to avoid render thrashing
                setOutput(prev => prev.length !== fullOutput.length ? fullOutput : prev);

                if (exec.status !== 'running') {
                    setStatus(exec.status);
                    setExecutionId(null);
                }
            } catch (e) {
                console.error("Poll error", e);
            }
        }, 1000);

        return () => clearInterval(interval);
    }, [executionId, status, adapter]);

    const handleRun = async () => {
        if (!args.trim()) return;
        setStatus('running');
        setOutput('');
        try {
            const id = await adapter.runTool(tool, args);
            setExecutionId(id);
        } catch (e) {
            setStatus('failed');
            setOutput(`Error launching tool: ${e}`);
        }
    };

    const handleAbort = async () => {
        if (executionId) {
            await adapter.abortTool(executionId);
            setStatus('failed'); // Optimistic update
        }
    };

    return (
        <div className="h-full flex flex-col space-y-4">
            <div className="flex items-center gap-2 mb-2">
                <Terminal className="w-4 h-4 text-cyan-400" />
                <h3 className="text-xs uppercase tracking-widest text-cyan-100 font-semibold">Manual Verification</h3>
            </div>

            <div className="grid grid-cols-[1fr_2fr_auto] gap-2 items-center">
                <select
                    value={tool}
                    onChange={e => setTool(e.target.value)}
                    className="bg-neuro-surface border border-neuro-border text-xs rounded px-2 py-1.5 focus:border-cyan-500 outline-none"
                    disabled={status === 'running'}
                >
                    {['nmap', 'nuclei', 'ffuf', 'subfinder', 'curl'].map(t => (
                        <option key={t} value={t}>{t}</option>
                    ))}
                </select>
                <input
                    type="text"
                    value={args}
                    onChange={e => setArgs(e.target.value)}
                    className="bg-neuro-surface border border-neuro-border text-xs rounded px-2 py-1.5 font-mono focus:border-cyan-500 outline-none"
                    placeholder="Arguments..."
                    disabled={status === 'running'}
                />
                <div className="flex gap-2">
                    {status === 'running' ? (
                        <button
                            onClick={handleAbort}
                            className="p-1.5 rounded bg-red-900/30 border border-red-500/50 text-red-200 hover:bg-red-900/50 transition-colors"
                        >
                            <XCircle className="w-4 h-4" />
                        </button>
                    ) : (
                        <button
                            onClick={handleRun}
                            className="p-1.5 rounded bg-cyan-900/30 border border-cyan-500/50 text-cyan-200 hover:bg-cyan-900/50 transition-colors"
                        >
                            <Play className="w-4 h-4" />
                        </button>
                    )}
                </div>
            </div>

            <div
                ref={outputRef}
                className="flex-1 rounded-lg bg-black/40 border border-neuro-border/50 p-3 font-mono text-[10px] text-neuro-text-secondary overflow-y-auto whitespace-pre-wrap min-h-[160px]"
            >
                {output || <span className="text-neuro-text-muted italic">Ready for manual instruction...</span>}
            </div>

            <div className="flex justify-between items-center text-[10px] text-neuro-text-muted border-t border-neuro-border/30 pt-2">
                <span className="flex items-center gap-1">
                    <Bug className="w-3 h-3" />
                    {adapter.mode} MODE
                </span>
                <span className={cn(
                    "flex items-center gap-1",
                    status === 'running' && "text-cyan-400 animate-pulse",
                    status === 'failed' && "text-red-400",
                    status === 'completed' && "text-emerald-400"
                )}>
                    {status === 'running' && <RotateCw className="w-3 h-3 animate-spin" />}
                    {status.toUpperCase()}
                </span>
            </div>
        </div>
    );
}
