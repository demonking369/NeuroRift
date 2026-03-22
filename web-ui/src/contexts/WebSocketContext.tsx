'use client';

import React, { createContext, useContext } from 'react';
import { useWebSocket } from '@/hooks/useWebSocket';

type WSContextValue = ReturnType<typeof useWebSocket>;

const WebSocketContext = createContext<WSContextValue>({
    isConnected: false,
    subscribe: () => () => {},
    send: () => {},
});

export function WebSocketProvider({ children }: { children: React.ReactNode }) {
    const ws = useWebSocket();
    return (
        <WebSocketContext.Provider value={ws}>
            {children}
        </WebSocketContext.Provider>
    );
}

export function useWS() {
    return useContext(WebSocketContext);
}
