'use client';

import { useEffect, useRef, useState, useCallback } from 'react';

export interface WSMessage {
    channel: string;
    data: any;
    ts: number;
}

type MessageHandler = (msg: WSMessage) => void;

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8888/ws';
const RECONNECT_DELAY = 2000;
const MAX_RECONNECT_DELAY = 30000;

export function useWebSocket() {
    const [isConnected, setIsConnected] = useState(false);
    const wsRef = useRef<WebSocket | null>(null);
    const handlersRef = useRef<Map<string, Set<MessageHandler>>>(new Map());
    const reconnectDelayRef = useRef(RECONNECT_DELAY);
    const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
    const mountedRef = useRef(true);

    const subscribe = useCallback((channel: string, handler: MessageHandler) => {
        if (!handlersRef.current.has(channel)) {
            handlersRef.current.set(channel, new Set());
        }
        handlersRef.current.get(channel)!.add(handler);

        return () => {
            handlersRef.current.get(channel)?.delete(handler);
        };
    }, []);

    const send = useCallback((data: any) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify(data));
        }
    }, []);

    const connect = useCallback(() => {
        if (!mountedRef.current) return;
        if (wsRef.current?.readyState === WebSocket.OPEN) return;

        try {
            const ws = new WebSocket(WS_URL);

            ws.onopen = () => {
                if (!mountedRef.current) { ws.close(); return; }
                setIsConnected(true);
                reconnectDelayRef.current = RECONNECT_DELAY;
            };

            ws.onmessage = (event) => {
                try {
                    const msg: WSMessage = JSON.parse(event.data);
                    const handlers = handlersRef.current.get(msg.channel);
                    if (handlers) {
                        handlers.forEach(h => h(msg));
                    }
                    // Also fire wildcard handlers
                    const wildcardHandlers = handlersRef.current.get('*');
                    if (wildcardHandlers) {
                        wildcardHandlers.forEach(h => h(msg));
                    }
                } catch { /* ignore malformed */ }
            };

            ws.onclose = () => {
                setIsConnected(false);
                if (mountedRef.current) {
                    reconnectTimeoutRef.current = setTimeout(() => {
                        reconnectDelayRef.current = Math.min(
                            reconnectDelayRef.current * 1.5,
                            MAX_RECONNECT_DELAY
                        );
                        connect();
                    }, reconnectDelayRef.current);
                }
            };

            ws.onerror = () => {
                ws.close();
            };

            wsRef.current = ws;
        } catch {
            setIsConnected(false);
        }
    }, []);

    useEffect(() => {
        mountedRef.current = true;
        connect();

        // Ping keepalive
        const pingInterval = setInterval(() => {
            send({ type: 'ping' });
        }, 25000);

        return () => {
            mountedRef.current = false;
            clearInterval(pingInterval);
            if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
            wsRef.current?.close();
        };
    }, [connect, send]);

    return { isConnected, subscribe, send };
}
