"""
/api/ollama/models  —  list available models from the active backend
"""
from fastapi import APIRouter, HTTPException
import requests as req

router = APIRouter()


@router.get("/ollama/models")
async def get_models():
    """List models from the active backend (Ollama or OpenAI-compatible)."""
    try:
        from config import Config  # noqa: PLC0415
        backend = getattr(Config, "BACKEND_TYPE", "ollama")
    except ImportError:
        backend = "ollama"

    if backend == "api":
        return await _list_openai_models()
    return await _list_ollama_models()


async def _list_ollama_models():
    try:
        from config import Config  # noqa: PLC0415
        base_url = Config.OLLAMA_BASE_URL
    except ImportError:
        base_url = "http://localhost:11434"

    try:
        r = req.get(f"{base_url}/api/tags", timeout=5)
        r.raise_for_status()
        models = [m["name"] for m in r.json().get("models", [])]
        return {"models": models}
    except req.exceptions.ConnectionError:
        raise HTTPException(status_code=503, detail="Cannot reach Ollama. Is it running?")
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Ollama error: {exc}")


async def _list_openai_models():
    try:
        from config import Config  # noqa: PLC0415
        api_url = getattr(Config, "API_URL", "http://127.0.0.1:1234").rstrip("/")
        api_key = getattr(Config, "API_KEY", "")
    except ImportError:
        api_url = "http://127.0.0.1:1234"
        api_key = ""

    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        r = req.get(f"{api_url}/v1/models", headers=headers, timeout=5)
        r.raise_for_status()
        data = r.json()
        items = data.get("data") or data.get("models") or []
        models = [m.get("id") or m.get("name", "") for m in items if isinstance(m, dict)]
        return {"models": [m for m in models if m]}
    except req.exceptions.ConnectionError:
        raise HTTPException(status_code=503, detail="Cannot reach API server. Is it running?")
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"API error: {exc}")

