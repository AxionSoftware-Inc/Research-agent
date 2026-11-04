"""
Tools package initialization
"""
from agent.tools.registry import ToolRegistry
from agent.tools.system_tools import register_system_tools
from agent.tools.research_tools import register_research_tools
from agent.tools.code_index import register_code_index_tools
from agent.tools.plan_tools import register_plan_tools


def create_default_registry() -> ToolRegistry:
    registry = ToolRegistry()
    register_system_tools(registry)
    register_research_tools(registry)
    register_code_index_tools(registry)
    register_plan_tools(registry)
    return registry


__all__ = ["ToolRegistry", "create_default_registry"]
