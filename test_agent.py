"""
End-to-end Test for Universal Agent with Gemma 4 26B
"""
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from agent.llm import OllamaClient
from agent.tools import create_default_registry
from agent.context import ContextManager
from agent.engine import Agent


def test_agent():
    print(">>> Initializing Agent with gemma4-26b:latest ...")
    llm = OllamaClient(model="gemma4-26b:latest")
    registry = create_default_registry()
    context = ContextManager()
    agent = Agent(llm=llm, tools=registry, context=context, max_iterations=5)

    print(f">>> Registered tools: {[t['name'] for t in registry.list_tools()]}")

    test_prompt = "Please list the files in the 'test_data' folder using the list_directory tool, and summarize what you find."
    print(f"\n>>> Running test prompt: {test_prompt}")

    def on_th(th):
        print(f"\n[Thinking]: {th}\n")

    def on_tc(name, args):
        print(f"[Tool Call]: {name} with args {args}")

    def on_tr(name, res):
        lines = res.splitlines()
        preview = lines[0] if lines else ""
        print(f"[Tool Result]: ({len(lines)} lines) -> {preview[:100]}...")

    def on_msg(msg):
        print(f"\n[Final Response]:\n{msg}\n")

    result = agent.run(
        user_prompt=test_prompt,
        on_thinking=on_th,
        on_tool_call=on_tc,
        on_tool_result=on_tr,
        on_message=on_msg
    )

    print(">>> Agent run finished successfully!")
    return result


if __name__ == "__main__":
    test_agent()
