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
    state: 'idle' | 'planning' | 'executing' | 'error';
    current_task?: string | null;
    last_update: string;
    queue_depth?: number;
}

export interface Finding {
    id: string;
    title: string;
    description: string;
    severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';
    tool_source: string;
    discovered_at: string;
}

export interface SessionState {
    id: string;
    name: string;
    mode: OperationalMode;
    status: 'active' | 'paused' | 'archived';
    updated_at: string;
    findings: Finding[];
    artifacts: Array<{ id: string; label: string }>
    metadata: {
        description?: string;
    };
}

export interface TaskState {
    id: string;
    label: string;
    status: 'queued' | 'running' | 'blocked' | 'complete';
    progress: number;
}

export interface ApprovalState {
    id: string;
    label: string;
    status: 'pending' | 'approved' | 'rejected';
    risk: 'low' | 'medium' | 'high';
}

export interface SystemHealth {
    cpu: number;
    memory: number;
    latency: number;
}
