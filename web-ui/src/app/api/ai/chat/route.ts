import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
    try {
        const body = await req.json();
        const { prompt, model = 'llama3' } = body;

        // 1. Enforcement Layer Validation
        if (!prompt || typeof prompt !== 'string') {
            return NextResponse.json({ error: 'Invalid prompt' }, { status: 400 });
        }
        if (prompt.length > 4000) {
            return NextResponse.json({ error: 'Prompt exceeds maximum length' }, { status: 400 });
        }

        // 2. Proxy to Ollama
        const ollamaRes = await fetch('http://127.0.0.1:11434/api/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                model,
                prompt,
                stream: true,
            }),
        });

        if (!ollamaRes.ok) {
            return NextResponse.json(
                { error: `Ollama error: ${ollamaRes.statusText}` },
                { status: ollamaRes.status }
            );
        }

        // 3. Stream Response
        const stream = new ReadableStream({
            async start(controller) {
                const reader = ollamaRes.body?.getReader();
                if (!reader) {
                    controller.close();
                    return;
                }

                try {
                    while (true) {
                        const { done, value } = await reader.read();
                        if (done) break;
                        // Pass raw bytes through - client adapter handles parsing
                        controller.enqueue(value);
                    }
                    controller.close();
                } catch (err) {
                    controller.error(err);
                }
            },
        });

        return new NextResponse(stream, {
            headers: {
                'Content-Type': 'text/event-stream',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
            },
        });

    } catch (error) {
        console.error('AI Proxy Error:', error);
        return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
    }
}
