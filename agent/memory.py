"""
Persistent Dense Project Memory Ledger
Maintains an ultra-compact (< 300-500 tokens) persistent memory of the project,
allowing millions of tokens of cumulative work without blowing up the LLM context.
"""
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent.config import WORKSPACE_DIR


class MemoryLedger:
    def __init__(self, workspace_dir: Path = WORKSPACE_DIR):
        self.workspace_dir = Path(workspace_dir)
        self.memory_file = self.workspace_dir / ".agent_memory.json"
        self.data: Dict[str, Any] = self._load()

    def _default_state(self) -> Dict[str, Any]:
        return {
            "project_name": self.workspace_dir.name,
            "tech_stack": "Python, Next.js, FastAPI, Ollama, Tectonic",
            "key_facts": [],
            "known_files": {},
            "active_milestones": [],
            "completed_tasks": [],
            "last_updated": time.time(),
        }

    def _load(self) -> Dict[str, Any]:
        if self.memory_file.exists():
            try:
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return self._default_state()

    def save(self):
        try:
            self.memory_file.parent.mkdir(parents=True, exist_ok=True)
            self.data["last_updated"] = time.time()
            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def add_fact(self, fact: str):
        fact = fact.strip()
        if fact and fact not in self.data["key_facts"]:
            self.data["key_facts"].append(fact)
            if len(self.data["key_facts"]) > 25:
                self.data["key_facts"].pop(0)  # Keep most recent
            self.save()

    def record_touched_file(self, rel_path: str, role: str):
        self.data["known_files"][rel_path] = role
        if len(self.data["known_files"]) > 30:
            # Keep top 30 files
            oldest_key = next(iter(self.data["known_files"]))
            del self.data["known_files"][oldest_key]
        self.save()

    def record_completed_task(self, task_summary: str):
        task_summary = task_summary.strip()
        if task_summary:
            self.data["completed_tasks"].append(task_summary)
            if len(self.data["completed_tasks"]) > 10:
                self.data["completed_tasks"].pop(0)
            self.save()

    def format_for_context(self) -> str:
        """
        Synthesizes an ultra-dense, token-efficient prompt string (< 250 tokens).
        This provides perfect recall without bloating the context window.
        """
        lines = [
            f"### PROJECT MEMORY & SCRATCHPAD (Workspace: {self.data.get('project_name', '')}):",
            f"- Tech: {self.data.get('tech_stack', 'N/A')}",
        ]

        # Key facts
        facts = self.data.get("key_facts", [])
        if facts:
            lines.append("- Critical Learnings:")
            for f in facts[-8:]:
                lines.append(f"  * {f}")

        # Touched files
        files = self.data.get("known_files", {})
        if files:
            files_list = [f"{k} ({v})" for k, v in list(files.items())[-8:]]
            lines.append(f"- Key Files: {', '.join(files_list)}")

        # Recent tasks completed
        tasks = self.data.get("completed_tasks", [])
        if tasks:
            lines.append("- Recent Finished Work:")
            for t in tasks[-4:]:
                lines.append(f"  * {t}")

        return "\n".join(lines)

    def reset(self):
        self.data = self._default_state()
        self.save()


# Global memory ledger
memory_ledger = MemoryLedger()
