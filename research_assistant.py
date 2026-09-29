import base64
import os
from pathlib import Path

import fitz
import httpx
from fastapi import FastAPI, File, Form, UploadFile


ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT / "workspace"
OUTPUTS = ROOT / "outputs"
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
VLM_MODEL = os.getenv("VLM_MODEL", "qwen3.5-35b-a3b-vlm-q4")

WORKSPACE.mkdir(exist_ok=True)
OUTPUTS.mkdir(exist_ok=True)
app = FastAPI(title="Local AI Research Assistant", version="0.1.0")


def page_image(page: fitz.Page) -> str:
    pix = page.get_pixmap(matrix=fitz.Matrix(2.2, 2.2), alpha=False)
    return base64.b64encode(pix.tobytes("png")).decode("ascii")


async def ask_vlm(prompt: str, image_b64: str) -> str:
    payload = {
        "model": VLM_MODEL,
        "stream": False,
        "messages": [{
            "role": "user",
            "content": prompt,
            "images": [image_b64],
        }],
        "options": {"temperature": 0.1},
    }
    async with httpx.AsyncClient(timeout=600) as client:
        response = await client.post(f"{OLLAMA_URL}/api/chat", json=payload)
        response.raise_for_status()
        return response.json()["message"]["content"]


@app.get("/health")
async def health():
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{OLLAMA_URL}/api/tags")
            response.raise_for_status()
        models = [item.get("name", "") for item in response.json().get("models", [])]
        available = any(name == VLM_MODEL or name.startswith(f"{VLM_MODEL}:") for name in models)
        return {"ok": available, "ollama": True, "vlm_model": VLM_MODEL, "model_available": available, "models": models}
    except Exception as exc:
        return {"ok": False, "ollama": False, "vlm_model": VLM_MODEL, "model_available": False, "error": str(exc)}


@app.post("/analyze")
async def analyze_pdf(
    file: UploadFile = File(...),
    instruction: str = Form(
        "Convert this scientific page into faithful Markdown and LaTeX. "
        "Understand the formula semantically; do not guess missing symbols. "
        "Preserve headings, tables, equation numbering, units, and references. "
        "Return the result in Markdown, then a short list of uncertainties."
    ),
    max_pages: int = Form(4),
):
    safe_name = Path(file.filename or "document.pdf").name
    pdf_path = WORKSPACE / safe_name
    pdf_path.write_bytes(await file.read())
    document = fitz.open(pdf_path)
    results = []
    for index in range(min(max_pages, len(document))):
        page = document[index]
        native_text = page.get_text("text")
        prompt = (
            f"Page {index + 1} of {len(document)}.\n\n{instruction}\n\n"
            "Use the page image as the source of truth. The following selectable PDF text "
            "is context only and may be incomplete:\n" + native_text[:12000]
        )
        try:
            content = await ask_vlm(prompt, page_image(page))
        except Exception as exc:
            content = f"[VLM error on page {index + 1}: {exc}]"
        results.append({"page": index + 1, "native_text": native_text, "result": content})
    document.close()
    return {"file": safe_name, "pages": results, "model": VLM_MODEL}
