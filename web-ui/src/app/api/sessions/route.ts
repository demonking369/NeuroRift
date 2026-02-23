import { NextResponse } from 'next/server';
import fs from 'fs/promises';
import path from 'path';
import os from 'os';

const SESSIONS_DIR = path.join(os.homedir(), '.vulnforge', 'sessions');

export async function GET() {
    try {
        await fs.mkdir(SESSIONS_DIR, { recursive: true });
        const dirs = await fs.readdir(SESSIONS_DIR, { withFileTypes: true });

        const sessions = await Promise.all(
            dirs.filter(d => d.isDirectory()).map(async (d) => {
                const sessionPath = path.join(SESSIONS_DIR, d.name);
                const stats = await fs.stat(sessionPath);

                // Try to read metadata if exists
                let metadata = { toolCount: 0, findingsCount: 0, status: 'active' };
                try {
                    const metaPath = path.join(sessionPath, 'metadata.json');
                    const metaContent = await fs.readFile(metaPath, 'utf-8');
                    metadata = JSON.parse(metaContent);
                } catch {
                    // Ignore if no metadata
                }

                // Parse ID format: target__timestamp
                const [target, timestamp] = d.name.split('__');

                return {
                    id: d.name,
                    target: target || 'unknown',
                    timestamp: timestamp ? new Date(parseInt(timestamp)).toISOString() : stats.birthtime.toISOString(),
                    status: metadata.status,
                    toolCount: metadata.toolCount,
                    findingsCount: metadata.findingsCount
                };
            })
        );

        return NextResponse.json(sessions.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()));
    } catch (e) {
        return NextResponse.json({ error: String(e) }, { status: 500 });
    }
}

export async function POST(request: Request) {
    try {
        const { target } = await request.json();
        const timestamp = Date.now();
        const id = `${target}__${timestamp}`;
        const sessionPath = path.join(SESSIONS_DIR, id);

        await fs.mkdir(sessionPath, { recursive: true });

        // Init metadata
        const metadata = { toolCount: 0, findingsCount: 0, status: 'active', startTime: timestamp };
        await fs.writeFile(path.join(sessionPath, 'metadata.json'), JSON.stringify(metadata, null, 2));

        return NextResponse.json({
            id,
            target,
            timestamp: new Date(timestamp).toISOString(),
            status: 'active',
            toolCount: 0,
            findingsCount: 0
        });
    } catch (e) {
        return NextResponse.json({ error: String(e) }, { status: 500 });
    }
}
