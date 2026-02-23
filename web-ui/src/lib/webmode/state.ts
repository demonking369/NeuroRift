'use client';

import { useEffect, useMemo, useReducer, useState } from 'react';
import type { DeviceTier, WebModeConfig } from '@/lib/webmode/types';

interface WebModeState {
    phase: 'dormant' | 'syncing' | 'command' | 'adaptive';
    mode: 'observe' | 'command';
    lastSignal: string;
}

type WebModeAction =
    | { type: 'SYNC' }
    | { type: 'ARM' }
    | { type: 'OBSERVE' }
    | { type: 'SIGNAL'; payload: string };

const initialState: WebModeState = {
    phase: 'dormant',
    mode: 'observe',
    lastSignal: 'Awaiting intent stream...'
};

function reducer(state: WebModeState, action: WebModeAction): WebModeState {
    switch (action.type) {
        case 'SYNC':
            return { ...state, phase: 'syncing', lastSignal: 'Synchronizing buses...' };
        case 'ARM':
            return { ...state, phase: 'command', mode: 'command', lastSignal: 'Command lattice armed.' };
        case 'OBSERVE':
            return { ...state, phase: 'adaptive', mode: 'observe', lastSignal: 'Adaptive observation enabled.' };
        case 'SIGNAL':
            return { ...state, lastSignal: action.payload };
        default:
            return state;
    }
}

const defaultConfig: WebModeConfig = {
    aiBehavior: {
        intentSynthesis: true,
        proposalCritique: true,
        selfEvolution: false,
        negotiationDepth: 0.68,
    },
    agentModes: {
        autonomy: 'collaborative',
        supervision: 'balanced',
    },
    stealth: {
        enabled: false,
        level: 0.4,
        scanDepth: 0.72,
    },
    memory: {
        usage: 0.68,
        decay: 0.22,
        reinforcement: 0.74,
    },
    contributions: {
        mode: 'proposal-only',
        allowTelemetry: false,
    },
    openclaw: {
        horizon: 12,
        learningRate: 0.42,
    },
    neurorift: {
        rateLimit: 240,
        sandboxLevel: 'hardened',
    },
    onlineMode: {
        enabled: false,
        access: 'read',
    },
};

export function useDeviceTier(): DeviceTier {
    const [tier, setTier] = useState<DeviceTier>('desktop');

    useEffect(() => {
        const updateTier = () => {
            const width = window.innerWidth;
            if (width < 720) {
                setTier('mobile');
            } else if (width < 1100) {
                setTier('tablet');
            } else if (width < 1600) {
                setTier('desktop');
            } else {
                setTier('wide');
            }
        };

        updateTier();
        window.addEventListener('resize', updateTier);
        return () => window.removeEventListener('resize', updateTier);
    }, []);

    return tier;
}

export function useWebModeState() {
    const [state, dispatch] = useReducer(reducer, initialState);
    const [config, setConfig] = useState<WebModeConfig>(defaultConfig);

    useEffect(() => {
        const timer = window.setTimeout(() => dispatch({ type: 'SYNC' }), 400);
        const armTimer = window.setTimeout(() => dispatch({ type: 'ARM' }), 1600);
        return () => {
            window.clearTimeout(timer);
            window.clearTimeout(armTimer);
        };
    }, []);

    const updateConfig = (path: string, value: boolean | number | string) => {
        setConfig(prev => {
            const next = structuredClone(prev);
            const segments = path.split('.');
            let cursor: any = next;
            segments.slice(0, -1).forEach(segment => {
                cursor[segment] = cursor[segment] ?? {};
                cursor = cursor[segment];
            });
            cursor[segments[segments.length - 1]] = value;
            return next;
        });
    };

    const controlMode = useMemo(() => (config.onlineMode.access === 'control' ? 'control' : 'read'), [config.onlineMode.access]);

    return {
        state,
        config,
        controlMode,
        dispatch,
        updateConfig,
    };
}
