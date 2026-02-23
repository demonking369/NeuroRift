import { StreamEvent } from '../stream';

export interface Session {
    id: string;
    target: string;
    timestamp: string;
    status: 'active' | 'completed' | 'archived';
    toolCount: number;
    findingsCount: number;
}

export interface ToolExecution {
    id: string;
    tool: string;
    args: string;
    status: 'running' | 'completed' | 'failed';
    startTime: number;
    endTime?: number;
    stdout: string;
    stderr: string;
}

export interface Artifact {
    id: string;
    name: string;
    type: 'json' | 'md' | 'html' | 'text' | 'image';
    path: string;
    size: number;
    content?: string; // Loaded on demand
}

export interface FileNode {
    name: string;
    type: 'file' | 'directory';
    path: string;
    children?: FileNode[];
    size?: number;
}

export interface SystemMetrics {
    cpu: number;
    memory: number;
    network: { rx: number; tx: number };
}

export interface WebModeAdapter {
    // Mode Identity
    mode: 'REAL' | 'PROTOTYPE';

    // Session Management
    listSessions(): Promise<Session[]>;
    createSession(target: string): Promise<Session>;
    deleteSession(id: string): Promise<void>;

    // Tool Execution
    runTool(tool: string, args: string, sessionId?: string): Promise<string>; // returns execution ID
    getToolStatus(executionId: string): Promise<ToolExecution>;
    abortTool(executionId: string): Promise<void>;

    // Artifacts & Files
    listArtifacts(sessionId: string): Promise<FileNode[]>;
    readArtifact(path: string): Promise<string>;

    // System State
    getSystemMetrics(): Promise<SystemMetrics>;

    // Event Streaming
    subscribeToEvents(callback: (event: StreamEvent) => void): () => void;

    // AI Control
    sendAIMessage(prompt: string): AsyncGenerator<string, void, unknown>;
    cancelAI(): void;

    // System Control
    getSystemState(): Promise<SystemState>;
}

export interface SystemState {
    status: 'healthy' | 'degraded' | 'critical';
    ollama: {
        status: 'connected' | 'disconnected';
        model: string;
    };
}
