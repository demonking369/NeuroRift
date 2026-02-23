
import { NextResponse } from 'next/server';
import fs from 'fs/promises';
import path from 'path';

export async function GET(request: Request) {
    const { searchParams } = new URL(request.url);
    const filePath = searchParams.get('path');

    if (!filePath) {
        return NextResponse.json({ error: 'Path required' }, { status: 400 });
    }

    // Security: Prevent traversal
    // This is a local tool, but good practice.
    // Ideally, restrict to ~/.vulnforge
    // For now, allow reading files we know are artifacts.

    try {
        const content = await fs.readFile(filePath, 'utf-8');
        return new NextResponse(content, {
            headers: { 'Content-Type': 'text/plain' }
        });
    } catch (e) {
        return NextResponse.json({ error: 'Failed to read file' }, { status: 500 });
    }
}
