import type { WebModeConfig } from '@/lib/webmode/types';

export interface ConfigField {
    path: keyof WebModeConfig | string;
    label: string;
    description: string;
    type: 'toggle' | 'slider' | 'select';
    min?: number;
    max?: number;
    step?: number;
    options?: Array<{ label: string; value: string }>;
}

export interface ConfigSection {
    id: string;
    title: string;
    description: string;
    fields: ConfigField[];
}

export const configSchema: ConfigSection[] = [
    {
        id: 'ai-behavior',
        title: 'AI Behavior',
        description: 'Intent synthesis, critique loops, and autonomous negotiation depth.',
        fields: [
            {
                path: 'aiBehavior.intentSynthesis',
                label: 'Intent synthesis',
                description: 'Generate structured intents from free-form input.',
                type: 'toggle',
            },
            {
                path: 'aiBehavior.proposalCritique',
                label: 'Proposal critique',
                description: 'Multi-agent scoring of plan proposals.',
                type: 'toggle',
            },
            {
                path: 'aiBehavior.selfEvolution',
                label: 'Self-evolution proposals',
                description: 'Allow proposal-based evolution of agent behaviors.',
                type: 'toggle',
            },
            {
                path: 'aiBehavior.negotiationDepth',
                label: 'Negotiation depth',
                description: 'Depth of agent negotiation cycles.',
                type: 'slider',
                min: 0.2,
                max: 1,
                step: 0.02,
            },
        ],
    },
    {
        id: 'agent-modes',
        title: 'Agent Modes',
        description: 'Autonomy tiering and supervision intensity.',
        fields: [
            {
                path: 'agentModes.autonomy',
                label: 'Autonomy',
                description: 'Baseline autonomy for the agent mesh.',
                type: 'select',
                options: [
                    { label: 'Guided', value: 'guided' },
                    { label: 'Collaborative', value: 'collaborative' },
                    { label: 'Autonomous', value: 'autonomous' },
                ],
            },
            {
                path: 'agentModes.supervision',
                label: 'Supervision',
                description: 'Oversight strictness for agent actions.',
                type: 'select',
                options: [
                    { label: 'Strict', value: 'strict' },
                    { label: 'Balanced', value: 'balanced' },
                    { label: 'Permissive', value: 'permissive' },
                ],
            },
        ],
    },
    {
        id: 'stealth',
        title: 'Stealth + Scan Depth',
        description: 'Control scan depth and stealth posture.',
        fields: [
            {
                path: 'stealth.enabled',
                label: 'Stealth mode',
                description: 'Mask execution signatures where possible.',
                type: 'toggle',
            },
            {
                path: 'stealth.level',
                label: 'Stealth level',
                description: 'Intensity of stealth controls.',
                type: 'slider',
                min: 0,
                max: 1,
                step: 0.05,
            },
            {
                path: 'stealth.scanDepth',
                label: 'Scan depth',
                description: 'Maximum probe depth for agents.',
                type: 'slider',
                min: 0.2,
                max: 1,
                step: 0.05,
            },
        ],
    },
    {
        id: 'memory',
        title: 'Memory Plane',
        description: 'Control local memory usage, decay, and reinforcement.',
        fields: [
            {
                path: 'memory.usage',
                label: 'Memory usage',
                description: 'Percent of local memory budget in use.',
                type: 'slider',
                min: 0,
                max: 1,
                step: 0.02,
            },
            {
                path: 'memory.decay',
                label: 'Decay rate',
                description: 'How quickly transient memory fades.',
                type: 'slider',
                min: 0,
                max: 1,
                step: 0.02,
            },
            {
                path: 'memory.reinforcement',
                label: 'Reinforcement',
                description: 'Memory reinforcement intensity.',
                type: 'slider',
                min: 0,
                max: 1,
                step: 0.02,
            },
        ],
    },
    {
        id: 'contribution',
        title: 'Contribution Mode',
        description: 'Controls for external contributions and telemetry.',
        fields: [
            {
                path: 'contributions.mode',
                label: 'Contribution mode',
                description: 'All code evolution is proposal-only.',
                type: 'select',
                options: [
                    { label: 'Proposal-only', value: 'proposal-only' },
                    { label: 'Fork-required', value: 'fork-required' },
                ],
            },
            {
                path: 'contributions.allowTelemetry',
                label: 'Telemetry',
                description: 'Allow telemetry to inform evolution.',
                type: 'toggle',
            },
        ],
    },
    {
        id: 'openclaw',
        title: 'OpenClaw Core',
        description: 'Planning horizon and learning cadence.',
        fields: [
            {
                path: 'openclaw.horizon',
                label: 'Planning horizon',
                description: 'Number of steps for autonomous planning.',
                type: 'slider',
                min: 4,
                max: 24,
                step: 1,
            },
            {
                path: 'openclaw.learningRate',
                label: 'Learning rate',
                description: 'Rate of plan adaptation.',
                type: 'slider',
                min: 0.1,
                max: 1,
                step: 0.05,
            },
        ],
    },
    {
        id: 'neurorift',
        title: 'NeuroRift Execution',
        description: 'Deterministic execution constraints and sandboxes.',
        fields: [
            {
                path: 'neurorift.rateLimit',
                label: 'Rate limit',
                description: 'Max tool invocations per minute.',
                type: 'slider',
                min: 60,
                max: 600,
                step: 20,
            },
            {
                path: 'neurorift.sandboxLevel',
                label: 'Sandbox level',
                description: 'Isolation level for execution plane.',
                type: 'select',
                options: [
                    { label: 'Strict', value: 'strict' },
                    { label: 'Hardened', value: 'hardened' },
                    { label: 'Sealed', value: 'sealed' },
                ],
            },
        ],
    },
];
