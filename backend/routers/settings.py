"""
/api/settings  —  get and update configuration

Settings are stored in two places:
  1. ~/NovelWriter/.nwui_global.json   — global, survives restarts, no project needed
  2. <project>/config_override.json   — project-specific overrides (optional)

POST /api/settings always saves to the global file.
If a project is currently loaded it also saves to that project's file.
"""
from typing import Optional, Union

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import backend.state as state
from backend.config_manager import (
    get_current_config,
    save_global_config,
    apply_global_config,
    save_override,
    apply_config,
)
from backend.logger import nwlog

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
    Save settings globally (always) and to the current project (if loaded).
    No project is required — backend type, model, API URL etc. are global.
    """
    data = {k: v for k, v in body.dict().items() if v is not None}
    if not data:
        raise HTTPException(status_code=400, detail="No settings provided.")

    # Always persist to and apply the global config
    save_global_config(data)
    apply_global_config()
    nwlog("settings", "SAVED globally", keys=list(data.keys()))

    # Also persist to the current project if one is loaded
    project = state.current_project_path
    if project:
        save_override(project, data)
        apply_config(project)
        nwlog("settings", "SAVED to project", project=project)

    return {"success": True, "saved": data, "config": get_current_config()}
