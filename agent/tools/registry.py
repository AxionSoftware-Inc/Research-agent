"""
Tool Registry and Schema Generator for Ollama
"""
import inspect
import json
from typing import Any, Callable, Dict, List, Optional


class Tool:
    def __init__(self, fn: Callable, name: Optional[str] = None, description: Optional[str] = None):
        self.fn = fn
        self.name = name or fn.__name__
        self.description = description or (inspect.getdoc(fn) or "").strip()
        self.schema = self._generate_schema()

    def _generate_schema(self) -> Dict[str, Any]:
        sig = inspect.signature(self.fn)
        properties = {}
        required = []

        type_map = {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
            list: "array",
            dict: "object",
        }

        for param_name, param in sig.parameters.items():
            if param_name in ("self", "cls"):
                continue

            param_type = "string"
            if param.annotation != inspect.Parameter.empty:
                param_type = type_map.get(param.annotation, "string")

            prop_def: Dict[str, Any] = {"type": param_type}

            # Optional default check
            if param.default == inspect.Parameter.empty:
                required.append(param_name)
            else:
                prop_def["default"] = param.default

            properties[param_name] = prop_def

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }

    def execute(self, **kwargs) -> str:
        try:
            res = self.fn(**kwargs)
            if isinstance(res, (dict, list)):
                return json.dumps(res, indent=2, ensure_ascii=False)
            return str(res)
        except Exception as e:
            return f"Error executing tool '{self.name}': {type(e).__name__}: {str(e)}"


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, fn_or_tool: Any, name: Optional[str] = None, description: Optional[str] = None):
        if isinstance(fn_or_tool, Tool):
            self._tools[fn_or_tool.name] = fn_or_tool
            return fn_or_tool
        tool = Tool(fn_or_tool, name=name, description=description)
        self._tools[tool.name] = tool
        return fn_or_tool

    def tool(self, name: Optional[str] = None, description: Optional[str] = None):
        """Decorator to register a tool function"""
        def decorator(fn: Callable):
            self.register(fn, name=name, description=description)
            return fn
        return decorator

    def get_tool(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def get_schemas(self) -> List[Dict[str, Any]]:
        return [tool.schema for tool in self._tools.values()]

    def list_tools(self) -> List[Dict[str, str]]:
        return [{"name": t.name, "description": t.description} for t in self._tools.values()]

    def execute(self, name: str, args: Dict[str, Any]) -> str:
        tool = self.get_tool(name)
        if not tool:
            return f"Error: Tool '{name}' not found. Available tools: {list(self._tools.keys())}"
        return tool.execute(**args)
