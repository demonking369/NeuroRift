from dataclasses import dataclass


@dataclass
class PlannedStep:
    order: int
    action: str


class Planner:
    def create_plan(self, objective: str) -> list[PlannedStep]:
        return (
            [PlannedStep(order=1, action=f"Investigate: {objective}")]
            if objective
            else []
        )
