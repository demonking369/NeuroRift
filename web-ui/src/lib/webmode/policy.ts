import type { PanelDefinition, PolicyContext } from '@/lib/webmode/types';

export function evaluatePanelPolicy(panel: PanelDefinition, context: PolicyContext) {
    if (panel.policy.requiresSession && !context.sessionActive) {
        return false;
    }

    if (panel.policy.controlOnly && context.controlMode !== 'control') {
        return false;
    }

    if (panel.policy.minTier) {
        const tiers = ['mobile', 'tablet', 'desktop', 'wide'] as const;
        const required = tiers.indexOf(panel.policy.minTier);
        const current = tiers.indexOf(context.deviceTier);
        if (current < required) {
            return false;
        }
    }

    return true;
}
