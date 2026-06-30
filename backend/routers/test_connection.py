"""
/api/test-connection  —  probe the currently configured LLM backend.

Returns:
  { "status": "ok" | "warn" | "error", "message": str, "models": list[str] }
"""
import requests as req
from fastapi import APIRouter

router = APIRouter()


@router.post("/test-connection")
async def test_connection():
    """Test connectivity to the active LLM backend (Ollama or OpenAI-compatible)."""
    try:
        from config import Config  # noqa: PLC0415
        backend = getattr(Config, "BACKEND_TYPE", "ollama")
    except ImportError:
        backend = "ollama"

    if backend == "api":
        return await _test_openai()
    return await _test_ollama()


async def _test_ollama():
    try:
        from config import Config  # noqa: PLC0415
        base_url = Config.OLLAMA_BASE_URL
    except ImportError:
        base_url = "http://localhost:11434"

    try:
        r = req.get(f"{base_url}/api/tags", timeout=5)
        if r.status_code == 200:
            models = [m["name"] for m in r.json().get("models", [])]
            n = len(models)
            return {
                "status": "ok",
                "message": f"Ollama is running — {n} model{'s' if n != 1 else ''} available.",
                "models": models,
            }
        return {
            "status": "warn",
            "message": f"Ollama responded with HTTP {r.status_code}.",
            "models": [],
        }
    except req.exceptions.ConnectionError:
        return {
            "status": "error",
            "message": "Cannot connect to Ollama. Make sure it is installed and running.",
            "models": [],
        }
    except req.exceptions.Timeout:
        return {"status": "warn", "message": "Ollama connection timed out.", "models": []}
    except Exception as exc:
        return {"status": "error", "message": str(exc), "models": []}


async def _test_openai():
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
        if r.status_code == 200:
            data = r.json()
            # OpenAI-compat /v1/models returns {"data": [...]} or {"models": [...]}
            items = data.get("data") or data.get("models") or []
            models = [m.get("id") or m.get("name", "") for m in items if isinstance(m, dict)]
            models = [m for m in models if m]
            n = len(models)
            return {
                "status": "ok",
                "message": f"Connected — {n} model{'s' if n != 1 else ''} available.",
                "models": models,
            }
        if r.status_code == 401:
            return {"status": "warn", "message": "Connected but authentication failed (check API key).", "models": []}
        return {
            "status": "warn",
            "message": f"Server responded with HTTP {r.status_code}.",
            "models": [],
        }
    except req.exceptions.ConnectionError:
        return {
            "status": "error",
            "message": "Cannot connect to the API server. Check the URL and make sure it is running.",
            "models": [],
        }
    except req.exceptions.Timeout:
        return {"status": "warn", "message": "Connection timed out.", "models": []}
    except Exception as exc:
        return {"status": "error", "message": str(exc), "models": []}
