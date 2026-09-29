"""
Context and Memory Management for the Agent with Smart Summarization & Persistent Dense Memory Ledger
"""
from typing import Any, Dict, List, Optional, Set
from agent.config import DEFAULT_SYSTEM_PROMPT, CONTEXT_MAX_MESSAGES, MAX_TOOL_OUTPUT_CHARS
from agent.memory import memory_ledger
from agent.tools.plan_tools import plan_tracker


class ContextManager:
    def __init__(self, system_prompt: str = DEFAULT_SYSTEM_PROMPT):
        self.system_prompt = system_prompt
        self.messages: List[Dict[str, Any]] = []
        self.touched_files: Set[str] = set()
        self.compacted_summaries: List[str] = []
        self.reset()

    def reset(self):
        """Reset conversation back to system prompt + persistent memory ledger"""
        self.messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        self.touched_files.clear()
        self.compacted_summaries.clear()

    def add_user_message(self, content: str):
        self.messages.append({"role": "user", "content": content})
        self._prune_if_needed()

    def add_assistant_message(
        self,
        content: str,
        thinking: Optional[str] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None
    ):
        msg: Dict[str, Any] = {"role": "assistant", "content": content or ""}
        if thinking:
            msg["thinking"] = thinking
        if tool_calls:
            msg["tool_calls"] = tool_calls
        self.messages.append(msg)
        self._prune_if_needed()

    def add_tool_result(self, tool_name: str, result: str, tool_call_id: Optional[str] = None):
        """Truncate massive tool outputs and record tool result"""
        truncated_result = result
        if len(result) > MAX_TOOL_OUTPUT_CHARS:
            half = MAX_TOOL_OUTPUT_CHARS // 2
            truncated_result = (
                result[:half]
                + f"\n\n... [Output truncated ({len(result)} total chars)] ...\n\n"
                + result[-half:]
            )

        msg: Dict[str, Any] = {
            "role": "tool",
            "name": tool_name,
            "content": truncated_result,
        }
        if tool_call_id:
            msg["tool_call_id"] = tool_call_id

        self.messages.append(msg)
        self._prune_if_needed()

    def get_messages_for_llm(self) -> List[Dict[str, Any]]:
        """
        Format messages for Ollama /api/chat.
        Injects persistent memory ledger, compacted memory, and active plan.
        """
        active_plan = plan_tracker.get_summary()
        dense_memory = memory_ledger.format_for_context()

        dynamic_system_addons = [dense_memory]
        if self.compacted_summaries:
            dynamic_system_addons.append("### COMPACTED ACTIONS:\n" + "\n".join(self.compacted_summaries))
        if active_plan != "No active plan.":
            dynamic_system_addons.append(f"### ACTIVE PLAN:\n{active_plan}")

        formatted = []
        for i, msg in enumerate(self.messages):
            content = msg.get("content", "")
            if i == 0 and msg["role"] == "system" and dynamic_system_addons:
                content = content + "\n\n" + "\n\n".join(dynamic_system_addons)

            entry = {
                "role": msg["role"],
                "content": content,
            }
            if "tool_calls" in msg and msg["tool_calls"]:
                entry["tool_calls"] = msg["tool_calls"]
            if "tool_call_id" in msg and msg["tool_call_id"]:
                entry["tool_call_id"] = msg["tool_call_id"]
            formatted.append(entry)
        return formatted

    def finalize_task_and_flush(self, task_prompt: str, final_answer: str, tools_used: List[str]):
        """
        Cleans up the ephemeral context after a task finishes!
        Saves key learnings into the persistent Memory Ledger, then flushes all intermediate
        bloated tool outputs, resetting the active conversation context back to a lean ~400 tokens.
        """
        # Record task in memory ledger
        memory_ledger.record_completed_task(f"{task_prompt[:80]} -> Success")
        if tools_used:
            memory_ledger.add_fact(f"Tools used: {', '.join(set(tools_used))}")

        # Keep only system prompt, original prompt, and short final answer
        short_answer = final_answer[:500] if len(final_answer) > 500 else final_answer
        self.messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": task_prompt},
            {"role": "assistant", "content": short_answer},
        ]
        self.compacted_summaries.clear()

    def _prune_if_needed(self):
        """Prunes intermediate tool calls if conversation grows too long"""
        if len(self.messages) <= CONTEXT_MAX_MESSAGES:
            return

        fixed_prefix = self.messages[:2]
        prune_count = len(self.messages) - (CONTEXT_MAX_MESSAGES - 5)
        to_prune = self.messages[2:2 + prune_count]
        remaining_tail = self.messages[2 + prune_count:]

        summary_points = []
        for m in to_prune:
            role = m.get("role")
            if role == "assistant" and "tool_calls" in m:
                for tc in m["tool_calls"]:
                    fn = tc.get("function", {})
                    name = fn.get("name")
                    summary_points.append(f"- Action: {name}")

        if summary_points:
            self.compacted_summaries.append("\n".join(summary_points[-10:]))

        notice = {
            "role": "system",
            "content": f"[System: {len(to_prune)} intermediate steps summarized into memory to keep context lean.]"
        }
        self.messages = fixed_prefix + [notice] + remaining_tail

    def get_token_estimate(self) -> int:
        total_chars = sum(len(str(m.get("content", ""))) for m in self.messages)
        return int(total_chars / 3.5)
