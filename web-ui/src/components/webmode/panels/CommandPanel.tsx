'use client';

import { useState } from 'react';
import { Bot, Send, PauseCircle, PlayCircle, StepForward, Shield } from 'lucide-react';
import { getWebSocket } from '@/lib/websocket';
import { cn } from '@/lib/utils';
import { useWebModeContext } from '@/components/webmode/WebModeProvider';

interface CommandMessage {
    id: string;
    role: 'user' | 'assistant';
    text: string;
    timestamp: string;
}

const COMMAND_PRESETS = ['continue', 'pause', 'resume', 'map intent flow', 'audit policies'];

export function CommandPanel() {
    const { controlMode, sendSignal } = useWebModeContext();
    const [input, setInput] = useState('');
    const [messages, setMessages] = useState<CommandMessage[]>([
        {
            id: 'seed-1',
            role: 'assistant',
            text: 'Command fabric online. Provide intent or directive to orchestrate OpenClaw + NeuroRift.',
            timestamp: new Date().toLocaleTimeString(),
        }
    ]);

    const submitMessage = (message: string) => {
        if (!message.trim()) return;

        const entry: CommandMessage = {
            id: `${Date.now()}-user`,
            role: 'user',
            text: message,
            timestamp: new Date().toLocaleTimeString(),
        };

        setMessages(prev => [entry, ...prev]);
        setInput('');
        sendSignal(`Intent captured: ${message}`);

        const ws = getWebSocket();
        ws.send({
            type: 'chat',
            message,
            channel: 'command',
        });

        setTimeout(() => {
            setMessages(prev => [
                {
                    id: `${Date.now()}-assistant`,
                    role: 'assistant',
                    text: 'Intent accepted. Routing through policy lattice for plan negotiation.',
                    timestamp: new Date().toLocaleTimeString(),
                },
                ...prev
            ]);
        }, 700);
    };

    return (
        <div className="space-y-4">
            <div className="flex flex-wrap items-center gap-3">
                <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-neuro-bg/60 border border-neuro-border/60">
                    <Bot className="w-4 h-4 text-cyan-300" />
                    <span className="text-xs uppercase tracking-[0.3em] text-neuro-text-muted">Chat-First Control</span>
                </div>
                <div className={cn(
                    'px-3 py-2 rounded-xl border text-xs uppercase tracking-[0.3em]',
                    controlMode === 'control' ? 'border-emerald-400/50 text-emerald-200' : 'border-amber-300/50 text-amber-200'
                )}>
                    {controlMode} access
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)] gap-4">
                <div className="space-y-3">
                    <div className="flex items-center gap-2">
                        <button className="command-chip" onClick={() => submitMessage('continue')}> <PlayCircle className="w-4 h-4" /> Continue</button>
                        <button className="command-chip" onClick={() => submitMessage('pause')}> <PauseCircle className="w-4 h-4" /> Pause</button>
                        <button className="command-chip" onClick={() => submitMessage('resume')}> <StepForward className="w-4 h-4" /> Resume</button>
                    </div>
                    <div className="space-y-3">
                        {messages.map(message => (
                            <div key={message.id} className={cn(
                                'rounded-xl border px-4 py-3 text-sm',
                                message.role === 'assistant'
                                    ? 'bg-neuro-bg/70 border-neuro-border/60 text-neuro-text-primary'
                                    : 'bg-gradient-to-r from-cyan-500/20 to-blue-500/10 border-cyan-400/30 text-neuro-text-primary'
                            )}>
                                <div className="flex items-center justify-between text-[10px] uppercase tracking-[0.3em] text-neuro-text-muted mb-2">
                                    <span>{message.role === 'assistant' ? 'System' : 'User'}</span>
                                    <span>{message.timestamp}</span>
                                </div>
                                <p>{message.text}</p>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="space-y-4">
                    <div className="rounded-xl border border-neuro-border/60 bg-neuro-bg/60 p-4">
                        <h4 className="text-xs uppercase tracking-[0.4em] text-neuro-text-muted">Intent Presets</h4>
                        <div className="mt-3 flex flex-wrap gap-2">
                            {COMMAND_PRESETS.map(preset => (
                                <button
                                    key={preset}
                                    onClick={() => submitMessage(preset)}
                                    className="px-3 py-2 rounded-lg bg-neuro-surface/80 border border-neuro-border/60 text-xs text-neuro-text-secondary hover:text-neuro-text-primary hover:border-cyan-400/40 transition"
                                >
                                    {preset}
                                </button>
                            ))}
                        </div>
                    </div>

                    <div className="rounded-xl border border-neuro-border/60 bg-neuro-bg/60 p-4">
                        <h4 className="text-xs uppercase tracking-[0.4em] text-neuro-text-muted">Safety Constraints</h4>
                        <div className="mt-3 space-y-2 text-xs text-neuro-text-secondary">
                            <div className="flex items-center gap-2">
                                <Shield className="w-4 h-4 text-emerald-300" />
                                <span>No direct OS execution from Web Mode.</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <Shield className="w-4 h-4 text-emerald-300" />
                                <span>OpenClaw proposals require NeuroRift enforcement.</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <Shield className="w-4 h-4 text-emerald-300" />
                                <span>Execution permissions immutable at runtime.</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div className="flex gap-2">
                <input
                    value={input}
                    onChange={event => setInput(event.target.value)}
                    placeholder="Transmit intent, directive, or negotiation request..."
                    className="flex-1 rounded-xl border border-neuro-border/60 bg-neuro-bg/80 px-4 py-3 text-sm text-neuro-text-primary placeholder:text-neuro-text-muted focus:outline-none focus:ring-1 focus:ring-cyan-400/50"
                />
                <button
                    onClick={() => submitMessage(input)}
                    className="px-4 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 text-white text-sm font-semibold shadow-lg shadow-cyan-500/30"
                >
                    <Send className="w-4 h-4" />
                </button>
            </div>
        </div>
    );
}
