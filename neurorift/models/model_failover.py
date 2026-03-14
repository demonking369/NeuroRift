class ModelFailover:
    def pick(self, providers): return providers[0] if providers else "fallback"
