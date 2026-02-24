type WebSocketPayload = Record<string, any> & { type: string };

type EventCallback = (payload: any) => void;

class NeuroRiftSocket {
    private ws: WebSocket | null = null;
    private callbacks = new Set<EventCallback>();
    private queue: WebSocketPayload[] = [];
    private reconnectTimer: number | null = null;
    private intentionallyClosed = false;

    connect() {
        if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
            return;
        }

        const endpoint = process.env.NEXT_PUBLIC_NEURORIFT_WS_URL ?? 'ws://127.0.0.1:8765';
        this.ws = new WebSocket(endpoint);

        this.ws.onopen = () => {
            const pending = [...this.queue];
            this.queue = [];
            pending.forEach(payload => this.send(payload));
            window.dispatchEvent(new CustomEvent('neurorift:connection', { detail: { connected: true } }));
        };

        this.ws.onmessage = event => {
            try {
                const payload = JSON.parse(event.data);
                this.callbacks.forEach(callback => callback(payload));
                window.dispatchEvent(new CustomEvent('neurorift:event', { detail: payload }));

                if (payload.type === 'chat_response') {
                    window.dispatchEvent(new CustomEvent('neurorift:chat_response', { detail: payload }));
                }
                if (payload.type === 'session_list') {
                    window.dispatchEvent(new CustomEvent('neurorift:session_list', { detail: payload }));
                }
            } catch (error) {
                console.error('Failed to parse websocket event', error);
            }
        };

        this.ws.onerror = () => {
            window.dispatchEvent(new CustomEvent('neurorift:connection', { detail: { connected: false } }));
        };

        this.ws.onclose = () => {
            window.dispatchEvent(new CustomEvent('neurorift:connection', { detail: { connected: false } }));
            this.ws = null;
            if (!this.intentionallyClosed) {
                this.reconnectTimer = window.setTimeout(() => this.connect(), 1200);
            }
        };
    }

    close() {
        this.intentionallyClosed = true;
        if (this.reconnectTimer) {
            window.clearTimeout(this.reconnectTimer);
        }
        this.ws?.close();
        this.ws = null;
    }

    send(payload: WebSocketPayload) {
        this.connect();

        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            this.queue.push(payload);
            return;
        }

        this.ws.send(JSON.stringify(payload));
    }

    subscribe(callback: EventCallback) {
        this.callbacks.add(callback);
        return () => {
            this.callbacks.delete(callback);
        };
    }
}

let instance: NeuroRiftSocket | null = null;

export function getWebSocket() {
    if (!instance) {
        instance = new NeuroRiftSocket();
        instance.connect();
    }

    return instance;
}
