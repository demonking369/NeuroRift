class TaskRouter:
    def route(self, task: str) -> dict:
        return {"task": task, "route": "agent_loop"}
