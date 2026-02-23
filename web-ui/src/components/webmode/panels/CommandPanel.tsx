'use client';

import { useState, useRef, useEffect } from 'react';
import { Bot, Send, PauseCircle, PlayCircle, StepForward, Shield, Sparkles, AlertTriangle, Fingerprint, StopCircle, RefreshCw } from 'lucide-react';
import { getWebSocket } from '@/lib/websocket';
import { cn } from '@/lib/utils';
import { useWebModeContext } from '@/components/webmode/WebModeProvider';

interface CommandMessage {
    id: string;
    role: 'user' | 'assistant';
    text: string;
    timestamp: string;
    status?: 'draft' | 'negotiating' | 'executed' | 'streaming';
}

const COMMAND_PRESETS = ['continue', 'pause', 'resume', 'map intent flow', 'audit policies'];

export function CommandPanel() {
    const { controlMode, adapter } = useWebModeContext();
    const [input, setInput] = useState('');
    const [isDrafting, setIsDrafting] = useState(false);
    const [isStreaming, setIsStreaming] = useState(false);
    const [confidence, setConfidence] = useState(0);
    const [messages, setMessages] = useState<CommandMessage[]>([
        {
            id: 'seed-1',
            role: 'assistant',
            text: 'Command fabric online. Provide intent or directive to orchestrate OpenClaw + NeuroRift.',
            timestamp: '00:00:00',
            status: 'executed'
        }
    ]);
    const bottomRef = useRef<HTMLDivElement>(null);

    // Auto-scroll
    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, isDrafting]);

    // Simulate "Confidence" based on input length/complexity
    useEffect(() => {
        if (!input) {
            setConfidence(0);
            return;
        }
        // Fake heuristic: longer commands with specific keywords = higher confidence
        const score = Math.min(0.95, (input.length / 50) + (input.includes('scan') ? 0.2 : 0) + (input.includes('analyze') ? 0.2 : 0));
        setConfidence(score);
    }, [input]);

    const handleDraft = () => {
        if (!input.trim()) return;
        setIsDrafting(true);
    };

    const confirmIntent = async () => {
        if (!input.trim()) return;

        const userMsg: CommandMessage = {
            id: `${Date.now()}-user`,
            role: 'user',
            text: input,
            timestamp: new Date().toLocaleTimeString(),
            status: 'negotiating'
        };

        const assistantMsgId = `${Date.now()}-assistant`;
        const assistantMsg: CommandMessage = {
            id: assistantMsgId,
            role: 'assistant',
            text: '',
            timestamp: new Date().toLocaleTimeString(),
            status: 'negotiating'
        };

        setMessages(prev => [...prev, userMsg, assistantMsg]);
        const currentInput = input;
        setInput('');
        setIsDrafting(false);
        setIsStreaming(true);

        try {
            let fullText = '';
            for await (const chunk of adapter.sendAIMessage(currentInput)) {
                fullText += chunk;
                setMessages(prev => prev.map(m =>
                    m.id === assistantMsgId
                        ? { ...m, text: fullText, status: 'streaming' }
                        : m
                ));
            }

            // Finalize
            setMessages(prev => prev.map(m =>
                m.id === assistantMsgId
                    ? { ...m, status: 'executed' }
                    : m
            ));

        } catch (error) {
            setMessages(prev => prev.map(m =>
                m.id === assistantMsgId
                    ? { ...m, text: m.text + '\n[Error: Execution interrupted or failed]', status: 'executed' }
                    : m
            ));
        } finally {
            setIsStreaming(false);
        }
    };

    const handleStop = () => {
        adapter.cancelAI();
        setIsStreaming(false);
    };

    return (
        <div className="space-y-4 h-full flex flex-col">
            <div className="flex flex-wrap items-center gap-3 shrink-0">
                <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-neuro-bg/60 border border-neuro-border/60">
                    <Bot className="w-4 h-4 text-cyan-300" />
                    <span className="text-xs uppercase tracking-[0.3em] text-neuro-text-muted">Arbitration Fabric</span>
                </div>
                <div className={cn(
                    'px-3 py-2 rounded-xl border text-xs uppercase tracking-[0.3em]',
                    controlMode === 'control' ? 'border-emerald-400/50 text-emerald-200' : 'border-amber-300/50 text-amber-200'
                )}>
                    {controlMode} access
                </div>
                {/* Mode Indicator */}
                <div className="ml-auto flex items-center gap-2 text-[10px] uppercase tracking-wider text-neuro-text-muted opacity-60">
                    <div className={cn("w-1.5 h-1.5 rounded-full", adapter.mode === 'REAL' ? "bg-emerald-500" : "bg-purple-500")} />
                    {adapter.mode} MODE
                </div>
            </div>

            <div className="flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)] gap-4">
                <div className="space-y-3 flex flex-col h-full min-h-0">
                    {/* Stream Area */}
                    <div className="flex-1 overflow-y-auto space-y-3 pr-2 custom-scrollbar">
                        {messages.map(message => (
                            <div key={message.id} className={cn(
                                'rounded-xl border px-4 py-3 text-sm transition-all duration-500',
                                message.role === 'assistant'
                                    ? 'bg-neuro-bg/70 border-neuro-border/60 text-neuro-text-primary'
                                    : 'bg-gradient-to-r from-cyan-500/10 to-blue-500/5 border-cyan-400/20 text-neuro-text-primary',
                                message.status === 'negotiating' && 'opacity-70 border-amber-400/30'
                            )}>
                                <div className="flex items-center justify-between text-[10px] uppercase tracking-[0.3em] text-neuro-text-muted mb-2">
                                    <div className="flex items-center gap-2">
                                        <span>{message.role === 'assistant' ? 'System' : 'Operator'}</span>
                                        {message.status === 'negotiating' && (
                                            <span className="text-amber-300 flex items-center gap-1">
                                                <Sparkles className="w-3 h-3 animate-spin" /> Negotiating
                                            </span>
                                        )}
                                        {message.status === 'streaming' && (
                                            <span className="text-cyan-300 flex items-center gap-1">
                                                <RefreshCw className="w-3 h-3 animate-spin" /> Streaming
                                            </span>
                                        )}
                                    </div>
                                    <span>{message.timestamp}</span>
                                </div>
                                <div className="whitespace-pre-wrap font-light leading-relaxed">
                                    {message.text || <span className="animate-pulse opacity-50">Thinking...</span>}
                                </div>
                            </div>
                        ))}
                        <div ref={bottomRef} />
                    </div>

                    {/* Input Area */}
                    <div className="relative shrink-0">
                        {isDrafting ? (
                            <div className="absolute bottom-full left-0 right-0 mb-2 p-4 rounded-xl border border-cyan-400/30 bg-cyan-950/90 backdrop-blur-md shadow-2xl z-10 space-y-3 animate-in slide-in-from-bottom-2">
                                <div className="flex items-center justify-between text-xs uppercase tracking-widest text-cyan-200">
                                    <div className="flex items-center gap-2"><Fingerprint className="w-4 h-4" /> Intent Draft</div>
                                    <div>{(confidence * 100).toFixed(0)}% Confidence</div>
                                </div>
                                <div className="text-lg text-white font-light border-l-2 border-cyan-400 pl-3">
                                    "{input}"
                                </div>
                                <div className="flex items-center gap-2 text-xs text-neuro-text-muted mt-2 bg-black/20 p-2 rounded">
                                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                                    <span>Projected Impact: 3 Agents, 12% Memory Load</span>
                                </div>
                                <div className="flex gap-2 pt-2">
                                    <button
                                        onClick={() => setIsDrafting(false)}
                                        className="flex-1 px-4 py-2 border border-neuro-border/60 rounded-lg text-xs hover:bg-white/5"
                                    >
                                        Discard
                                    </button>
                                    <button
                                        onClick={confirmIntent}
                                        className="flex-1 px-4 py-2 bg-cyan-500/20 border border-cyan-400/50 text-cyan-200 rounded-lg text-xs hover:bg-cyan-500/30 flex items-center justify-center gap-2"
                                    >
                                        <Send className="w-3 h-3" /> Execute
                                    </button>
                                </div>
                            </div>
                        ) : (
                            <div className="flex gap-2">
                                <input
                                    value={input}
                                    onChange={event => setInput(event.target.value)}
                                    onKeyDown={event => event.key === 'Enter' && !isStreaming && handleDraft()}
                                    placeholder={isStreaming ? "System executing..." : "Draft intent for arbitration..."}
                                    disabled={isStreaming}
                                    className="flex-1 rounded-xl border border-neuro-border/60 bg-neuro-bg/80 px-4 py-3 text-sm text-neuro-text-primary placeholder:text-neuro-text-muted focus:outline-none focus:ring-1 focus:ring-cyan-400/50 disabled:opacity-50"
                                />
                                {isStreaming ? (
                                    <button
                                        onClick={handleStop}
                                        className="px-4 py-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm font-semibold hover:bg-rose-500/20 transition-all flex items-center gap-2"
                                    >
                                        <StopCircle className="w-4 h-4" /> Stop
                                    </button>
                                ) : (
                                    <button
                                        onClick={handleDraft}
                                        disabled={!input.trim()}
                                        className="px-4 py-3 rounded-xl bg-gradient-to-r from-neuro-bg to-neuro-surface border border-neuro-border/60 text-neuro-text-primary text-sm font-semibold hover:border-cyan-400/40 disabled:opacity-50 transition-all"
                                    >
                                        Review
                                    </button>
                                )}
                            </div>
                        )}

                        {/* Confidence Bar Under Input */}
                        <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-neuro-border/30 overflow-hidden rounded-b-xl">
                            <div
                                className="h-full bg-gradient-to-r from-transparent via-cyan-400 to-transparent transition-all duration-300"
                                style={{
                                    width: `${confidence * 100}%`,
                                    opacity: input && !isStreaming ? 1 : 0
                                }}
                            />
                        </div>
                    </div>
                </div>

                <div className="space-y-4">
                    <div className="rounded-xl border border-neuro-border/60 bg-neuro-bg/60 p-4">
                        <h4 className="text-xs uppercase tracking-[0.4em] text-neuro-text-muted mb-3">Directives</h4>
                        <div className="space-y-2">
                            {COMMAND_PRESETS.map(preset => (
                                <button
                                    key={preset}
                                    onClick={() => {
                                        if (isStreaming) return;
                                        setInput(preset);
                                        setTimeout(() => setIsDrafting(true), 0);
                                    }}
                                    disabled={isStreaming}
                                    className="w-full text-left px-3 py-2 rounded-lg bg-neuro-surface/80 border border-neuro-border/60 text-xs text-neuro-text-secondary hover:text-neuro-text-primary hover:border-cyan-400/40 transition flex items-center justify-between group disabled:opacity-50"
                                >
                                    <span>{preset}</span>
                                    <Send className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity text-cyan-400" />
                                </button>
                            ))}
                        </div>
                    </div>

                    <div className="rounded-xl border border-rose-500/10 bg-rose-950/5 p-4">
                        <div className="flex items-center gap-2 mb-2 text-rose-300/80">
                            <AlertTriangle className="w-4 h-4" />
                            <h4 className="text-xs uppercase tracking-[0.2em]">Safety Lock</h4>
                        </div>
                        <div className="space-y-2 text-[10px] text-neuro-text-muted leading-relaxed">
                            <p>Arbitration prevents direct execution. All intents are simulated against current <span className="text-rose-200">Rules of Engagement</span> before agent dispatch.</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
