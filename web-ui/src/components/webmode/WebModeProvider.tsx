import { createContext, useContext, useMemo } from 'react';
import { useDeviceTier, useWebModeState } from '@/lib/webmode/state';
import type { DeviceTier, WebModeConfig } from '@/lib/webmode/types';
import { WebModeAdapter } from '@/lib/webmode/adapter/interface';
import { PrototypeAdapter } from '@/lib/webmode/adapter/prototype';
import { RealAdapter } from '@/lib/webmode/adapter/real';

interface WebModeContextValue {
    deviceTier: DeviceTier;
    config: WebModeConfig;
    controlMode: 'read' | 'control';
    phase: string;
    lastSignal: string;
    adapter: WebModeAdapter;
    adapterMode: 'REAL' | 'PROTOTYPE';
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

    const adapter = useMemo(() => {
        // Check for prototype flag or default to prototype if not specified
        const useReal = process.env.NEXT_PUBLIC_WEBMODE === 'REAL';
        console.log(`[WebMode] Initializing adapter. Mode: ${useReal ? 'REAL' : 'PROTOTYPE'}`);
        return useReal ? new RealAdapter() : new PrototypeAdapter();
    }, []);

    return (
        <WebModeContext.Provider
            value={{
                deviceTier,
                config,
                controlMode: controlMode as 'read' | 'control',
                phase: state.phase,
                lastSignal: state.lastSignal,
                adapter,
                adapterMode: adapter.mode,
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
