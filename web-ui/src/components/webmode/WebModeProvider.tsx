'use client';

import { createContext, useContext } from 'react';
import { useDeviceTier, useWebModeState } from '@/lib/webmode/state';
import type { DeviceTier, WebModeConfig } from '@/lib/webmode/types';

interface WebModeContextValue {
    deviceTier: DeviceTier;
    config: WebModeConfig;
    controlMode: 'read' | 'control';
    phase: string;
    lastSignal: string;
    updateConfig: (path: string, value: boolean | number | string) => void;
    sendSignal: (message: string) => void;
}

const WebModeContext = createContext<WebModeContextValue | null>(null);

export function WebModeProvider({ children }: { children: React.ReactNode }) {
    const deviceTier = useDeviceTier();
    const { state, config, controlMode, dispatch, updateConfig } = useWebModeState();

    const sendSignal = (message: string) => {
        dispatch({ type: 'SIGNAL', payload: message });
    };

    return (
        <WebModeContext.Provider
            value={{
                deviceTier,
                config,
                controlMode,
                phase: state.phase,
                lastSignal: state.lastSignal,
                updateConfig,
                sendSignal,
            }}
        >
            {children}
        </WebModeContext.Provider>
    );
}

export function useWebModeContext() {
    const context = useContext(WebModeContext);
    if (!context) {
        throw new Error('useWebModeContext must be used within WebModeProvider');
    }
    return context;
}
