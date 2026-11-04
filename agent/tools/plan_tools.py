"""
Planning and Sub-goal Decomposition Tools for Long-Horizon Agent Execution
"""
from typing import List, Optional
from agent.tools.registry import ToolRegistry


class PlanTracker:
    def __init__(self):
        self.steps: List[str] = []
        self.current_step: int = 0
        self.notes: str = ""

    def update(self, steps: List[str], current_step: int, notes: str = ""):
        self.steps = steps
        self.current_step = max(0, min(current_step, len(steps)))
        self.notes = notes

    def get_summary(self) -> str:
        if not self.steps:
            return "No active plan."
        lines = ["Current Execution Plan:"]
        for idx, step in enumerate(self.steps, 1):
            if idx < self.current_step:
                status = "[DONE]"
            elif idx == self.current_step:
                status = "[CURRENT]"
            else:
                status = "[TODO]"
            lines.append(f"  {idx}. {status} {step}")
        if self.notes:
            lines.append(f"  Notes: {self.notes}")
        return "\n".join(lines)


# Global plan tracker instance
plan_tracker = PlanTracker()


def register_plan_tools(registry: ToolRegistry):

    @registry.tool(
        name="update_plan",
        description="Decompose a complex task into explicit steps, or update current progress in the plan."
    )
    def update_plan(steps: List[str], current_step: int, notes: str = "") -> str:
        plan_tracker.update(steps=steps, current_step=current_step, notes=notes)
        return f"Plan updated successfully!\n\n{plan_tracker.get_summary()}"
