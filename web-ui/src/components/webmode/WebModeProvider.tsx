import { createContext, useContext, useMemo, useState, useEffect } from 'react';
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
    availableModels: Array<{ label: string; value: string }>;
    updateConfig: (path: string, value: boolean | number | string) => void;
    sendSignal: (message: string) => void;
}

const WebModeContext = createContext<WebModeContextValue | null>(null);

export function WebModeProvider({ children }: { children: React.ReactNode }) {
    const deviceTier = useDeviceTier();
    const { state, config, controlMode, dispatch, updateConfig } = useWebModeState();
    const [availableModels, setAvailableModels] = useState<Array<{ label: string; value: string }>>([
        { label: 'Qwen 2.5 Coder (3b)', value: 'qwen2.5-coder:3b' }
    ]);

    useEffect(() => {
        // Fetch models from Ollama through our new API route
        fetch('/api/ai/models')
            .then(res => res.json())
            .then(data => {
                if (data.models && data.models.length > 0) {
                    setAvailableModels(
                        data.models.map((m: any) => ({
                            label: `${m.name} (${(m.size / 1024 / 1024 / 1024).toFixed(1)}GB)`,
                            value: m.name
                        }))
                    );
                }
            })
            .catch(err => console.error('Failed to fetch models:', err));
    }, []);

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
                availableModels,
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
