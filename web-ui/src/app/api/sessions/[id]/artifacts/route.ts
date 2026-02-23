
import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs/promises';
import path from 'path';
import os from 'os';
import { FileNode } from '@/lib/webmode/adapter/interface';

// Recursive function to build file tree
async function buildTree(currentPath: string): Promise<FileNode> {
    const stats = await fs.stat(currentPath);
    const name = path.basename(currentPath);

    if (stats.isDirectory()) {
        const children = await fs.readdir(currentPath);
        const childNodes = await Promise.all(
            children.map(child => buildTree(path.join(currentPath, child)))
        );
        return {
            name,
            type: 'directory',
            path: currentPath,
            children: childNodes
        };
    } else {
        return {
            name,
            type: 'file',
            path: currentPath,
            size: stats.size
        };
    }
}

export async function GET(
    request: NextRequest,
    context: { params: Promise<{ id: string }> }
) {
    const { id } = await context.params;

    // Composite ID: Target__Timestamp
    const parts = id.split('__');

    if (parts.length < 2) {
        return NextResponse.json([]);
    }

    const target = parts[0];
    const timestamp = parts[1];

    const sessionDir = path.join(os.homedir(), '.vulnforge', 'sessions', id);

    try {
        // checks if sessions exist
        await fs.access(sessionDir);

        const root = await buildTree(sessionDir);
        // Return children of the session dir, not the session dir itself as root
        return NextResponse.json(root.children || []);

    } catch (e) {
        console.error("Artifact error", e);
        return NextResponse.json([], { status: 500 });
    }
}
