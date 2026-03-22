from collections import defaultdict, deque


class ShortTermMemory:
    def __init__(self, limit: int = 30):
        self.buffers = defaultdict(lambda: deque(maxlen=limit))

    def add(self, sid: str, msg: str):
        self.buffers[sid].append(msg)
