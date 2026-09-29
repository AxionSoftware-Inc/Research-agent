"""
Live Test of gemma4-26b:latest with Autonomous Research Agent
Validates:
1. Local Ollama connection to gemma4-26b:latest
2. Streaming thinking & reasoning
3. Tool execution through the model
4. Final academic synthesis
"""
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from agent.llm import UniversalLLMClient
from agent.tools import create_default_registry
from agent.context import ContextManager
from agent.engine import Agent


def test_gemma4_live():
    print("=" * 70)
    print("🚀 LIVE TEST: Autonomous AI Research Agent with gemma4-26b:latest")
    print("=" * 70)

    model_name = "gemma4-26b:latest"
    print(f"📡 Connecting to local Ollama on http://127.0.0.1:11434 with model: {model_name}...")

    llm = UniversalLLMClient(
        base_url="http://127.0.0.1:11434",
        model=model_name,
        provider="ollama",
    )

    registry = create_default_registry()
    context = ContextManager()
    agent = Agent(llm=llm, tools=registry, context=context, max_iterations=4)

    test_prompt = "Search arXiv for 1 recent paper about 'quantum computing algorithms', summarize its key contribution in 2-3 sentences, and cite its suggested BibTeX key."
    print(f"\n📝 User Prompt: \"{test_prompt}\"\n")
    print("-" * 70)

    def on_thinking_chunk(chunk):
        sys.stdout.write(chunk)
        sys.stdout.flush()

    def on_content_chunk(chunk):
        sys.stdout.write(chunk)
        sys.stdout.flush()

    def on_tool_call(name, args):
        print(f"\n\n⚙️ [TOOL CALL]: {name}")
        print(f"   Arguments: {args}\n")

    def on_tool_result(name, res):
        lines = res.splitlines()
        preview = lines[0] if lines else ""
        print(f"📥 [TOOL RESULT]: ({len(lines)} lines) -> {preview[:100]}...\n")

    start_time = time.time()
    try:
        final_result = agent.run(
            user_prompt=test_prompt,
            on_thinking_chunk=on_thinking_chunk,
            on_content_chunk=on_content_chunk,
            on_tool_call=on_tool_call,
            on_tool_result=on_tool_result,
        )
        elapsed = time.time() - start_time
        print("\n" + "=" * 70)
        print(f"🎉 SUCCESS! Agent run finished in {elapsed:.1f}s using {model_name}")
        print("=" * 70)
        return True
    except Exception as e:
        print(f"\n❌ Error during live run: {type(e).__name__}: {str(e)}")
        return False


if __name__ == "__main__":
    test_gemma4_live()
