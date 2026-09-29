"""
Autonomous Long-Horizon Project Orchestrator (Plan Mode & Self-Chaining Loop)
Decomposes massive macro-tasks (e.g. 1000-page book, multi-module software) into a stateful blueprint,
executes steps iteratively with self-wakeup, flushes context between steps, and audits drift with LLM Critic.
"""
import json
import re
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from agent.config import WORKSPACE_DIR
from agent.context import ContextManager
from agent.critic import evaluate_alignment_and_drift
from agent.engine import Agent
from agent.llm import OllamaClient
from agent.memory import memory_ledger


class StepItem:
    def __init__(self, step_id: int, title: str, description: str, target_file: str = ""):
        self.step_id = step_id
        self.title = title
        self.description = description
        self.target_file = target_file
        self.status = "pending"  # "pending", "in_progress", "completed", "failed"
        self.alignment_score: Optional[int] = None
        self.quality_score: Optional[int] = None
        self.completed_at: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            "step_id": self.step_id,
            "title": self.title,
            "description": self.description,
            "target_file": self.target_file,
            "status": self.status,
            "alignment_score": self.alignment_score,
            "quality_score": self.quality_score,
            "completed_at": self.completed_at,
        }


class ProjectBlueprint:
    def __init__(self, goal: str, steps: List[StepItem], workspace_dir: Path = WORKSPACE_DIR):
        self.goal = goal
        self.steps = steps
        self.created_at = time.time()
        self.current_step_index = 0
        self.workspace_dir = Path(workspace_dir)
        self.file_path = self.workspace_dir / "project_blueprint.json"
        self.save()

    def save(self):
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "goal": self.goal,
                "current_step_index": self.current_step_index,
                "total_steps": len(self.steps),
                "created_at": self.created_at,
                "steps": [s.to_dict() for s in self.steps],
            }
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    @classmethod
    def load(cls, workspace_dir: Path = WORKSPACE_DIR) -> Optional["ProjectBlueprint"]:
        target = Path(workspace_dir) / "project_blueprint.json"
        if not target.exists():
            return None
        try:
            with open(target, "r", encoding="utf-8") as f:
                data = json.load(f)
            steps = [
                StepItem(
                    step_id=s["step_id"],
                    title=s["title"],
                    description=s["description"],
                    target_file=s.get("target_file", ""),
                )
                for s in data.get("steps", [])
            ]
            bp = cls(goal=data["goal"], steps=steps, workspace_dir=workspace_dir)
            bp.current_step_index = data.get("current_step_index", 0)
            return bp
        except Exception:
            return None


def is_macro_task(prompt: str) -> bool:
    """Detects if a user explicitly requested Plan Mode or multi-stage project blueprint"""
    p_lower = prompt.lower().strip()
    if p_lower.startswith("/plan") or p_lower.startswith("/blueprint"):
        return True
    explicit_markers = [
        "ko'p bosqichli reja", "arxitektura rejasi", "kitob yozish", "1000 bet",
        "yuzlab sahifa", "multi-chapter", "blueprint rejasi"
    ]
    return any(m in p_lower for m in explicit_markers)


def generate_blueprint_plan(llm: OllamaClient, user_prompt: str) -> List[StepItem]:
    """Uses LLM to break down a massive research or writing goal into actionable milestone steps"""
    plan_prompt = f"""You are a Senior Academic Research Director and Scientific Architect.
Break down the following research or macro project goal into a sequence of 5 to 10 actionable, self-contained milestone steps.
Each step should specify what research, literature extraction, or drafting to execute and the target output file.

Standard research sequence:
1. Research Scoping & Query Formulation (`01_research_scope.md`)
2. Literature Search & Ingestion (`02_literature_survey.md`, `references.bib`)
3. Methodology & Comparative Analysis (`03_methodology_analysis.md`)
4. Synthesis & Core Findings Draft (`04_findings_discussion.md`)
5. Full Paper/Report Assembly with Citations (`research_paper.tex` or `final_report.md`)
6. Review & Compilation to PDF (`outputs/research_paper.pdf`)

[GOAL]: {user_prompt}

Respond ONLY with valid JSON array of objects with keys "title", "description", "target_file":
[
  {{
    "title": "1-qadam: Mavzuni aniqlash va qidiruv strategiyasi",
    "description": "arXiv va internet uchun qidiruv so'zlarini shakllantirish va mavzu doirasini belgilash.",
    "target_file": "01_research_scope.md"
  }},
  ...
]
"""
    messages = [
        {"role": "system", "content": "You are a master research planning architect. Output valid JSON array only."},
        {"role": "user", "content": plan_prompt},
    ]

    try:
        resp = llm.chat(messages=messages, temperature=0.1, timeout=60.0)
        content = resp.get("content", "").strip()
        match = re.search(r"\[.*\]", content, re.DOTALL)
        if match:
            items = json.loads(match.group(0))
            steps = []
            for idx, item in enumerate(items, 1):
                steps.append(
                    StepItem(
                        step_id=idx,
                        title=item.get("title", f"Step {idx}"),
                        description=item.get("description", ""),
                        target_file=item.get("target_file", f"output_step_{idx}.md"),
                    )
                )
            if steps:
                return steps
    except Exception:
        pass

    # Fallback standard research blueprint
    return [
        StepItem(1, "Qidiruv va Adabiyotlar tahlili", "arXiv va ochiq internetdan manbalarni qidirish, references.bib ga kiritish", "01_literature_survey.md"),
        StepItem(2, "Nazariya va Metodologiya tahlili", "Topilgan ilmiy maqolalarning uslubiyoti, formulalari va qiyosiy tahlili", "02_methodology_matrix.md"),
        StepItem(3, "Natijalar sintezi va Muhokama", "Natijalar, afzalliklar va cheklovlarni umumlashtirish", "03_findings_synthesis.md"),
        StepItem(4, "Ilmiy maqola loyihasi (LaTeX)", "Mavzu bo'yicha to'liq maqolani iqtiboslar bilan yozish", "research_paper.tex"),
        StepItem(5, "Yakuniy tahrir va PDF kompilyatsiyasi", "Tectonic bilan maqolani PDF ko'rinishida chiqarish", "outputs/research_paper.pdf"),
    ]

