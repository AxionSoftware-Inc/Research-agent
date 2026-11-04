"""
AST and Codebase Structural Indexer (Tree-sitter & AST style analysis)
Enables instantaneous symbol lookup, file outlines, and reference discovery in large codebases.
"""
import ast
import os
import re
from pathlib import Path
from typing import Dict, List, Optional

from agent.config import WORKSPACE_DIR
from agent.tools.registry import ToolRegistry


def parse_python_outline(file_path: Path) -> str:
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            code = f.read()
        tree = ast.parse(code, filename=str(file_path))

        outline = [f"File: {file_path.name}"]
        imports = []
        classes = []
        functions = []

        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                names = ", ".join(a.name for a in node.names)
                imports.append(f"from {module} import {names}")
            elif isinstance(node, ast.ClassDef):
                bases = [ast.unparse(b) for b in node.bases]
                base_str = f"({', '.join(bases)})" if bases else ""
                class_desc = [f"  class {node.name}{base_str} (Line {node.lineno}):"]
                # Document docstring
                doc = ast.get_docstring(node)
                if doc:
                    class_desc.append(f"    \"\"\"{doc.splitlines()[0][:80]}\"\"\"")
                # Class methods
                for sub in node.body:
                    if isinstance(sub, ast.FunctionDef):
                        args = [a.arg for a in sub.args.args]
                        class_desc.append(f"    def {sub.name}({', '.join(args)}) [L{sub.lineno}]")
                classes.append("\n".join(class_desc))
            elif isinstance(node, ast.FunctionDef):
                args = [a.arg for a in node.args.args]
                doc = ast.get_docstring(node)
                doc_str = f" - {doc.splitlines()[0][:60]}" if doc else ""
                functions.append(f"  def {node.name}({', '.join(args)}) [Line {node.lineno}]{doc_str}")

        if imports:
            outline.append(f"Imports ({len(imports)}): " + ", ".join(imports[:10]))
        if classes:
            outline.append("Classes:\n" + "\n".join(classes))
        if functions:
            outline.append("Functions:\n" + "\n".join(functions))

        return "\n".join(outline) if (classes or functions) else f"File: {file_path.name} (No top-level classes or functions found)"
    except Exception as e:
        return f"Error parsing Python AST for '{file_path.name}': {str(e)}"


def parse_generic_outline(file_path: Path) -> str:
    """Regex based symbol extraction for JS/TS, Rust, Go, C++, etc."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        patterns = [
            (re.compile(r"^\s*(?:export\s+)?class\s+(\w+)"), "class"),
            (re.compile(r"^\s*(?:export\s+)?interface\s+(\w+)"), "interface"),
            (re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)"), "function"),
            (re.compile(r"^\s*(?:pub\s+)?fn\s+(\w+)\s*\(([^)]*)\)"), "fn"),
            (re.compile(r"^\s*func\s+(?:\([^)]+\)\s+)?(\w+)\s*\(([^)]*)\)"), "func"),
        ]

        symbols = []
        for i, line in enumerate(lines, 1):
            for pat, kind in patterns:
                m = pat.search(line)
                if m:
                    name = m.group(1)
                    symbols.append(f"  [{kind}] {name} (Line {i})")
                    break

        if not symbols:
            return f"File: {file_path.name} (No structural symbols matched)"
        return f"File: {file_path.name} Outline:\n" + "\n".join(symbols[:50])
    except Exception as e:
        return f"Error parsing outline for '{file_path.name}': {str(e)}"


def register_code_index_tools(registry: ToolRegistry):

    @registry.tool(
        name="get_file_outline",
        description="Get a structural AST outline of a file (classes, methods, functions, and signatures) without reading full code."
    )
    def get_file_outline(path: str) -> str:
        target_path = Path(path)
        if not target_path.is_absolute():
            target_path = WORKSPACE_DIR / target_path

        if not target_path.exists():
            return f"Error: File '{path}' does not exist."

        suffix = target_path.suffix.lower()
        if suffix == ".py":
            return parse_python_outline(target_path)
        elif suffix in (".js", ".ts", ".jsx", ".tsx", ".rs", ".go", ".cpp", ".c", ".h", ".cs", ".java"):
            return parse_generic_outline(target_path)
        else:
            return f"Outline not supported for file type '{suffix}'. Use read_file instead."

    @registry.tool(
        name="find_symbol",
        description="Find where a class, function, or method is defined across the entire codebase."
    )
    def find_symbol(symbol_name: str, path: str = ".") -> str:
        target_path = Path(path)
        if not target_path.is_absolute():
            target_path = WORKSPACE_DIR / target_path

        ignore_dirs = {".git", ".venv", "__pycache__", "node_modules", "outputs", ".agent_checkpoints"}
        matches = []

        symbol_pattern = re.compile(
            rf"^\s*(?:def|class|function|interface|fn|func|var|let|const|type)\s+{re.escape(symbol_name)}\b"
        )

        for root, dirs, files in os.walk(target_path):
            dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith(".")]
            for file in files:
                ext = Path(file).suffix.lower()
                if ext not in (".py", ".js", ".ts", ".jsx", ".tsx", ".rs", ".go", ".cpp", ".h", ".cs", ".java"):
                    continue

                full_file = Path(root) / file
                try:
                    with open(full_file, "r", encoding="utf-8", errors="ignore") as f:
                        for idx, line in enumerate(f, 1):
                            if symbol_pattern.search(line):
                                rel_path = full_file.relative_to(WORKSPACE_DIR)
                                matches.append(f"{rel_path}:{idx}: {line.strip()}")
                except Exception:
                    continue

        if not matches:
            return f"Symbol '{symbol_name}' was not found defined in the codebase."
        return f"Found {len(matches)} definition(s) for '{symbol_name}':\n" + "\n".join(matches)

    @registry.tool(
        name="find_references",
        description="Find all files and lines where a symbol is referenced, called, or imported."
    )
    def find_references(symbol_name: str, path: str = ".") -> str:
        target_path = Path(path)
        if not target_path.is_absolute():
            target_path = WORKSPACE_DIR / target_path

        ignore_dirs = {".git", ".venv", "__pycache__", "node_modules", "outputs", ".agent_checkpoints"}
        matches = []
        ref_pattern = re.compile(rf"\b{re.escape(symbol_name)}\b")

        for root, dirs, files in os.walk(target_path):
            dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith(".")]
            for file in files:
                ext = Path(file).suffix.lower()
                if ext not in (".py", ".js", ".ts", ".jsx", ".tsx", ".rs", ".go", ".cpp", ".h", ".cs", ".java", ".md", ".tex"):
                    continue

                full_file = Path(root) / file
                try:
                    with open(full_file, "r", encoding="utf-8", errors="ignore") as f:
                        for idx, line in enumerate(f, 1):
                            if ref_pattern.search(line):
                                rel_path = full_file.relative_to(WORKSPACE_DIR)
                                matches.append(f"{rel_path}:{idx}: {line.strip()[:140]}")
                                if len(matches) >= 60:
                                    matches.append("... [Over 60 references found, truncated] ...")
                                    return "\n".join(matches)
                except Exception:
                    continue

        if not matches:
            return f"No references found for '{symbol_name}'."
        return f"Found {len(matches)} reference(s) to '{symbol_name}':\n" + "\n".join(matches)
