"""
/api/status  —  system health check
/api/prereqs/install  —  install missing deps
"""
import subprocess
import sys

import requests as req
from fastapi import APIRouter

router = APIRouter()

_REQUIRED_PACKAGES = ["fastapi", "uvicorn", "requests", "sse_starlette"]


@router.get("/status")
async def get_status():
    """Return Ollama reachability and Python dependency status."""
    # Ollama check
    ollama_ok = False
    try:
        from config import Config  # noqa: PLC0415
        r = req.get(f"{Config.OLLAMA_BASE_URL}/api/tags", timeout=3)
        ollama_ok = r.status_code == 200
    except Exception:
        # Try default URL if Config not yet loaded
        try:
            r = req.get("http://localhost:11434/api/tags", timeout=3)
            ollama_ok = r.status_code == 200
        except Exception:
            pass

    # Python deps check
    deps_ok = True
    missing = []
    for pkg in _REQUIRED_PACKAGES:
        try:
            __import__(pkg)
        except ImportError:
            deps_ok = False
            missing.append(pkg)

    return {"ollama": ollama_ok, "deps": deps_ok, "missing_packages": missing}


@router.post("/prereqs/install")
async def install_prereqs():
    """Install missing Python dependencies into the current venv."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "fastapi",
            "uvicorn[standard]",
            "requests",
            "sse-starlette",
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    return {
        "success": result.returncode == 0,
        "output": (result.stdout + result.stderr)[-3000:],
    }
