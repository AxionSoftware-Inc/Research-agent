"""
VRAM Management & Model Swapper for Local LLM Instances (Ollama).
Provides:
- Real-time VRAM monitoring (/api/ps)
- Instant eviction/unloading of models from VRAM (keep_alive: 0)
- Auto-swapping: unloads old models before loading new target models to prevent OOM
- Preloading / Warming up models into VRAM before execution
"""
import logging
from typing import Any, Callable, Dict, List, Optional
import httpx

logger = logging.getLogger(__name__)


def get_vram_status(ollama_url: str = "http://127.0.0.1:11434") -> Dict[str, Any]:
    """Returns models currently residing in VRAM/RAM with sizes."""
    try:
        with httpx.Client(timeout=3.0) as client:
            resp = client.get(f"{ollama_url.rstrip('/')}/api/ps")
            if resp.status_code == 200:
                data = resp.json()
                loaded = []
                total_vram_bytes = 0
                for m in data.get("models", []):
                    vram_b = m.get("size_vram", 0)
                    total_vram_bytes += vram_b
                    loaded.append({
                        "name": m.get("name", ""),
                        "model": m.get("model", ""),
                        "size_gb": round(m.get("size", 0) / (1024**3), 2),
                        "size_vram_gb": round(vram_b / (1024**3), 2),
                        "expires_at": m.get("expires_at"),
                    })
                return {
                    "online": True,
                    "models": loaded,
                    "total_vram_gb": round(total_vram_bytes / (1024**3), 2),
                    "count": len(loaded),
                }
    except Exception as e:
        logger.debug(f"Failed to fetch VRAM status: {e}")
    return {"online": False, "models": [], "total_vram_gb": 0.0, "count": 0}


def unload_model_from_vram(model_name: str, ollama_url: str = "http://127.0.0.1:11434") -> bool:
    """Evicts a specific model from VRAM immediately using keep_alive: 0."""
    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(
                f"{ollama_url.rstrip('/')}/api/generate",
                json={"model": model_name, "keep_alive": 0},
            )
            return resp.status_code == 200
    except Exception as e:
        logger.error(f"Error unloading model {model_name} from VRAM: {e}")
        return False


def clean_ollama_name(model_name: str) -> str:
    """Strips 'ollama:' prefix if present and returns clean model tag for Ollama API."""
    if not model_name:
        return ""
    if model_name.startswith("ollama:"):
        return model_name[len("ollama:"):]
    return model_name


def unload_all_other_models(
    target_model: str,
    ollama_url: str = "http://127.0.0.1:11434",
    on_status: Optional[Callable[[str], None]] = None,
) -> List[str]:
    """
    Checks VRAM. If any models other than target_model are loaded,
    unloads them immediately to free VRAM for the target model.
    """
    status = get_vram_status(ollama_url)
    unloaded = []
    target = clean_ollama_name(target_model)
    target_base = target.split(":")[0]

    for m in status.get("models", []):
        m_name = clean_ollama_name(m.get("name", ""))
        m_base = m_name.split(":")[0]
        if m_name != target and m_base != target_base:
            if on_status:
                on_status(f"[VRAM] Bo'shatilmoqda: '{m_name}' xotiradan chiqarilmoqda...")
            logger.info(f"Evicting '{m_name}' from VRAM to make room for '{target}'")
            success = unload_model_from_vram(m_name, ollama_url)
            if success:
                unloaded.append(m_name)
    return unloaded


def preload_model_into_vram(
    model_name: str,
    keep_alive: Any = -1,
    ollama_url: str = "http://127.0.0.1:11434",
    timeout: float = 120.0,
    on_status: Optional[Callable[[str], None]] = None,
) -> bool:
    """Preloads / warms up a model into GPU VRAM."""
    target = clean_ollama_name(model_name)
    if on_status:
        on_status(f"[VRAM] Joylashtirilmoqda: '{target}' VRAMga yuklanmoqda...")
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(
                f"{ollama_url.rstrip('/')}/api/generate",
                json={"model": target, "keep_alive": keep_alive},
            )
            return resp.status_code == 200
    except Exception as e:
        logger.error(f"Error preloading model {target} into VRAM: {e}")
        return False


def swap_and_ensure_vram(
    target_model: str,
    ollama_url: str = "http://127.0.0.1:11434",
    keep_alive: Any = -1,
    on_status: Optional[Callable[[str], None]] = None,
) -> Dict[str, Any]:
    """
    Complete VRAM swap pipeline:
    1. Unload all models currently occupying VRAM that are not target_model
    2. Check if target_model is already loaded in VRAM
    3. If not, preload target_model into VRAM
    """
    target = clean_ollama_name(target_model)
    unloaded = unload_all_other_models(target, ollama_url, on_status=on_status)

    # Check if target is already in VRAM
    status = get_vram_status(ollama_url)
    target_base = target.split(":")[0]
    already_loaded = any(
        clean_ollama_name(m.get("name", "")) == target
        or clean_ollama_name(m.get("name", "")).split(":")[0] == target_base
        for m in status.get("models", [])
    )

    if not already_loaded:
        ok = preload_model_into_vram(
            target,
            keep_alive=keep_alive,
            ollama_url=ollama_url,
            on_status=on_status,
        )
        if on_status and ok:
            on_status(f"[VRAM] Tayyor: '{target}' VRAMga joylashtirildi!")
    else:
        if on_status:
            on_status(f"[VRAM] Faol: '{target}' allaqachon VRAMda tayyor!")

    final_status = get_vram_status(ollama_url)
    return {
        "status": "ready",
        "target_model": target,
        "unloaded_models": unloaded,
        "vram_info": final_status,
    }
