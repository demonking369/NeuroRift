from dataclasses import dataclass
@dataclass
class ResourceLimits:
    timeout_seconds:int=30
    memory_limit_mb:int=512
    cpu_seconds:int=20
