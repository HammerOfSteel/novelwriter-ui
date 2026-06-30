"""
Config manager: loads, saves, and applies per-project config overrides.

Config values are persisted in `<project_dir>/config_override.json` so
each project can have its own model, viewpoint, style, etc.
The NovelWriter `Config` class is patched in-place at runtime.
"""
import json
import os
from typing import Any, Dict

CONFIG_FILENAME = "config_override.json"

# Global settings file — persists across server restarts, shared by all projects
_GLOBAL_CONFIG_DIR = os.path.expanduser("~/NovelWriter")
_GLOBAL_CONFIG_PATH = os.path.join(_GLOBAL_CONFIG_DIR, ".nwui_global.json")

# Default values mirroring Config class defaults (English-first)
DEFAULTS: Dict[str, Any] = {
    # Backend selection
    "BACKEND_TYPE": "ollama",
    # Debug
    "DEBUG_MODE": False,
    # Ollama
    "OLLAMA_BASE_URL": "http://localhost:11434",
    "DEFAULT_MODEL": "",
    "CONTEXT_LENGTH_SIZE": 100000,
    "THINK_MODE": "high",
    # OpenAI-compatible API (LM Studio, Jan, etc.)
    "API_URL": "http://127.0.0.1:1234",
    "API_KEY": "",
    "API_MODEL": "",
    # Novel generation
    "NOVEL_VIEWPOINT": "Third person omniscient",
    "NOVEL_STYLE": "Literary fiction",
    "MAX_CONTEXT_CHARS": 4000,
    "NOVEL_LANGUAGE": "English",
}


# ---------------------------------------------------------------------------
# File I/O
# ---------------------------------------------------------------------------


def _config_path(project_path: str) -> str:
    return os.path.join(project_path, CONFIG_FILENAME)


def load_override(project_path: str) -> Dict[str, Any]:
    """Load the saved config override for the given project, or {}."""
    path = _config_path(project_path)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_override(project_path: str, data: Dict[str, Any]) -> None:
    """Merge `data` into the project's config_override.json."""
    os.makedirs(project_path, exist_ok=True)
    existing = load_override(project_path)
    existing.update({k: v for k, v in data.items() if v is not None})
    with open(_config_path(project_path), "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Global config (survives server restarts, no project needed)
# ---------------------------------------------------------------------------

def load_global_config() -> Dict[str, Any]:
    """Load the global config from ~/NovelWriter/.nwui_global.json."""
    if os.path.exists(_GLOBAL_CONFIG_PATH):
        try:
            with open(_GLOBAL_CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_global_config(data: Dict[str, Any]) -> None:
    """Merge `data` into the global config file."""
    os.makedirs(_GLOBAL_CONFIG_DIR, exist_ok=True)
    existing = load_global_config()
    existing.update({k: v for k, v in data.items() if v is not None})
    with open(_GLOBAL_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)


def apply_global_config() -> None:
    """Apply global settings to Config on startup (before any project is loaded)."""
    cfg = load_global_config()
    if not cfg:
        return
    try:
        import config as nw_config  # noqa: PLC0415
        Cfg = nw_config.Config
    except ImportError:
        return
    for key, value in cfg.items():
        if hasattr(Cfg, key):
            setattr(Cfg, key, value)


# ---------------------------------------------------------------------------
# Runtime patching
# ---------------------------------------------------------------------------


def apply_config(project_path: str) -> None:
    """
    Patch the NovelWriter Config class in-place:
    1. Apply global settings (~/.nwui_global.json) as the base.
    2. Set all path attributes to point at `project_path`.
    3. Apply any project-level overrides from config_override.json.
    """
    try:
        import config as nw_config  # noqa: PLC0415
        Cfg = nw_config.Config
    except ImportError:
        return  # novelwriter not on path yet — will be set up later

    # Layer 1: global defaults
    for key, value in load_global_config().items():
        if hasattr(Cfg, key):
            setattr(Cfg, key, value)

    # Layer 2: project paths
    Cfg.BASE_DIR = project_path
    Cfg.CHARACTERS_FILE = os.path.join(project_path, "characters.json")
    Cfg.WORLD_FILE = os.path.join(project_path, "world.json")
    Cfg.PLOT_FILE = os.path.join(project_path, "plot.md")
    Cfg.OUTLINE_FILE = os.path.join(project_path, "outline.json")
    Cfg.DRAFTS_DIR = os.path.join(project_path, "drafts")
    Cfg.STATE_FILE = os.path.join(project_path, "state.json")

    # Layer 3: project-specific overrides (wins over global for this project)
    for key, value in load_override(project_path).items():
        if hasattr(Cfg, key):
            setattr(Cfg, key, value)


def get_current_config() -> Dict[str, Any]:
    """Return a dict of the current effective Config values."""
    try:
        import config as nw_config  # noqa: PLC0415
        Cfg = nw_config.Config
        return {
            "BACKEND_TYPE": getattr(Cfg, "BACKEND_TYPE", "ollama"),
            "DEBUG_MODE": getattr(Cfg, "DEBUG_MODE", False),
            "OLLAMA_BASE_URL": Cfg.OLLAMA_BASE_URL,
            "DEFAULT_MODEL": Cfg.DEFAULT_MODEL,
            "CONTEXT_LENGTH_SIZE": Cfg.CONTEXT_LENGTH_SIZE,
            "THINK_MODE": Cfg.THINK_MODE,
            "API_URL": getattr(Cfg, "API_URL", "http://127.0.0.1:1234"),
            "API_KEY": getattr(Cfg, "API_KEY", ""),
            "API_MODEL": getattr(Cfg, "API_MODEL", ""),
            "NOVEL_VIEWPOINT": Cfg.NOVEL_VIEWPOINT,
            "NOVEL_STYLE": Cfg.NOVEL_STYLE,
            "MAX_CONTEXT_CHARS": Cfg.MAX_CONTEXT_CHARS,
            "NOVEL_LANGUAGE": getattr(Cfg, "NOVEL_LANGUAGE", "English"),
        }
    except ImportError:
        return dict(DEFAULTS)
