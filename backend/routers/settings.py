"""
/api/settings  —  get and update per-project configuration
"""
from typing import Optional, Union

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import backend.state as state
from backend.config_manager import get_current_config, save_override, apply_config

router = APIRouter()


class SettingsBody(BaseModel):
    BACKEND_TYPE: Optional[str] = None
    OLLAMA_BASE_URL: Optional[str] = None
    DEFAULT_MODEL: Optional[str] = None
    CONTEXT_LENGTH_SIZE: Optional[int] = None
    THINK_MODE: Optional[Union[str, bool]] = None
    API_URL: Optional[str] = None
    API_KEY: Optional[str] = None
    API_MODEL: Optional[str] = None
    DEBUG_MODE: Optional[bool] = None
    NOVEL_VIEWPOINT: Optional[str] = None
    NOVEL_STYLE: Optional[str] = None
    MAX_CONTEXT_CHARS: Optional[int] = None
    NOVEL_LANGUAGE: Optional[str] = None


@router.get("/settings")
def get_settings():
    """Return current effective configuration plus the active project path."""
    return {
        **get_current_config(),
        "project_path": state.current_project_path,
    }


@router.post("/settings")
def update_settings(body: SettingsBody):
    """
    Persist settings to the project's config_override.json and apply them.
    Global-only fields (DEBUG_MODE) are applied to Config even without a project.
    """
    project = state.current_project_path

    # Only save fields that were explicitly provided (non-None)
    data = {k: v for k, v in body.dict().items() if v is not None}
    if not data:
        raise HTTPException(status_code=400, detail="No settings provided.")

    # DEBUG_MODE can always be applied in-memory (no project needed)
    if "DEBUG_MODE" in data and not project:
        from config import Config  # noqa: PLC0415
        Config.DEBUG_MODE = bool(data["DEBUG_MODE"])
        return {"success": True, "saved": {"DEBUG_MODE": data["DEBUG_MODE"]}, "config": get_current_config()}

    if not project:
        raise HTTPException(
            status_code=400,
            detail="No project loaded. Settings are saved per-project.",
        )

    save_override(project, data)
    apply_config(project)

    return {"success": True, "saved": data, "config": get_current_config()}
