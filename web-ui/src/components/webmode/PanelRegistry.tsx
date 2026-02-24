import type React from 'react';
import type { PanelId } from '@/lib/webmode/types';
import { CommandPanel } from '@/components/webmode/panels/CommandPanel';
import { ActivityStreamPanel } from '@/components/webmode/panels/ActivityStreamPanel';
import { AgentGraphPanel } from '@/components/webmode/panels/AgentGraphPanel';
import { IntentFlowPanel } from '@/components/webmode/panels/IntentFlowPanel';
import { ExecutionTimelinePanel } from '@/components/webmode/panels/ExecutionTimelinePanel';
import { MemoryPulsePanel } from '@/components/webmode/panels/MemoryPulsePanel';
import { ConfigMatrixPanel } from '@/components/webmode/panels/ConfigMatrixPanel';
import { OnlineModePanel } from '@/components/webmode/panels/OnlineModePanel';
import { PermissionsPanel } from '@/components/webmode/panels/PermissionsPanel';

export const PanelRegistry: Record<PanelId, React.ComponentType> = {
    command: CommandPanel,
    activity: ActivityStreamPanel,
    'agent-graph': AgentGraphPanel,
    'intent-flow': IntentFlowPanel,
    'execution-timeline': ExecutionTimelinePanel,
    'memory-pulse': MemoryPulsePanel,
    'config-matrix': ConfigMatrixPanel,
    'online-mode': OnlineModePanel,
    permissions: PermissionsPanel,
};
