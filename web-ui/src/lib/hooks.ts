'use client';

import { useEffect, useMemo, useState } from 'react';
import type { AgentStatus, ApprovalState, SessionState, SystemHealth, TaskState } from '@/lib/types';

const initialSession: SessionState = {
    id: 'session-aurora',
    name: 'Aurora Lattice Sweep',
    mode: 'DEFENSIVE',
    status: 'active',
    updated_at: new Date().toISOString(),
    findings: [
        {
            id: 'finding-1',
            title: 'Token relay exposed in staging mesh',
            description: 'Relay endpoint responding without mutual authentication across agent segments.',
            severity: 'HIGH',
            tool_source: 'NeuroRift Sentinel',
            discovered_at: new Date(Date.now() - 1000 * 60 * 42).toISOString(),
        },
        {
            id: 'finding-2',
            title: 'Over-privileged task executor',
            description: 'Execution sandbox profile still includes deprecated system hooks.',
            severity: 'MEDIUM',
            tool_source: 'Policy Lens',
            discovered_at: new Date(Date.now() - 1000 * 60 * 18).toISOString(),
        }
    ],
    artifacts: [
        { id: 'artifact-1', label: 'Trace Bundle v3' },
        { id: 'artifact-2', label: 'Policy Snapshot' }
    ],
    metadata: {
        description: 'Long-running defensive calibration with OpenClaw orchestration.'
    }
};

const initialAgents: Record<string, AgentStatus> = {
    Planner: {
        state: 'planning',
        current_task: 'Synthesizing multi-agent scan lattice',
        last_update: new Date().toISOString(),
        queue_depth: 3,
        dependencies: ['Analyst'],
        signal_strength: 0.8,
        sentiment: 'neutral'
    },
    Operator: {
        state: 'executing',
        current_task: 'Executing containment probes',
        last_update: new Date().toISOString(),
        queue_depth: 1,
        dependencies: ['Planner'],
        signal_strength: 0.9,
        sentiment: 'cooperative'
    },
    Navigator: {
        state: 'idle',
        current_task: null,
        last_update: new Date().toISOString(),
        queue_depth: 0,
        signal_strength: 0.1,
        sentiment: 'neutral'
    },
    Analyst: {
        state: 'planning',
        current_task: 'Correlating memory decay signals',
        last_update: new Date().toISOString(),
        queue_depth: 2,
        dependencies: [],
        signal_strength: 0.6,
        sentiment: 'neutral'
    },
    Scribe: {
        state: 'idle',
        current_task: null,
        last_update: new Date().toISOString(),
        queue_depth: 0,
        signal_strength: 0.05,
        sentiment: 'neutral'
    },
};

const initialTasks: TaskState[] = [
    { id: 'task-1', label: 'Intent synthesis for scan batch', status: 'running', progress: 64 },
    { id: 'task-2', label: 'Policy diff + enforcement evaluation', status: 'queued', progress: 12 },
    { id: 'task-3', label: 'Memory reinforcement alignment', status: 'blocked', progress: 27 },
];

const initialApprovals: ApprovalState[] = [
    { id: 'approval-1', label: 'Escalate scan depth to 0.82', status: 'pending', risk: 'high' },
    { id: 'approval-2', label: 'Enable external tunnel for observers', status: 'pending', risk: 'medium' },
];

export function useNeuroRift() {
    const [session, setSession] = useState<SessionState | null>(initialSession);
    const [agents, setAgents] = useState<Record<string, AgentStatus>>(initialAgents);
    const [tasks, setTasks] = useState<TaskState[]>(initialTasks);
    const [approvals, setApprovals] = useState<ApprovalState[]>(initialApprovals);
    const [torConnected, setTorConnected] = useState(true);
    const [systemHealth, setSystemHealth] = useState<SystemHealth>({
        cpu: 41,
        memory: 63,
        latency: 120,
        memory_metrics: {
            usage: 0.45,
            reinforcement: 0.2,
            decay: 0.1,
            type: 'episodic'
        }
    });
    const [browserActive, setBrowserActive] = useState(false);

    useEffect(() => {
        const interval = window.setInterval(() => {
            setSystemHealth(prev => ({
                cpu: Math.min(95, Math.max(12, prev.cpu + (Math.random() * 8 - 4))),
                memory: Math.min(92, Math.max(18, prev.memory + (Math.random() * 6 - 3))),
                latency: Math.min(420, Math.max(40, prev.latency + (Math.random() * 20 - 10))),
                memory_metrics: {
                    ...prev.memory_metrics,
                    // Simulate subtle organic decay and reinforcement pulses
                    usage: Math.min(1, Math.max(0.2, prev.memory_metrics.usage + (Math.random() * 0.05 - 0.02))),
                    reinforcement: Math.min(1, Math.max(0, prev.memory_metrics.reinforcement + (Math.random() * 0.1 - 0.04))),
                }
            }));

            setAgents(prev => {
                const updated = { ...prev };
                Object.keys(updated).forEach(key => {
                    const agent = updated[key];
                    // Simulate dynamic signaling and dependency shifts
                    const isActive = agent.state === 'executing' || agent.state === 'planning';

                    updated[key] = {
                        ...agent,
                        last_update: new Date().toISOString(),
                        signal_strength: isActive ? Math.random() * 0.5 + 0.5 : Math.random() * 0.2, // Pulse if active
                        dependencies: isActive && Math.random() > 0.7
                            ? ['Planner', 'Operator'].filter(d => d !== key) // Randomly depend on others
                            : []
                    };
                });
                return updated;
            });

            setTasks(prev =>
                prev.map(task =>
                    task.status === 'running'
                        ? { ...task, progress: Math.min(100, task.progress + Math.random() * 6) }
                        : task
                )
            );
        }, 2000); // Faster update cycle for "liveness"

        return () => window.clearInterval(interval);
    }, []);

    useEffect(() => {
        const handleSessionLoad = (event: CustomEvent) => {
            if (event.detail.type === 'load_session') {
                setSession(event.detail.session || initialSession);
            }
        };

        window.addEventListener('neurorift:session_load', handleSessionLoad as EventListener);
        return () => window.removeEventListener('neurorift:session_load', handleSessionLoad as EventListener);
    }, []);

    useEffect(() => {
        const timeout = window.setTimeout(() => setBrowserActive(true), 1500);
        return () => window.clearTimeout(timeout);
    }, []);

    const metrics = useMemo(() => ({
        activeTasks: tasks.filter(task => task.status === 'running').length,
        pendingApprovals: approvals.filter(approval => approval.status === 'pending').length,
    }), [tasks, approvals]);

    return {
        session,
        agents,
        tasks,
        approvals,
        torConnected,
        systemHealth,
        browserActive,
        metrics,
        setTorConnected,
    };
}
