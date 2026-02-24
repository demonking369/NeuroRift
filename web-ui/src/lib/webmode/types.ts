export type DeviceTier = 'mobile' | 'tablet' | 'desktop' | 'wide';

export type PanelId =
    | 'command'
    | 'activity'
    | 'agent-graph'
    | 'intent-flow'
    | 'execution-timeline'
    | 'memory-pulse'
    | 'config-matrix'
    | 'online-mode'
    | 'permissions';

export type PanelSlot = 'primary' | 'secondary' | 'tertiary' | 'dock';

export interface PanelDefinition {
    id: PanelId;
    title: string;
    description: string;
    slot: PanelSlot;
    policy: PanelPolicy;
    tone?: 'signal' | 'neutral' | 'warning';
}

export interface PanelPolicy {
    controlOnly?: boolean;
    minTier?: DeviceTier;
    requiresSession?: boolean;
}

export interface PolicyContext {
    deviceTier: DeviceTier;
    controlMode: 'read' | 'control';
    sessionActive: boolean;
}

export interface WebModeConfig {
    aiBehavior: {
        intentSynthesis: boolean;
        proposalCritique: boolean;
        selfEvolution: boolean;
        negotiationDepth: number;
    };
    agentModes: {
        autonomy: 'guided' | 'collaborative' | 'autonomous';
        supervision: 'strict' | 'balanced' | 'permissive';
    };
    stealth: {
        enabled: boolean;
        level: number;
        scanDepth: number;
    };
    memory: {
        usage: number;
        decay: number;
        reinforcement: number;
    };
    contributions: {
        mode: 'proposal-only' | 'fork-required';
        allowTelemetry: boolean;
    };
    openclaw: {
        horizon: number;
        learningRate: number;
    };
    neurorift: {
        rateLimit: number;
        sandboxLevel: 'strict' | 'hardened' | 'sealed';
    };
    onlineMode: {
        enabled: boolean;
        access: 'read' | 'control';
    };
}
