import type { PanelDefinition, PanelId, PanelSlot } from '@/lib/webmode/types';

export const panelDefinitions: PanelDefinition[] = [
    {
        id: 'command',
        title: 'Command Fabric',
        description: 'Chat-first control surface with intent routing.',
        slot: 'primary',
        policy: { requiresSession: true },
        tone: 'signal',
    },
    {
        id: 'activity',
        title: 'Agent Activity Stream',
        description: 'Event-bus view of agent negotiation & critique.',
        slot: 'secondary',
        policy: { requiresSession: true },
    },
    {
        id: 'agent-graph',
        title: 'Agent State Graph',
        description: 'Live topology of agent roles, states, and trust weights.',
        slot: 'primary',
        policy: { requiresSession: true, minTier: 'tablet' },
    },
    {
        id: 'intent-flow',
        title: 'Intent → Action Flow',
        description: 'Policy-driven intent routing and gating map.',
        slot: 'primary',
        policy: { requiresSession: true },
    },
    {
        id: 'execution-timeline',
        title: 'Execution Pipeline',
        description: 'Deterministic execution path with enforcement checkpoints.',
        slot: 'secondary',
        policy: { requiresSession: true },
    },
    {
        id: 'memory-pulse',
        title: 'Memory Pulse',
        description: 'Short-term, episodic, preference, and decay indicators.',
        slot: 'tertiary',
        policy: { requiresSession: true, minTier: 'tablet' },
    },
    {
        id: 'permissions',
        title: 'Permission Decisions',
        description: 'Approval lattice for sensitive actions.',
        slot: 'tertiary',
        policy: { requiresSession: true },
        tone: 'warning',
    },
    {
        id: 'config-matrix',
        title: 'Configuration Matrix',
        description: 'Policy-driven control matrix for OpenClaw + NeuroRift.',
        slot: 'dock',
        policy: { controlOnly: false },
    },
    {
        id: 'online-mode',
        title: 'Online Mode',
        description: 'Secure tunnel exposure with explicit access control.',
        slot: 'dock',
        policy: { controlOnly: false },
    },
];

export const layoutZones: Record<PanelSlot, PanelId[]> = {
    primary: ['command', 'agent-graph', 'intent-flow'],
    secondary: ['activity', 'execution-timeline'],
    tertiary: ['memory-pulse', 'permissions'],
    dock: ['config-matrix', 'online-mode'],
};
