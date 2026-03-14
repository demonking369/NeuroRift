class LongTermMemory:
    def __init__(self): self.data={}
    def store(self, user_id: str, key: str, value): self.data.setdefault(user_id,{})[key]=value
