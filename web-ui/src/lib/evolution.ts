export interface SelfEvolutionConfig {
    enabled: boolean;
    require_human_approval: boolean;
    sandbox_branch: string;
}

export const DEFAULT_SELF_EVOLUTION: SelfEvolutionConfig = {
    enabled: true,
    require_human_approval: true,
    sandbox_branch: 'ai-evolution',
};
