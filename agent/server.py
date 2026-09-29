"""
FastAPI Server providing REST & SSE Streaming API for Next.js / Tauri GUI
Features:
- Multi-Chat / Parallel Sessions Management
- Real-time Context Metrics & Token Tracking
- Stop / Abort Task Execution
- File & Image Upload with Workspace Extraction
- Workspace / Project Folder Switching
- Runtime Settings Configuration
"""
import json
import os
import queue
import shutil
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure project root is in sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel

from agent.checkpoint import checkpoint_manager
from agent.config import (
    DEFAULT_MODEL,
    DEFAULT_SYSTEM_PROMPT,
    MAX_ITERATIONS,
    OLLAMA_URL,
    WORKSPACE_DIR,
)
from agent.context import ContextManager
from agent.engine import Agent
from agent.llm import OllamaClient, UniversalLLMClient, detect_local_providers, ModelConfig
from agent.tools import create_default_registry
from agent.tools.plan_tools import PlanTracker
from agent.vram import (
    get_vram_status,
    unload_model_from_vram,
    unload_all_other_models,
    preload_model_into_vram,
    swap_and_ensure_vram,
)

app = FastAPI(title="Local Agent API", version="2.0.0")

# Enable CORS for Next.js / Tauri frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# App-level mutable settings
app_settings = {
    "ollama_url": OLLAMA_URL,
    "default_model": DEFAULT_MODEL,
    "temperature": 0.2,
    "max_iterations": MAX_ITERATIONS,
    "system_prompt": DEFAULT_SYSTEM_PROMPT,
    "workspace_dir": str(WORKSPACE_DIR),
    "plan_mode_auto": True,
    "critic_enabled": True,
    "auto_flush_context": True,
    "context_window_size": 262144,
    "top_p": 0.95,
}

# Model context limit registry
MODEL_CONTEXT_LIMITS = {
    "gemma4-26b": 262144,
    "gemma4": 262144,
    "qwen3": 32768,
    "qwen2.5": 32768,
    "llama3.3": 131072,
    "llama3": 8192,
    "mistral": 32768,
}


def get_model_context_limit(model_name: str) -> int:
    lower = model_name.lower()
    for key, limit in MODEL_CONTEXT_LIMITS.items():
        if key in lower:
            return limit
    return 32768


# Shared tool registry
tool_registry = create_default_registry()

# Models & API Providers Registry
models_registry: Dict[str, dict] = {
    "gemma4-26b:latest": {
        "id": "gemma4-26b:latest",
        "name": "gemma4-26b:latest (Ollama Local)",
        "provider": "ollama",
        "base_url": app_settings["ollama_url"],
        "model_name": "gemma4-26b:latest",
        "api_key": None,
        "input_cost_per_1m": 0.0,
        "output_cost_per_1m": 0.0,
        "is_local": True,
    }
}


def get_llm_client_for_model(model_id_or_name: str) -> UniversalLLMClient:
    cfg = models_registry.get(model_id_or_name)
    if cfg:
        return UniversalLLMClient(
            base_url=cfg["base_url"],
            model=cfg["model_name"],
            provider=cfg.get("provider", "ollama"),
            api_key=cfg.get("api_key"),
            input_cost_per_1m=cfg.get("input_cost_per_1m", 0.0),
            output_cost_per_1m=cfg.get("output_cost_per_1m", 0.0),
        )
    return UniversalLLMClient(
        base_url=app_settings["ollama_url"],
        model=model_id_or_name,
        provider="ollama",
    )


class SessionState:
    def __init__(self, session_id: str, name: str, model: str, project_id: str = "proj_default"):
        self.session_id = session_id
        self.name = name
        self.model = model
        self.project_id = project_id
        self.llm_client = get_llm_client_for_model(model)
        self.context = ContextManager(system_prompt=app_settings["system_prompt"])
        self.plan_tracker = PlanTracker()
        self.agent = Agent(
            llm=self.llm_client,
            tools=tool_registry,
            context=self.context,
            max_iterations=app_settings["max_iterations"],
        )
        self.cancel_event = threading.Event()
        self.is_running = False
        self.created_at = time.time()
        # Token & Financial Cost Tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost_usd = 0.0


# Projects and Sessions storage
active_project_id = "proj_default"
projects_store: Dict[str, dict] = {
    "proj_default": {
        "id": "proj_default",
        "name": Path(app_settings["workspace_dir"]).name or "AI-ResearchAssistant",
        "path": app_settings["workspace_dir"],
        "created_at": time.time(),
    }
}

sessions: Dict[str, SessionState] = {}

# Create default session
default_session = SessionState("default", "General Task", DEFAULT_MODEL, project_id="proj_default")
sessions["default"] = default_session



# --- Data Models ---
class ChatRequest(BaseModel):
    session_id: Optional[str] = "default"
    prompt: str
    model: Optional[str] = None
    attachments: Optional[List[str]] = None


class AddModelRequest(BaseModel):
    name: str
    provider: str = "openai_compatible"  # "ollama" or "openai_compatible"
    base_url: str
    model_name: str
    api_key: Optional[str] = None
    input_cost_per_1m: float = 0.0
    output_cost_per_1m: float = 0.0


class CreateProjectRequest(BaseModel):
    name: str
    path: Optional[str] = None


class CreateSessionRequest(BaseModel):
    name: Optional[str] = "New Chat"
    model: Optional[str] = None
    project_id: Optional[str] = None


class WorkspaceRequest(BaseModel):
    path: str


class SettingsRequest(BaseModel):
    ollama_url: Optional[str] = None
    default_model: Optional[str] = None
    temperature: Optional[float] = None
    max_iterations: Optional[int] = None
    system_prompt: Optional[str] = None
    plan_mode_auto: Optional[bool] = None
    critic_enabled: Optional[bool] = None
    auto_flush_context: Optional[bool] = None
    context_window_size: Optional[int] = None
    top_p: Optional[float] = None


class VramUnloadRequest(BaseModel):
    model: Optional[str] = None


class VramSwapRequest(BaseModel):
    target_model: str
    session_id: Optional[str] = "default"


# --- Endpoints ---


@app.get("/api/status")
def get_status(session_id: str = "default"):
    session = sessions.get(session_id, default_session)
    unique_models = list({m["id"]: m for m in models_registry.values()}.values())
    tokens_used = session.context.get_token_estimate()
    tokens_max = get_model_context_limit(session.model)
    percent = round((tokens_used / tokens_max) * 100, 2)

    model_cfg = models_registry.get(session.model, {})
    vram_info = get_vram_status(app_settings["ollama_url"])

    return {
        "status": "online",
        "current_model": session.model,
        "available_models": [m["name"] for m in unique_models],
        "models_detailed": unique_models,
        "workspace": app_settings["workspace_dir"],
        "vram": vram_info,
        "checkpoints_count": len(checkpoint_manager.history),
        "active_plan": session.plan_tracker.get_summary(),
        "token_estimate": tokens_used,
        "token_max": tokens_max,
        "token_percent": percent,
        "is_running": session.is_running,
        "active_session": session.session_id,
        "sessions_count": len(sessions),
        "total_cost_usd": round(session.total_cost_usd, 6),
        "total_input_tokens": session.total_input_tokens,
        "total_output_tokens": session.total_output_tokens,
        "model_pricing": {
            "input_cost_per_1m": model_cfg.get("input_cost_per_1m", 0.0),
            "output_cost_per_1m": model_cfg.get("output_cost_per_1m", 0.0),
            "is_local": model_cfg.get("is_local", True),
        },
    }



# Projects Endpoints
@app.get("/api/projects")
def list_projects():
    res = []
    for p_id, p_data in projects_store.items():
        chat_count = sum(1 for s in sessions.values() if getattr(s, "project_id", "proj_default") == p_id)
        res.append({
            **p_data,
            "is_active": p_id == active_project_id,
            "chat_count": chat_count,
        })
    return {"projects": res, "active_project_id": active_project_id}


@app.post("/api/projects")
def create_project(req: CreateProjectRequest):
    global active_project_id
    proj_id = f"proj_{int(time.time() * 1000)}"
    path_str = req.path or str(Path(app_settings["workspace_dir"]) / req.name)
    target_path = Path(path_str)
    try:
        target_path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Cannot create folder: {str(e)}")

    project_data = {
        "id": proj_id,
        "name": req.name,
        "path": str(target_path),
        "created_at": time.time(),
    }
    projects_store[proj_id] = project_data

    # Create initial chat session for this project
    initial_chat = SessionState(
        f"chat_{int(time.time() * 1000)}",
        f"General Chat",
        app_settings["default_model"],
        project_id=proj_id,
    )
    sessions[initial_chat.session_id] = initial_chat

    # Switch active project
    active_project_id = proj_id
    app_settings["workspace_dir"] = str(target_path)
    checkpoint_manager.workspace_dir = target_path
    checkpoint_manager.checkpoints_dir = target_path / ".agent_checkpoints"
    checkpoint_manager.checkpoints_dir.mkdir(parents=True, exist_ok=True)

    return {
        "status": "success",
        "project": project_data,
        "initial_session": {
            "id": initial_chat.session_id,
            "name": initial_chat.name,
            "model": initial_chat.model,
            "project_id": proj_id,
        },
    }


@app.post("/api/projects/{proj_id}/activate")
def activate_project(proj_id: str):
    global active_project_id
    if proj_id not in projects_store:
        raise HTTPException(status_code=404, detail="Project not found")
    active_project_id = proj_id
    proj = projects_store[proj_id]
    target_path = Path(proj["path"])
    target_path.mkdir(parents=True, exist_ok=True)
    app_settings["workspace_dir"] = str(target_path)
    checkpoint_manager.workspace_dir = target_path
    checkpoint_manager.checkpoints_dir = target_path / ".agent_checkpoints"
    checkpoint_manager.checkpoints_dir.mkdir(parents=True, exist_ok=True)
    return {"status": "success", "active_project": proj}


@app.delete("/api/projects/{proj_id}")
def delete_project(proj_id: str):
    if proj_id == "proj_default":
        raise HTTPException(status_code=400, detail="Cannot delete default project")
    if proj_id in projects_store:
        del projects_store[proj_id]
        to_del = [sid for sid, s in sessions.items() if getattr(s, "project_id", "") == proj_id]
        for sid in to_del:
            del sessions[sid]
        return {"status": "success", "message": f"Project {proj_id} deleted"}
    return {"status": "error", "message": "Project not found"}


# Sessions endpoints
@app.get("/api/sessions")
def list_sessions(project_id: Optional[str] = None):
    res = []
    for s in sessions.values():
        p_id = getattr(s, "project_id", "proj_default")
        if project_id and p_id != project_id:
            continue
        res.append({
            "id": s.session_id,
            "name": s.name,
            "model": s.model,
            "project_id": p_id,
            "is_running": s.is_running,
            "tokens": s.context.get_token_estimate(),
            "created_at": s.created_at,
        })
    return {"sessions": res}


@app.post("/api/sessions")
def create_session(req: CreateSessionRequest):
    sess_id = f"chat_{int(time.time() * 1000)}"
    model = req.model or app_settings["default_model"]
    p_id = req.project_id or active_project_id
    sess = SessionState(sess_id, req.name or "New Chat", model, project_id=p_id)
    sessions[sess_id] = sess
    return {
        "status": "success",
        "session": {
            "id": sess.session_id,
            "name": sess.name,
            "model": sess.model,
            "project_id": p_id,
        },
    }


@app.delete("/api/sessions/{session_id}")
def delete_session(session_id: str):
    if session_id in sessions and session_id != "default":
        del sessions[session_id]
        return {"status": "success", "message": f"Session {session_id} deleted"}
    return {"status": "error", "message": "Cannot delete default session"}


@app.post("/api/sessions/{session_id}/cancel")
def cancel_task(session_id: str):
    sess = sessions.get(session_id)
    if sess:
        sess.cancel_event.set()
        return {"status": "success", "message": "Task cancellation requested"}
    return {"status": "error", "message": "Session not found"}



# Workspace switcher
@app.get("/api/workspace")
def get_workspace():
    return {"workspace": app_settings["workspace_dir"]}


@app.post("/api/workspace")
def set_workspace(req: WorkspaceRequest):
    new_path = Path(req.path)
    if not new_path.exists() or not new_path.is_dir():
        raise HTTPException(status_code=400, detail="Invalid directory path")
    app_settings["workspace_dir"] = str(new_path)
    checkpoint_manager.workspace_dir = new_path
    checkpoint_manager.checkpoints_dir = new_path / ".agent_checkpoints"
    checkpoint_manager.checkpoints_dir.mkdir(parents=True, exist_ok=True)
    return {"status": "success", "workspace": app_settings["workspace_dir"]}


# Settings endpoints
@app.get("/api/settings")
def get_settings():
    return app_settings


@app.post("/api/settings")
def update_settings(req: SettingsRequest):
    if req.ollama_url is not None:
        app_settings["ollama_url"] = req.ollama_url
    if req.default_model is not None:
        app_settings["default_model"] = req.default_model
    if req.temperature is not None:
        app_settings["temperature"] = req.temperature
    if req.max_iterations is not None:
        app_settings["max_iterations"] = req.max_iterations
    if req.system_prompt is not None:
        app_settings["system_prompt"] = req.system_prompt
    if req.plan_mode_auto is not None:
        app_settings["plan_mode_auto"] = req.plan_mode_auto
    if req.critic_enabled is not None:
        app_settings["critic_enabled"] = req.critic_enabled
    if req.auto_flush_context is not None:
        app_settings["auto_flush_context"] = req.auto_flush_context
    if req.context_window_size is not None:
        app_settings["context_window_size"] = req.context_window_size
    if req.top_p is not None:
        app_settings["top_p"] = req.top_p

    # Update in existing sessions
    for s in sessions.values():
        s.llm_client.base_url = app_settings["ollama_url"]
        s.agent.max_iterations = app_settings["max_iterations"]

    return {"status": "success", "settings": app_settings}



# File & Image Upload endpoint
@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Uploads file or image into workspace/uploads/ folder"""
    upload_dir = Path(app_settings["workspace_dir"]) / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)

    safe_name = Path(file.filename or "upload.bin").name
    dest_path = upload_dir / safe_name

    # Write file content
    content = await file.read()
    dest_path.write_bytes(content)

    ext = dest_path.suffix.lower()
    is_image = ext in (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp")
    rel_path = str(dest_path.relative_to(Path(app_settings["workspace_dir"])))

    # If it's a PDF or text file, extract preview text
    extracted_text = ""
    if ext == ".pdf":
        try:
            import pymupdf
            doc = pymupdf.open(dest_path)
            extracted_text = "\n".join([page.get_text() for page in doc[:3]])[:4000]
            doc.close()
        except Exception:
            pass
    elif ext in (".txt", ".md", ".py", ".json", ".csv", ".tex", ".js", ".ts"):
        try:
            extracted_text = content.decode("utf-8", errors="replace")[:4000]
        except Exception:
            pass

    return {
        "status": "success",
        "file_name": safe_name,
        "path": rel_path,
        "is_image": is_image,
        "size": len(content),
        "preview_text": extracted_text,
    }


# Model & API Providers Operations
@app.get("/api/models")
def list_models():
    unique_models = list({m["id"]: m for m in models_registry.values()}.values())
    return {
        "current": default_session.model,
        "models": unique_models,
    }



@app.post("/api/models/scan")
def scan_local_models():
    """Scans local Ollama (11434), LM Studio (1234), vLLM (8000), LocalAI (8080)"""
    discovered = detect_local_providers()
    added_count = 0
    for m in discovered:
        if m.id not in models_registry and m.model_name not in models_registry:
            models_registry[m.id] = m.to_dict()
            # Also register by short model_name for easy lookup
            models_registry[m.model_name] = m.to_dict()
            added_count += 1
    unique_models = list({m["id"]: m for m in models_registry.values()}.values())
    return {
        "status": "success",
        "added_count": added_count,
        "total_models": len(unique_models),
        "models": unique_models,
    }


@app.post("/api/models")
def add_custom_model(req: AddModelRequest):
    model_id = f"custom_{int(time.time() * 1000)}"
    is_local = req.base_url.startswith("http://127.0.0.1") or req.base_url.startswith("http://localhost")
    entry = {
        "id": model_id,
        "name": req.name,
        "provider": req.provider,
        "base_url": req.base_url.rstrip("/"),
        "model_name": req.model_name,
        "api_key": req.api_key,
        "input_cost_per_1m": req.input_cost_per_1m,
        "output_cost_per_1m": req.output_cost_per_1m,
        "is_local": is_local,
    }
    models_registry[model_id] = entry
    models_registry[req.model_name] = entry
    return {"status": "success", "model": entry}


@app.delete("/api/models/{model_id}")
def delete_model(model_id: str):
    to_delete = [k for k, v in models_registry.items() if v.get("id") == model_id or k == model_id]
    if to_delete:
        for k in to_delete:
            models_registry.pop(k, None)
        return {"status": "success", "message": f"Model {model_id} removed"}
    return {"status": "error", "message": "Model not found"}


@app.get("/api/vram/status")
def get_vram_endpoint():
    return get_vram_status(app_settings["ollama_url"])


@app.post("/api/vram/unload")
def unload_vram_endpoint(req: Optional[VramUnloadRequest] = None):
    model_name = req.model if req and req.model else None
    if model_name:
        ok = unload_model_from_vram(model_name, app_settings["ollama_url"])
        return {"status": "success" if ok else "error", "unloaded": model_name}
    else:
        unloaded = unload_all_other_models("", app_settings["ollama_url"])
        return {"status": "success", "unloaded_models": unloaded}


@app.post("/api/vram/swap")
def swap_vram_endpoint(req: VramSwapRequest):
    sess = sessions.get(req.session_id or "default", default_session)
    cfg = models_registry.get(req.target_model, {})
    url = cfg.get("base_url", app_settings["ollama_url"])
    model_name = cfg.get("model_name", req.target_model)
    res = swap_and_ensure_vram(model_name, ollama_url=url)
    sess.model = req.target_model
    sess.llm_client = get_llm_client_for_model(req.target_model)
    sess.agent.llm = sess.llm_client
    return res


@app.post("/api/model/select")
def select_model(model: str = Form(...), session_id: str = Form("default")):
    sess = sessions.get(session_id, default_session)
    sess.model = model
    sess.llm_client = get_llm_client_for_model(model)
    sess.agent.llm = sess.llm_client

    # Check if target model is from Ollama and swap VRAM in a daemon thread so request is fast
    cfg = models_registry.get(model, {})
    provider = cfg.get("provider", "ollama")
    if provider == "ollama":
        target_name = cfg.get("model_name", model)
        base_url = cfg.get("base_url", app_settings["ollama_url"])
        threading.Thread(
            target=swap_and_ensure_vram,
            args=(target_name, base_url),
            daemon=True,
        ).start()

    return {"status": "success", "session_id": sess.session_id, "current_model": sess.model}



@app.get("/api/checkpoints")
def list_checkpoints():
    return {"checkpoints": checkpoint_manager.list_checkpoints()}


@app.post("/api/undo")
def trigger_undo():
    res = checkpoint_manager.undo()
    return {"status": "success", "message": res}


@app.post("/api/clear")
def clear_context(session_id: str = Query("default")):
    sess = sessions.get(session_id, default_session)
    sess.context.reset()
    sess.plan_tracker = PlanTracker()
    return {"status": "success", "message": f"Context reset for session '{sess.name}'"}


@app.get("/api/plan")
def get_plan(session_id: str = Query("default")):
    sess = sessions.get(session_id, default_session)
    return {
        "steps": sess.plan_tracker.steps,
        "current_step": sess.plan_tracker.current_step,
        "notes": sess.plan_tracker.notes,
        "summary": sess.plan_tracker.get_summary(),
    }


@app.get("/api/files")
def get_workspace_files():
    ws = Path(app_settings["workspace_dir"])
    ignore_dirs = {".git", ".venv", "__pycache__", "node_modules", ".next", ".agent_checkpoints"}

    def scan_dir(path: Path) -> List[Dict[str, Any]]:
        items = []
        try:
            for entry in sorted(path.iterdir(), key=lambda e: e.name.lower()):
                if entry.name in ignore_dirs or entry.name.startswith("."):
                    continue
                # Only include directories (projects and folders)
                if entry.is_dir():
                    items.append({
                        "name": entry.name,
                        "path": str(entry.relative_to(ws)),
                        "type": "directory",
                        "children": scan_dir(entry) if len(entry.parts) - len(ws.parts) < 4 else [],
                    })
        except Exception:
            pass
        return items

    return {"files": scan_dir(ws)}


@app.get("/api/memory")
def get_memory():
    from agent.memory import memory_ledger
    return {
        "raw": memory_ledger.data,
        "formatted": memory_ledger.format_for_context(),
    }


@app.get("/api/literature")
def get_literature():
    ws = Path(app_settings["workspace_dir"])
    papers_dir = ws / "outputs" / "papers"
    papers = []
    if papers_dir.exists():
        for p in sorted(papers_dir.glob("*.pdf"), key=lambda f: -f.stat().st_mtime):
            papers.append({
                "name": p.name,
                "path": str(p.relative_to(ws)),
                "size": p.stat().st_size,
                "modified": p.stat().st_mtime,
            })

    # BibTeX references
    bib_file = ws / "references.bib"
    references = []
    if bib_file.exists():
        try:
            content = bib_file.read_text(encoding="utf-8", errors="replace")
            keys = re.findall(r"@(\w+)\s*\{\s*([^,]+),", content)
            for entry_type, key in keys:
                title_m = re.search(rf"@\w+\s*\{{\s*{re.escape(key)},.*?(?:title\s*=\s*[\"{{](.*?)[\"\}}])", content, re.DOTALL | re.IGNORECASE)
                year_m = re.search(rf"@\w+\s*\{{\s*{re.escape(key)},.*?(?:year\s*=\s*[\"{{]?(\d{{4}}))", content, re.DOTALL | re.IGNORECASE)
                references.append({
                    "type": entry_type,
                    "key": key.strip(),
                    "title": title_m.group(1).replace("\n", " ").strip() if title_m else "Untitled Entry",
                    "year": year_m.group(1) if year_m else "",
                })
        except Exception:
            pass

    # LaTeX drafts
    latex_drafts = []
    for tf in sorted(ws.rglob("*.tex"), key=lambda f: -f.stat().st_mtime):
        rel = str(tf.relative_to(ws))
        if any(ign in rel for ign in [".venv", "node_modules", ".next"]):
            continue
        latex_drafts.append({
            "name": tf.name,
            "path": rel,
            "size": tf.stat().st_size,
        })

    return {
        "papers": papers,
        "references": references,
        "latex_drafts": latex_drafts[:30],
    }


@app.get("/api/file/content")
def get_file_content(path: str = Query(...)):
    ws = Path(app_settings["workspace_dir"])
    target_path = Path(path)
    if not target_path.is_absolute():
        target_path = ws / target_path

    if not target_path.exists() or target_path.is_dir():
        raise HTTPException(status_code=404, detail="File not found")

    try:
        with open(target_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return {"path": path, "content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/file/raw")
def get_file_raw(path: str = Query(...)):
    ws = Path(app_settings["workspace_dir"])
    target_path = Path(path)
    if not target_path.is_absolute():
        target_path = ws / target_path

    if not target_path.exists() or target_path.is_dir():
        raise HTTPException(status_code=404, detail="File not found")

    suffix = target_path.suffix.lower()
    media_types = {
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".svg": "image/svg+xml",
        ".html": "text/html",
        ".txt": "text/plain",
        ".tex": "text/plain",
    }
    media_type = media_types.get(suffix, "application/octet-stream")
    return FileResponse(target_path, media_type=media_type, filename=target_path.name)


class SaveFileRequest(BaseModel):
    path: str
    content: str


@app.post("/api/file/save")
def save_file_endpoint(req: SaveFileRequest):
    ws = Path(app_settings["workspace_dir"])
    target_path = Path(req.path)
    if not target_path.is_absolute():
        target_path = ws / target_path

    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(req.content)
        return {"status": "success", "path": str(target_path)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class LatexCompileRequest(BaseModel):
    tex_path: str
    output_dir: Optional[str] = None


@app.post("/api/latex/compile")
def compile_latex_endpoint(req: LatexCompileRequest):
    from agent.tools.research_tools import compile_latex
    result = compile_latex(req.tex_path, req.output_dir or "")
    return result


@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    """
    SSE Streaming Endpoint for ReAct Agent loop.
    Emits events: thinking_chunk, content_chunk, thinking, tool_call, tool_result, message, done, error.
    """
    session = sessions.get(req.session_id or "default")
    if not session:
        session = default_session

    if req.model and req.model != session.model:
        session.model = req.model
        session.llm_client = get_llm_client_for_model(req.model)
        session.agent.llm = session.llm_client

    session.cancel_event.clear()
    session.is_running = True

    # If attachments are present, enrich the prompt
    final_prompt = req.prompt
    if req.attachments and len(req.attachments) > 0:
        att_lines = ["\n\n[Attached Files in Workspace]:"]
        for att in req.attachments:
            att_lines.append(f"- {att}")
        final_prompt += "\n".join(att_lines)

    def event_stream():
        q = queue.Queue()

        def on_thinking(th: str):
            q.put({"type": "thinking", "data": th})

        def on_thinking_chunk(chunk: str):
            q.put({"type": "thinking_chunk", "data": chunk})

        def on_content_chunk(chunk: str):
            q.put({"type": "content_chunk", "data": chunk})

        def on_tool_call(name: str, args: dict):
            q.put({"type": "tool_call", "name": name, "args": args})

        def on_tool_result(name: str, result: str):
            q.put({"type": "tool_result", "name": name, "result": result[:2000]})

        def on_message(final_msg: str):
            q.put({"type": "message", "data": final_msg})

        def on_progress(text: str):
            q.put({"type": "progress", "text": text})

        def on_cost_update(cost_data: dict):
            session.total_input_tokens += cost_data.get("prompt_tokens", 0)
            session.total_output_tokens += cost_data.get("completion_tokens", 0)
            session.total_cost_usd += cost_data.get("cost_usd", 0.0)
            q.put({
                "type": "cost_update",
                "step_tokens": cost_data.get("total_tokens", 0),
                "step_cost": cost_data.get("cost_usd", 0.0),
                "total_input_tokens": session.total_input_tokens,
                "total_output_tokens": session.total_output_tokens,
                "total_cost_usd": round(session.total_cost_usd, 6),
            })

        def worker():
            from agent.orchestrator import is_macro_task, generate_blueprint_plan, ProjectBlueprint
            from agent.critic import evaluate_alignment_and_drift

            try:
                # 0. Auto-Swap VRAM for Ollama: evicts other models and loads target model into VRAM
                cfg = models_registry.get(session.model) or models_registry.get(f"ollama:{session.model}") or {}
                provider = cfg.get("provider", "ollama")
                if provider == "ollama":
                    target_name = cfg.get("model_name", session.model)
                    base_url = cfg.get("base_url", app_settings["ollama_url"])

                    def on_vram_status(txt: str):
                        q.put({"type": "vram_status", "text": txt})

                    try:
                        swap_res = swap_and_ensure_vram(
                            target_model=target_name,
                            ollama_url=base_url,
                            on_status=on_vram_status,
                        )
                        q.put({"type": "vram_ready", "data": swap_res})
                    except Exception as ex:
                        pass

                # Check if this is an explicit macro-task plan request
                if is_macro_task(final_prompt):
                    q.put({"type": "mode_status", "mode": "Reja Asosida (Plan Mode)", "active": True})
                    on_progress("📋 Ko'p bosqichli ilmiy reja shakllantirilmoqda...")

                    # 1. Generate master blueprint
                    steps = generate_blueprint_plan(session.llm_client, final_prompt)
                    blueprint = ProjectBlueprint(goal=final_prompt, steps=steps, workspace_dir=Path(app_settings["workspace_dir"]))

                    q.put({"type": "blueprint_created", "data": [s.to_dict() for s in steps]})
                    on_content_chunk("📋 **Ilmiy Tadqiqot Rejasi:**\n\n")
                    for s in steps:
                        on_content_chunk(f"- **{s.step_id}-qadam**: {s.title} (`{s.target_file}`)\n")
                    on_content_chunk("\n---\n")

                    # 2. Autonomous Recursive Step Execution (Self-Chaining & Self-Wakeup)
                    for i, step in enumerate(steps):
                        if session.cancel_event.is_set():
                            q.put({"type": "message", "data": "⏹️ Loyiha foydalanuvchi tomonidan to'xtatildi."})
                            break

                        step.status = "in_progress"
                        blueprint.current_step_index = i + 1
                        blueprint.save()
                        q.put({"type": "step_start", "step": step.to_dict()})
                        on_progress(f"🚀 Bosqich {step.step_id}/{len(steps)}: {step.title}...")
                        on_content_chunk(f"\n\n### 🔬 {step.step_id}-Bosqich: {step.title}\n")

                        step_prompt = (
                            f"We are executing Step {step.step_id}/{len(steps)} of research project: '{step.title}'. "
                            f"Objective: {step.description}. Target output file: '{step.target_file}'. "
                            "Execute necessary tools (e.g. search_arxiv, search_web, fetch_web_page, download_and_extract_paper, "
                            "manage_bibtex, write_file, compile_latex), write rigorous academic content, and verify results."
                        )

                        step_result = session.agent.run(
                            user_prompt=step_prompt,
                            on_thinking=on_thinking,
                            on_thinking_chunk=on_thinking_chunk,
                            on_content_chunk=on_content_chunk,
                            on_tool_call=on_tool_call,
                            on_tool_result=on_tool_result,
                            on_cost_update=on_cost_update,
                            on_progress=on_progress,
                            cancel_event=session.cancel_event,
                        )

                        # 3. LLM Self-Critic & Goal Drift Audit
                        audit = evaluate_alignment_and_drift(
                            llm=session.llm_client,
                            master_goal=final_prompt,
                            step_objective=step.title,
                            step_output=step_result,
                        )

                        step.alignment_score = audit.get("alignment_score", 90)
                        step.quality_score = audit.get("quality_score", 90)
                        step.status = "completed"
                        blueprint.save()

                        # Emit audit and step completion
                        q.put({"type": "alignment_audit", "step_id": step.step_id, "audit": audit})
                        q.put({
                            "type": "step_complete",
                            "step": step.to_dict(),
                            "next_step": step.step_id + 1 if step.step_id < len(steps) else None,
                        })

                        # Sleep briefly to yield queue cleanly
                        time.sleep(0.5)

                    if not session.cancel_event.is_set():
                        q.put({
                            "type": "message",
                            "data": f"🎉 **Loyiha to'liq yakunlandi!** Barcha {len(steps)} ta bosqich muvaffaqiyatli bajarildi, sifat tekshirildi va `project_blueprint.json` ga saqlandi.",
                        })

                else:
                    # Standard Single-Task Execution
                    q.put({"type": "mode_status", "mode": "Avtonom Tadqiqotchi (ReAct)", "active": True})
                    session.agent.run(
                        user_prompt=final_prompt,
                        on_thinking=on_thinking,
                        on_thinking_chunk=on_thinking_chunk,
                        on_content_chunk=on_content_chunk,
                        on_tool_call=on_tool_call,
                        on_tool_result=on_tool_result,
                        on_message=on_message,
                        on_cost_update=on_cost_update,
                        on_progress=on_progress,
                        cancel_event=session.cancel_event,
                    )


            except Exception as e:
                q.put({"type": "error", "data": str(e)})
            finally:
                session.is_running = False
                q.put({"type": "done"})

        t = threading.Thread(target=worker, daemon=True)
        t.start()

        while True:
            item = q.get()
            event_type = item.get("type")
            yield f"event: {event_type}\ndata: {json.dumps(item)}\n\n"
            if event_type in ("done", "error"):
                break

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/api/blueprint")
def get_blueprint():
    from agent.orchestrator import ProjectBlueprint
    bp = ProjectBlueprint.load(Path(app_settings["workspace_dir"]))
    if not bp:
        return {"status": "none", "blueprint": None}
    return {
        "status": "active",
        "blueprint": {
            "goal": bp.goal,
            "current_step_index": bp.current_step_index,
            "total_steps": len(bp.steps),
            "steps": [s.to_dict() for s in bp.steps],
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("agent.server:app", host="127.0.0.1", port=8765, reload=True)
