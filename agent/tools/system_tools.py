"""
Core System & Developer Tools (Claude Code / Codex Style)
"""
import fnmatch
import os
import subprocess
from pathlib import Path
from typing import Optional

from agent.config import WORKSPACE_DIR, MAX_TOOL_OUTPUT_CHARS
from agent.tools.registry import ToolRegistry


def register_system_tools(registry: ToolRegistry):

    @registry.tool(
        name="run_shell_command",
        description="Run a shell command (PowerShell on Windows) in the workspace directory. Use for building, testing, git, or running scripts."
    )
    def run_shell_command(command: str, timeout: int = 60) -> str:
        try:
            process = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
                cwd=str(WORKSPACE_DIR),
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding="utf-8",
                errors="replace",
            )
            stdout = process.stdout.strip()
            stderr = process.stderr.strip()
            code = process.returncode

            result_lines = []
            if stdout:
                result_lines.append(f"STDOUT:\n{stdout}")
            if stderr:
                result_lines.append(f"STDERR:\n{stderr}")
            result_lines.append(f"EXIT CODE: {code}")

            output = "\n".join(result_lines)
            if len(output) > MAX_TOOL_OUTPUT_CHARS:
                half = MAX_TOOL_OUTPUT_CHARS // 2
                output = output[:half] + f"\n\n... [Output truncated ({len(output)} chars total)] ...\n\n" + output[-half:]
            return output
        except subprocess.TimeoutExpired:
            return f"Error: Command timed out after {timeout} seconds."
        except Exception as e:
            return f"Error running command: {type(e).__name__}: {str(e)}"

    @registry.tool(
        name="read_file",
        description="Read the contents of a file with line numbers. Use start_line and line_count to read specific chunks."
    )
    def read_file(path: str, start_line: int = 1, line_count: int = 150) -> str:
        target_path = Path(path)
        if not target_path.is_absolute():
            target_path = WORKSPACE_DIR / target_path

        if not target_path.exists():
            return f"Error: File '{path}' does not exist."
        if target_path.is_dir():
            return f"Error: '{path}' is a directory, not a file. Use list_directory instead."

        try:
            with open(target_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

            total_lines = len(lines)
            if start_line < 1:
                start_line = 1

            start_idx = start_line - 1
            end_idx = min(start_idx + line_count, total_lines)

            if start_idx >= total_lines:
                return f"File '{path}' has {total_lines} lines. Requested start line {start_line} is out of range."

            output = [f"File: {path} (Lines {start_line}-{end_idx} of {total_lines})"]
            for i in range(start_idx, end_idx):
                output.append(f"{i + 1:4d}: {lines[i].rstrip()}")

            return "\n".join(output)
        except Exception as e:
            return f"Error reading file '{path}': {str(e)}"

    @registry.tool(
        name="write_file",
        description="Create a new file or overwrite an existing file with the provided content."
    )
    def write_file(path: str, content: str) -> str:
        target_path = Path(path)
        if not target_path.is_absolute():
            target_path = WORKSPACE_DIR / target_path

        try:
            from agent.checkpoint import checkpoint_manager
            checkpoint_manager.track_file(target_path)

            target_path.parent.mkdir(parents=True, exist_ok=True)
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(content)
            line_count = len(content.splitlines())
            return f"Successfully wrote {len(content)} bytes ({line_count} lines) to '{path}'."
        except Exception as e:
            return f"Error writing to file '{path}': {str(e)}"

    @registry.tool(
        name="edit_file",
        description="Surgically replace a text snippet in a file with new text. Whitespace and indentation resilient."
    )
    def edit_file(path: str, target_snippet: str, replacement: str) -> str:
        target_path = Path(path)
        if not target_path.is_absolute():
            target_path = WORKSPACE_DIR / target_path

        if not target_path.exists():
            return f"Error: File '{path}' does not exist."

        try:
            from agent.checkpoint import checkpoint_manager
            checkpoint_manager.track_file(target_path)

            with open(target_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 1. Exact match attempt
            if target_snippet in content:
                count = content.count(target_snippet)
                if count > 1:
                    return f"Error: target_snippet matched {count} times in '{path}'. Please provide more surrounding lines to make it unique."
                new_content = content.replace(target_snippet, replacement, 1)
                with open(target_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                return f"Successfully replaced snippet in '{path}'."

            # 2. Line-ending normalized match (CRLF vs LF)
            content_norm = content.replace("\r\n", "\n")
            target_norm = target_snippet.replace("\r\n", "\n")
            if target_norm in content_norm:
                count = content_norm.count(target_norm)
                if count > 1:
                    return f"Error: target_snippet matched {count} times in '{path}'. Please provide more surrounding lines to make it unique."
                new_content = content_norm.replace(target_norm, replacement.replace("\r\n", "\n"), 1)
                with open(target_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                return f"Successfully replaced snippet in '{path}' (normalized line endings)."

            # 3. Line-by-line whitespace-trimmed fuzzy match
            content_lines = content.splitlines(keepends=True)
            target_lines = [l.strip() for l in target_snippet.splitlines() if l.strip()]

            if not target_lines:
                return "Error: target_snippet is empty."

            match_start = -1
            match_len = 0
            for i in range(len(content_lines) - len(target_lines) + 1):
                window = [content_lines[i + j].strip() for j in range(len(target_lines))]
                if window == target_lines:
                    if match_start != -1:
                        return f"Error: target_snippet matched multiple locations in '{path}'. Please provide more surrounding lines."
                    match_start = i
                    match_len = len(target_lines)

            if match_start != -1:
                # Replace the matched lines
                prefix = content_lines[:match_start]
                suffix = content_lines[match_start + match_len:]
                rep_lines = [l + "\n" for l in replacement.splitlines()]
                new_lines = prefix + rep_lines + suffix
                with open(target_path, "w", encoding="utf-8") as f:
                    f.writelines(new_lines)
                return f"Successfully replaced snippet in '{path}' (fuzzy matched lines {match_start + 1}-{match_start + match_len})."

            return f"Error: target_snippet was not found in '{path}'. Make sure the snippet exists in the file."
        except Exception as e:
            return f"Error editing file '{path}': {str(e)}"

    @registry.tool(
        name="undo_last_action",
        description="Revert the most recent file modification or creation back to its exact previous state."
    )
    def undo_last_action() -> str:
        from agent.checkpoint import checkpoint_manager
        return checkpoint_manager.undo()

    @registry.tool(
        name="list_directory",
        description="List files and directories at a given path up to a specified depth."
    )
    def list_directory(path: str = ".", max_depth: int = 2) -> str:
        target_path = Path(path)
        if not target_path.is_absolute():
            target_path = WORKSPACE_DIR / target_path

        if not target_path.exists():
            return f"Error: Path '{path}' does not exist."

        entries = []
        base_depth = len(target_path.parts)

        ignore_dirs = {".git", ".venv", "__pycache__", "node_modules", ".idea", ".vscode"}

        try:
            for root, dirs, files in os.walk(target_path):
                rel_parts = Path(root).relative_to(target_path).parts
                cur_depth = len(rel_parts)

                dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith(".")]

                indent = "  " * cur_depth
                folder_name = os.path.basename(root)
                if cur_depth > 0:
                    entries.append(f"{indent[:-2]}[DIR] {folder_name}/")

                if cur_depth < max_depth:
                    for f in sorted(files):
                        entries.append(f"{indent}[FILE] {f}")

                if cur_depth >= max_depth:
                    dirs.clear()

            return "\n".join(entries[:200]) if entries else f"Empty directory: '{path}'"
        except Exception as e:
            return f"Error listing directory '{path}': {str(e)}"

    @registry.tool(
        name="grep_search",
        description="Search for a text pattern or word across files in the workspace."
    )
    def grep_search(query: str, path: str = ".", extension: str = "") -> str:
        target_path = Path(path)
        if not target_path.is_absolute():
            target_path = WORKSPACE_DIR / target_path

        matches = []
        ignore_dirs = {".git", ".venv", "__pycache__", "node_modules"}

        for root, dirs, files in os.walk(target_path):
            dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith(".")]
            for file in files:
                if extension and not file.endswith(extension):
                    continue
                file_path = Path(root) / file
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        for idx, line in enumerate(f, 1):
                            if query.lower() in line.lower():
                                rel_path = file_path.relative_to(WORKSPACE_DIR)
                                matches.append(f"{rel_path}:{idx}: {line.strip()[:150]}")
                                if len(matches) >= 50:
                                    matches.append("... [More than 50 matches found, truncated] ...")
                                    return "\n".join(matches)
                except Exception:
                    continue

        if not matches:
            return f"No matches found for query '{query}' in '{path}'."
        return "\n".join(matches)
