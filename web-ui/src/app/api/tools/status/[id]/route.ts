
import { NextRequest, NextResponse } from 'next/server';

export const globalExecutions = (global as any)._nr_executions || new Map();
(global as any)._nr_executions = globalExecutions;

export async function GET(
    request: NextRequest,
    context: { params: Promise<{ id: string }> }
) {
    const { id } = await context.params;
    const exec = globalExecutions.get(id);

    if (!exec) {
        return NextResponse.json({ error: 'Execution not found' }, { status: 404 });
    }

    // Return status and latest logs
    // (In a real app, optimize log slicing)
    return NextResponse.json({
        id: exec.id,
        tool: exec.tool,
        status: exec.status,
        startTime: exec.startTime,
        duration: exec.status === 'completed' ? (Date.now() - exec.startTime) : undefined,
        stdout: exec.stdout,
        stderr: exec.stderr
    });
}
