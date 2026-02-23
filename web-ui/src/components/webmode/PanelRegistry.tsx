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
import { ManualToolPanel } from '@/components/webmode/panels/ManualToolPanel';
import { SessionManagerPanel } from '@/components/webmode/panels/SessionManagerPanel';
import { ArtifactViewerPanel } from '@/components/webmode/panels/ArtifactViewerPanel';
import { SystemHealthPanel } from '@/components/webmode/panels/SystemHealthPanel';

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
    'manual-tool': ManualToolPanel,
    'session-manager': SessionManagerPanel,
    'artifact-viewer': ArtifactViewerPanel,
    'system-health': SystemHealthPanel,
};
