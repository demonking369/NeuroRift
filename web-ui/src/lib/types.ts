export type OperationalMode = 'OFFENSIVE' | 'DEFENSIVE' | 'STEALTH';

export type AgentType =
    | 'Planner'
    | 'Operator'
    | 'Navigator'
    | 'Analyst'
    | 'Scribe'
    | 'Observer'
    | 'Critic'
    | 'Meta';

export interface AgentStatus {
    agent?: AgentType;
    state: 'idle' | 'planning' | 'executing' | 'error' | 'awaiting_approval';
    current_task?: string | null;
    last_update: string;
    queue_depth?: number;
    // New fields for Graph Visualization
    dependencies?: string[]; // Names of agents this agent is waiting on
    signal_strength?: number; // 0-1, visual pulse intensity
    sentiment?: 'neutral' | 'cooperative' | 'adversarial'; // Color coding
}

export interface MemoryMetrics {
    usage: number; // 0-1
    reinforcement: number; // 0-1, episodic strength
    decay: number; // 0-1, preference stability
    type: 'episodic' | 'preference';
}

export interface PolicyDelta {
    resource: string;
    change: 'allow' | 'deny' | 'modify';
    reason: string;
}

export interface ApprovalState {
    id: string;
    label: string;
    status: 'pending' | 'approved' | 'rejected' | 'analyzing';
    risk: 'low' | 'medium' | 'high' | 'critical';
    risk_score?: number; // 0-100
    policy_deltas?: PolicyDelta[]; // What changes if approved
    deadline?: string; // ISO date for auto-rejection
}

export interface IntentState {
    id: string;
    raw_input: string;
    status: 'drafting' | 'negotiating' | 'ready' | 'executed';
    confidence_score: number; // 0-1
    projected_risk: 'low' | 'medium' | 'high';
}

export interface SystemHealth {
    cpu: number;
    memory: number;
    latency: number;
    memory_metrics: MemoryMetrics; // Enhanced memory tracking
}

export interface TaskState {
    id: string;
    label: string;
    status: 'running' | 'queued' | 'blocked' | 'complete' | 'failed' | 'canceled';
    progress: number;
}

export interface Finding {
    id: string;
    title: string;
    description: string;
    severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
    tool_source: string;
    discovered_at: string;
}

export interface Artifact {
    id: string;
    label: string;
}

export interface SessionState {
    id: string;
    name: string;
    mode: OperationalMode;
    status: 'active' | 'archived' | 'paused';
    updated_at: string;
    findings: Finding[];
    artifacts: Artifact[];
    metadata: {
        description?: string;
    };
}
