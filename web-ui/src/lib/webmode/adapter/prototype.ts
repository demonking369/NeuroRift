import { WebModeAdapter, Session, ToolExecution, FileNode, SystemMetrics, SystemState } from './interface';
import { StreamEvent } from '../stream';

// Mock Data
const MOCK_SESSIONS: Session[] = [
    { id: 'sess_001', target: 'megacorp.com', timestamp: '2023-10-27T10:00:00Z', status: 'completed', toolCount: 12, findingsCount: 8 },
    { id: 'sess_002', target: '192.168.1.0/24', timestamp: '2023-10-28T14:30:00Z', status: 'active', toolCount: 3, findingsCount: 1 },
];

const MOCK_ARTIFACTS: FileNode[] = [
    {
        name: 'scans',
        type: 'directory',
        path: '/scans',
        children: [
            { name: 'nmap_initial.xml', type: 'file', path: '/scans/nmap_initial.xml', size: 1024 },
            { name: 'nuclei_results.json', type: 'file', path: '/scans/nuclei_results.json', size: 2048 },
        ]
    },
    {
        name: 'report.md',
        type: 'file',
        path: '/report.md',
        size: 512
    }
];

export class PrototypeAdapter implements WebModeAdapter {
    mode: 'PROTOTYPE' = 'PROTOTYPE';
    private executions: Map<string, ToolExecution> = new Map();

    async listSessions(): Promise<Session[]> {
        return Promise.resolve(MOCK_SESSIONS);
    }

    async createSession(target: string): Promise<Session> {
        const newSession: Session = {
            id: `sess_${Date.now()}`,
            target,
            timestamp: new Date().toISOString(),
            status: 'active',
            toolCount: 0,
            findingsCount: 0
        };
        MOCK_SESSIONS.unshift(newSession);
        return newSession;
    }

    async deleteSession(id: string): Promise<void> {
        const index = MOCK_SESSIONS.findIndex(s => s.id === id);
        if (index > -1) MOCK_SESSIONS.splice(index, 1);
    }

    async runTool(tool: string, args: string): Promise<string> {
        const id = `exec_${Date.now()}`;
        const execution: ToolExecution = {
            id,
            tool,
            args,
            status: 'running',
            startTime: Date.now(),
            stdout: `[${tool}] Starting simulated execution...\nTarget: ${args}\n`,
            stderr: ''
        };
        this.executions.set(id, execution);

        // Simulate progress
        setTimeout(() => {
            const exec = this.executions.get(id);
            if (exec) {
                exec.stdout += `[${tool}] Finding open ports...\n[${tool}] Discovered: 80, 443, 8080\n`;
                // Force update if needed, but in React we poll
            }
        }, 1000);

        setTimeout(() => {
            const exec = this.executions.get(id);
            if (exec) {
                exec.stdout += `[${tool}] Analysis complete.\n`;
                exec.status = 'completed';
                exec.endTime = Date.now();
            }
        }, 3000);

        return id;
    }

    async getToolStatus(id: string): Promise<ToolExecution> {
        const exec = this.executions.get(id);
        if (!exec) throw new Error('Execution not found');
        return exec;
    }

    async abortTool(id: string): Promise<void> {
        const exec = this.executions.get(id);
        if (exec && exec.status === 'running') {
            exec.status = 'failed';
            exec.stderr += '\n[Adapter] Execution aborted by operator.';
            exec.endTime = Date.now();
        }
    }

    async listArtifacts(sessionId: string): Promise<FileNode[]> {
        return MOCK_ARTIFACTS;
    }

    async readArtifact(path: string): Promise<string> {
        if (path.endsWith('.json')) return JSON.stringify({ mock: 'data', findings: [] }, null, 2);
        if (path.endsWith('.md')) return '# Mock Report\n\nThis is a simulated artifact content.';
        return 'Binary or unknown file content simulated.';
    }

    async getSystemMetrics(): Promise<SystemMetrics> {
        return {
            cpu: 10 + Math.random() * 20,
            memory: 40 + Math.random() * 10,
            network: { rx: Math.random() * 1000, tx: Math.random() * 500 }
        };
    }

    async getSystemState(): Promise<SystemState> {
        return {
            status: 'healthy',
            ollama: { status: 'connected', model: 'simulated-llama3' }
        };
    }

    private isAICancelled = false;

    async *sendAIMessage(prompt: string): AsyncGenerator<string, void, unknown> {
        this.isAICancelled = false;

        // Simulating "thinking" delay
        await new Promise(resolve => setTimeout(resolve, 600));

        const response = `[PROTOTYPE] Analysis of: "${prompt}"\n\nI have analyzed the request and determined that this is a simulated environment. \n\n1. Token streaming is emulated.\n2. No actual LLM is running.\n3. Latency is artificial.\n\nProceeding with simulated execution directives...`;

        const tokens = response.split(/(\s+)/); // Split by whitespace to simulate word streaming

        for (const token of tokens) {
            if (this.isAICancelled) break;
            yield token;
            // Variable typing speed
            await new Promise(resolve => setTimeout(resolve, 20 + Math.random() * 50));
        }
    }

    cancelAI(): void {
        this.isAICancelled = true;
    }

    subscribeToEvents(callback: (event: StreamEvent) => void): () => void {
        const interval = setInterval(() => {
            if (Math.random() > 0.7) {
                callback({
                    id: `evt-${Date.now()}`,
                    label: 'Simulated Event: Prototype Adapter Signal',
                    time: new Date().toLocaleTimeString(),
                    tone: Math.random() > 0.9 ? 'warning' : 'neutral'
                });
            }
        }, 2000);
        return () => clearInterval(interval);
    }
}
