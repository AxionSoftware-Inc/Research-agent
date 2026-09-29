"""
Checkpoint and Rollback (Undo) System
Tracks file modifications and allows instant single or multi-step rollback.
"""
import json
import shutil
import time
from pathlib import Path
from typing import Dict, List, Optional

from agent.config import WORKSPACE_DIR


class Checkpoint:
    def __init__(self, checkpoint_id: str, description: str, timestamp: float):
        self.checkpoint_id = checkpoint_id
        self.description = description
        self.timestamp = timestamp
        # Mapping from relative file path to previous content (None if file was newly created)
        self.file_states: Dict[str, Optional[str]] = {}

    def record_file(self, rel_path: str, previous_content: Optional[str]):
        if rel_path not in self.file_states:
            self.file_states[rel_path] = previous_content

    def to_dict(self) -> dict:
        return {
            "checkpoint_id": self.checkpoint_id,
            "description": self.description,
            "timestamp": self.timestamp,
            "file_states": self.file_states,
        }


class CheckpointManager:
    def __init__(self, workspace_dir: Path = WORKSPACE_DIR):
        self.workspace_dir = workspace_dir
        self.checkpoints_dir = workspace_dir / ".agent_checkpoints"
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)
        self.history: List[Checkpoint] = []
        self._active_checkpoint: Optional[Checkpoint] = None

    def begin_checkpoint(self, description: str) -> Checkpoint:
        """Start a new checkpoint session before tool execution"""
        checkpoint_id = f"chk_{int(time.time() * 1000)}"
        self._active_checkpoint = Checkpoint(
            checkpoint_id=checkpoint_id,
            description=description,
            timestamp=time.time(),
        )
        return self._active_checkpoint

    def track_file(self, file_path: str | Path):
        """Record the state of a file before it gets modified or created"""
        if not self._active_checkpoint:
            return

        target_path = Path(file_path)
        if not target_path.is_absolute():
            target_path = self.workspace_dir / target_path

        try:
            rel_path = str(target_path.relative_to(self.workspace_dir))
        except ValueError:
            rel_path = str(target_path)

        if rel_path in self._active_checkpoint.file_states:
            return

        if target_path.exists() and target_path.is_file():
            try:
                with open(target_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                self._active_checkpoint.record_file(rel_path, content)
            except Exception:
                self._active_checkpoint.record_file(rel_path, None)
        else:
            # File didn't exist prior to this step
            self._active_checkpoint.record_file(rel_path, None)

    def commit_checkpoint(self) -> Optional[Checkpoint]:
        """Finalize and save the active checkpoint if files were touched"""
        if not self._active_checkpoint:
            return None

        chk = self._active_checkpoint
        self._active_checkpoint = None

        if chk.file_states:
            self.history.append(chk)
            # Persist to disk
            meta_file = self.checkpoints_dir / f"{chk.checkpoint_id}.json"
            try:
                with open(meta_file, "w", encoding="utf-8") as f:
                    json.dump(chk.to_dict(), f, indent=2)
            except Exception:
                pass
            return chk
        return None

    def undo(self) -> str:
        """Rollback the latest checkpoint, restoring all files to previous states"""
        if not self.history:
            return "No previous checkpoints available to undo."

        chk = self.history.pop()
        restored = []
        deleted = []
        errors = []

        for rel_path, old_content in chk.file_states.items():
            full_path = self.workspace_dir / rel_path
            try:
                if old_content is None:
                    # File was newly created in this checkpoint, delete it on undo
                    if full_path.exists():
                        full_path.unlink()
                        deleted.append(rel_path)
                else:
                    # Restore previous content
                    full_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(full_path, "w", encoding="utf-8") as f:
                        f.write(old_content)
                    restored.append(rel_path)
            except Exception as e:
                errors.append(f"{rel_path}: {str(e)}")

        # Delete metadata file
        meta_file = self.checkpoints_dir / f"{chk.checkpoint_id}.json"
        if meta_file.exists():
            meta_file.unlink(missing_ok=True)

        msg_parts = [f"Reverted checkpoint '{chk.description}' (ID: {chk.checkpoint_id}):"]
        if restored:
            msg_parts.append(f"  - Restored ({len(restored)}): {', '.join(restored)}")
        if deleted:
            msg_parts.append(f"  - Removed newly created ({len(deleted)}): {', '.join(deleted)}")
        if errors:
            msg_parts.append(f"  - Errors ({len(errors)}): {', '.join(errors)}")

        return "\n".join(msg_parts)

    def list_checkpoints(self) -> List[dict]:
        return [
            {
                "id": c.checkpoint_id,
                "description": c.description,
                "time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(c.timestamp)),
                "files": list(c.file_states.keys()),
            }
            for c in reversed(self.history)
        ]


# Global instance
checkpoint_manager = CheckpointManager()
