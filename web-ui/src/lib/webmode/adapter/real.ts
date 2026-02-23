import { WebModeAdapter, Session, ToolExecution, FileNode, SystemMetrics, SystemState } from './interface';
import { StreamEvent } from '../stream';

export class RealAdapter implements WebModeAdapter {
    mode: 'REAL' = 'REAL';
    private abortController: AbortController | null = null;

    private async fetchJson<T>(endpoint: string, options?: RequestInit): Promise<T> {
        const res = await fetch(endpoint, options);
        if (!res.ok) throw new Error(`API Error: ${res.statusText}`);
        return res.json();
    }

    async listSessions(): Promise<Session[]> {
        return this.fetchJson<Session[]>('/api/sessions');
    }

    async createSession(target: string): Promise<Session> {
        return this.fetchJson<Session>('/api/sessions', {
            method: 'POST',
            body: JSON.stringify({ target })
        });
    }

    async deleteSession(id: string): Promise<void> {
        await fetch(`/api/sessions/${id}`, { method: 'DELETE' });
    }

    async runTool(tool: string, args: string, sessionId?: string): Promise<string> {
        const res = await this.fetchJson<{ executionId: string }>('/api/tools/run', {
            method: 'POST',
            body: JSON.stringify({ tool, args, sessionId })
        });
        return res.executionId;
    }

    async getToolStatus(id: string): Promise<ToolExecution> {
        return this.fetchJson<ToolExecution>(`/api/tools/status/${id}`);
    }

    async abortTool(id: string): Promise<void> {
        await fetch(`/api/tools/status/${id}`, { method: 'DELETE' });
    }

    async listArtifacts(sessionId: string): Promise<FileNode[]> {
        return this.fetchJson<FileNode[]>(`/api/sessions/${sessionId}/artifacts`);
    }

    async readArtifact(path: string): Promise<string> {
        const res = await fetch(`/api/artifacts/content?path=${encodeURIComponent(path)}`);
        return res.text();
    }

    async getSystemMetrics(): Promise<SystemMetrics> {
        return this.fetchJson<SystemMetrics>('/api/system/metrics');
    }

    async getSystemState(): Promise<SystemState> {
        // In real mode, we'd check endpoints. For now, assume healthy if we can fetch metrics.
        try {
            await this.getSystemMetrics();
            return {
                status: 'healthy',
                ollama: { status: 'connected', model: 'llama3' }
            };
        } catch (e) {
            return {
                status: 'degraded',
                ollama: { status: 'disconnected', model: 'unknown' }
            };
        }
    }

    async *sendAIMessage(prompt: string): AsyncGenerator<string, void, unknown> {
        if (this.abortController) {
            this.abortController.abort();
        }
        this.abortController = new AbortController();

        try {
            const response = await fetch('/api/ai/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt }),
                signal: this.abortController.signal
            });

            if (!response.ok) throw new Error(`AI Error: ${response.statusText}`);
            if (!response.body) throw new Error('No response body');

            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                // Parse potentially multiple JSON objects per chunk if Ollama sends raw json stream
                // However, our proxy pipes raw bytes. Ollama sends JSON objects per line.
                // Actually, our proxy just pipes. We need to parse here if it's JSON stream, OR if it's raw text.
                // Ollama /api/generate returns a stream of JSON objects.
                // We should parse each json object and extract the 'response' field.

                const lines = chunk.split('\n').filter(line => line.trim() !== '');
                for (const line of lines) {
                    try {
                        const json = JSON.parse(line);
                        if (json.response) {
                            yield json.response;
                        }
                        if (json.done) {
                            return;
                        }
                    } catch (e) {
                        // ignore partial json
                    }
                }
            }
        } catch (error: any) {
            if (error.name === 'AbortError') return;
            throw error;
        } finally {
            this.abortController = null;
        }
    }

    cancelAI(): void {
        if (this.abortController) {
            this.abortController.abort();
            this.abortController = null;
        }
    }

    subscribeToEvents(callback: (event: StreamEvent) => void): () => void {
        const es = new EventSource('/api/stream');
        es.onmessage = (msg) => {
            const event = JSON.parse(msg.data) as StreamEvent;
            callback(event);
        };
        return () => es.close();
    }
}
