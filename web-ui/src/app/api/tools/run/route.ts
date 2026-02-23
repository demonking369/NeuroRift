import { NextResponse } from 'next/server';
import { spawn } from 'child_process';
import { globalExecutions } from '../status/[id]/route';

export async function POST(request: Request) {
    try {
        const { tool, args, sessionId } = await request.json();

        if (!['nmap', 'nuclei', 'ffuf', 'subfinder', 'curl'].includes(tool)) {
            return NextResponse.json({ error: 'Tool not allowed' }, { status: 403 });
        }

        const executionId = `exec_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

        console.log(`[API] Starting tool: ${tool} ${args}`);

        const child = spawn(tool, args.split(' '), {
            shell: false,
            // cwd: sessionId ? ... : undefined
        });

        const executionEntry: any = {
            id: executionId,
            tool,
            args,
            status: 'running',
            startTime: Date.now(),
            stdout: '',
            stderr: '',
            child // Store reference to kill if needed
        };

        globalExecutions.set(executionId, executionEntry);

        child.stdout.on('data', (data) => {
            executionEntry.stdout += data.toString();
        });

        child.stderr.on('data', (data) => {
            executionEntry.stderr += data.toString();
        });

        child.on('close', (code) => {
            executionEntry.status = code === 0 ? 'completed' : 'failed';
            executionEntry.endTime = Date.now();
            executionEntry.child = undefined; // cleanup
        });

        return NextResponse.json({ executionId });
    } catch (e) {
        return NextResponse.json({ error: String(e) }, { status: 500 });
    }
}
