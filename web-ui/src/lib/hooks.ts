'use client';

import { useEffect, useMemo, useState } from 'react';
import { getWebSocket } from '@/lib/websocket';
import type { AgentStatus, ApprovalState, SessionState, SystemHealth, TaskState } from '@/lib/types';

function normalizeMode(mode?: string) {
    if (mode?.toUpperCase() === 'DEFENSIVE') return 'DEFENSIVE';
    return 'OFFENSIVE';
}

function normalizeSession(raw: any): SessionState {
    const state = raw?.state ?? raw;
    const findings = Array.isArray(state?.findings) ? state.findings : [];
    const artifacts = Array.isArray(state?.artifacts) ? state.artifacts : [];

    return {
        id: state?.id ?? raw?.id ?? `session-${Date.now()}`,
        name: state?.name ?? raw?.name ?? 'Session',
        mode: normalizeMode(state?.mode) as SessionState['mode'],
        status: String(state?.status ?? raw?.status ?? 'active').toLowerCase() as SessionState['status'],
        updated_at: state?.updated_at ?? raw?.updated_at ?? new Date().toISOString(),
        findings: findings.map((finding: any) => ({
            id: finding.id,
            title: finding.title,
            description: finding.description,
            severity: String(finding.severity).toUpperCase(),
            tool_source: finding.tool_source,
            discovered_at: finding.discovered_at,
        })),
        artifacts: artifacts.map((artifact: any) => ({
            id: artifact.id,
            label: artifact.name || artifact.label || artifact.path,
        })),
        metadata: state?.metadata ?? raw?.metadata ?? {},
    };
}

export function useNeuroRift() {
    const [session, setSession] = useState<SessionState | null>(null);
    const [agents, setAgents] = useState<Record<string, AgentStatus>>({});
    const [tasks, setTasks] = useState<TaskState[]>([]);
    const [approvals, setApprovals] = useState<ApprovalState[]>([]);
    const [torConnected, setTorConnected] = useState(false);
    const [systemHealth, setSystemHealth] = useState<SystemHealth>({ cpu: 0, memory: 0, latency: 0 });
    const [browserActive, setBrowserActive] = useState(false);

    useEffect(() => {
        const ws = getWebSocket();
        ws.send({ type: 'get_session_list' });

        const unsubscribe = ws.subscribe((event: any) => {
            switch (event.type) {
                case 'session_loaded':
                    setSession(normalizeSession(event.state));
                    break;
                case 'session_created':
                    setSession(prev => prev ? prev : {
                        id: event.session_id,
                        name: event.name,
                        mode: 'OFFENSIVE',
                        status: 'active',
                        updated_at: new Date().toISOString(),
                        findings: [],
                        artifacts: [],
                        metadata: {},
                    });
                    ws.send({ type: 'load_session', session_id: event.session_id });
                    break;
                case 'task_queued':
                    setTasks(prev => [{ id: event.task.id, label: `${event.task.tool_name} → ${event.task.target}`, status: 'queued', progress: 0 }, ...prev]);
                    break;
                case 'task_started':
                    setTasks(prev => prev.map(task => task.id === event.task_id ? { ...task, status: 'running', progress: Math.max(task.progress, 5) } : task));
                    break;
                case 'task_output':
                    window.dispatchEvent(new CustomEvent('neurorift:task_output', { detail: event }));
                    setTasks(prev => prev.map(task => task.id === event.task_id ? { ...task, progress: Math.min(95, task.progress + 10) } : task));
                    break;
                case 'task_completed':
                    setTasks(prev => prev.map(task => task.id === event.task_id ? { ...task, status: 'complete', progress: 100 } : task));
                    break;
                case 'task_failed':
                case 'task_cancelled':
                    setTasks(prev => prev.map(task => task.id === event.task_id ? { ...task, status: 'blocked', progress: task.progress } : task));
                    break;
                case 'agent_status_changed':
                    setAgents(prev => ({
                        ...prev,
                        [event.agent]: {
                            agent: event.agent,
                            state: String(event.status?.state ?? 'idle').toLowerCase() as AgentStatus['state'],
                            current_task: event.status?.current_task,
                            last_update: event.status?.last_update ?? new Date().toISOString(),
                        },
                    }));
                    break;
                case 'approval_required':
                    setApprovals(prev => [{
                        id: event.approval.id,
                        label: event.approval.action?.description || 'Approval required',
                        status: 'pending',
                        risk: String(event.approval.action?.risk_level || 'medium').toLowerCase() as ApprovalState['risk'],
                    }, ...prev]);
                    break;
                case 'system_health':
                    setSystemHealth(prev => ({ ...prev, cpu: event.cpu, memory: event.memory }));
                    break;
                case 'tor_status':
                    setTorConnected(Boolean(event.connected));
                    break;
                case 'browser_status':
                    setBrowserActive(Boolean(event.active));
                    break;
                case 'finding_discovered':
                    setSession(prev => prev ? { ...prev, findings: [event.finding, ...prev.findings] } : prev);
                    break;
                default:
                    break;
            }
        });

        const handleSessionList = (customEvent: Event) => {
            const event = customEvent as CustomEvent;
            const sessions = event.detail?.sessions ?? [];
            if (!session && sessions.length > 0) {
                ws.send({ type: 'load_session', session_id: sessions[0].id });
            }
        };

        window.addEventListener('neurorift:session_list', handleSessionList);

        return () => {
            unsubscribe();
            window.removeEventListener('neurorift:session_list', handleSessionList);
        };
    }, [session]);

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
