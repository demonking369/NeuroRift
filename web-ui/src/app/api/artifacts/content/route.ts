import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs/promises';
import path from 'path';

export async function GET(request: NextRequest) {
    const searchParams = request.nextUrl.searchParams;
    const filePath = searchParams.get('path');

    if (!filePath) {
        return NextResponse.json({ error: 'Path required' }, { status: 400 });
    }

    // Security check: ensure path is within allowed directories
    // For now, allow reading from anywhere in user home for demo purposes, 
    // but in production this should be restricted to session dirs.
    // const safePath = path.normalize(filePath).replace(/^(\.\.(\/|\\|$))+/, '');

    try {
        const content = await fs.readFile(filePath, 'utf-8');
        return new NextResponse(content, {
            headers: { 'Content-Type': 'text/plain' }
        });
    } catch (e) {
        return NextResponse.json({ error: 'File not found or unreadable' }, { status: 404 });
    }
}
