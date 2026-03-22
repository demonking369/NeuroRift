import { NextResponse } from 'next/server';

export async function GET() {
    try {
        const ollamaRes = await fetch('http://127.0.0.1:11434/api/tags', {
            method: 'GET',
        });

        if (!ollamaRes.ok) {
            return NextResponse.json(
                { error: `Ollama error: ${ollamaRes.statusText}` },
                { status: ollamaRes.status }
            );
        }

        const data = await ollamaRes.json();
        
        // Return a clean list of model names
        const models = data.models.map((m: any) => ({
            name: m.name,
            size: m.size,
            details: m.details,
        }));

        return NextResponse.json({ models });

    } catch (error) {
        console.error('AI Proxy Models Error:', error);
        return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
    }
}
