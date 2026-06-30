"""
Project management endpoints:

  GET  /api/projects               — list all projects in ~/NovelWriter
  GET  /api/project/state          — current project state
  POST /api/project/new            — create a brand-new project
  POST /api/project/load           — load an existing NovelWriter project
  POST /api/project/scan           — preview a directory (no side-effects)
  POST /api/project/import         — import a generic writing directory
  POST /api/project/close          — unload the current project
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import backend.state as state
from backend.config_manager import apply_config, save_override
from backend.debug_logger import dlog

router = APIRouter()


# ---------------------------------------------------------------------------
# Request bodies
# ---------------------------------------------------------------------------


class NewProjectBody(BaseModel):
    idea: str
    folder_name: str = ""
    project_dir: Optional[str] = None  # parent dir; defaults to ~/NovelWriter


class LoadProjectBody(BaseModel):
    path: str


class ScanBody(BaseModel):
    path: str


class ImportBody(BaseModel):
    source_path: str
    project_name: str = ""
    project_dir: Optional[str] = None


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _slugify(text: str) -> str:
    text = text.lower()[:60]
    text = re.sub(r"[^a-z0-9\s\-]", "", text)
    text = re.sub(r"\s+", "-", text.strip())
    text = re.sub(r"-{2,}", "-", text)
    return text.strip("-") or "my-novel"


def _count_words(filepath: str) -> int:
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return len(f.read().split())
    except OSError:
        return 0


def _scan_directory(path: str) -> dict:
    """
    Inspect a directory and return a structured description.
    Does NOT modify anything on disk.
    """
    path = os.path.expanduser(path)

    if not os.path.isdir(path):
        return {"type": "invalid", "error": "Directory not found"}

    # ── NovelWriter project detection ──────────────────────────────────────
    has_plot = os.path.exists(os.path.join(path, "plot.md"))
    has_outline = os.path.exists(os.path.join(path, "outline.json"))
    has_drafts = os.path.isdir(os.path.join(path, "drafts"))
    has_chars = os.path.exists(os.path.join(path, "characters.json"))
    has_world = os.path.exists(os.path.join(path, "world.json"))

    if has_plot or has_outline or has_drafts:
        return {
            "type": "novelwriter",
            "has_plot": has_plot,
            "has_outline": has_outline,
            "has_drafts": has_drafts,
            "has_characters": has_chars,
            "has_world": has_world,
        }

    # ── Generic markdown directory scan ────────────────────────────────────
    chapters: dict[str, List[dict]] = {}
    root_files: List[dict] = []
    total_words = 0
    total_files = 0

    for root, dirs, files in os.walk(path):
        dirs[:] = sorted(d for d in dirs if not d.startswith("."))
        for fname in sorted(files):
            if not fname.endswith(".md"):
                continue
            full = os.path.join(root, fname)
            rel = os.path.relpath(full, path)
            parts = Path(rel).parts
            words = _count_words(full)
            total_words += words
            total_files += 1
            entry = {"path": rel.replace("\\", "/"), "name": fname, "words": words}

            if len(parts) == 1:
                root_files.append(entry)
            else:
                chapter_name = parts[0]
                chapters.setdefault(chapter_name, []).append(entry)

    chapter_list = [
        {
            "name": name,
            "files": files,
            "words": sum(f["words"] for f in files),
        }
        for name, files in chapters.items()
    ]

    kind = "generic" if (chapter_list or root_files) else "empty"
    return {
        "type": kind,
        "chapters": chapter_list,
        "root_files": root_files,
        "total_files": total_files,
        "total_words": total_words,
    }


def _detect_stage(path: str) -> str:
    """Infer pipeline stage from what files exist in the project dir."""
    has_plot = os.path.exists(os.path.join(path, "plot.md"))
    has_outline = os.path.exists(os.path.join(path, "outline.json"))
    drafts_dir = os.path.join(path, "drafts")
    has_any_scene = os.path.isdir(drafts_dir) and any(
        f.startswith("scene_") and f.endswith(".md")
        for f in os.listdir(drafts_dir)
    )

    if not has_plot:
        return "init"
    if not has_outline:
        return "outline"
    if has_any_scene:
        return "write"
    return "write"   # outline exists, no scenes yet — ready to start writing


def _load_project_state(path: str) -> dict:
    """Read all project artefacts and return a state dict for the frontend."""
    plot_preview = ""
    plot_path = os.path.join(path, "plot.md")
    if os.path.exists(plot_path):
        with open(plot_path, "r", encoding="utf-8") as f:
            plot_preview = f.read()[:700]

    characters: List[str] = []
    chars_path = os.path.join(path, "characters.json")
    if os.path.exists(chars_path):
        try:
            with open(chars_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            if isinstance(raw, list):
                characters = [c.get("name", "?") for c in raw if isinstance(c, dict)]
            elif isinstance(raw, dict):
                characters = list(raw.keys())
        except (json.JSONDecodeError, OSError):
            pass

    outline: List[dict] = []
    outline_path = os.path.join(path, "outline.json")
    if os.path.exists(outline_path):
        try:
            with open(outline_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            if isinstance(raw, list):
                outline = raw
            elif isinstance(raw, dict) and "chapters" in raw:
                outline = raw["chapters"]
        except (json.JSONDecodeError, OSError):
            pass

    # Scene counts
    total_scenes = 0
    written_scenes = 0
    drafts_dir = os.path.join(path, "drafts")
    for chapter in outline:
        for scene in chapter.get("scenes", []):
            total_scenes += 1
            sid = scene.get("scene_id")
            if sid and os.path.exists(os.path.join(drafts_dir, f"scene_{sid}.md")):
                written_scenes += 1

    is_imported = os.path.exists(os.path.join(path, "import_meta.json"))

    return {
        "loaded": True,
        "path": path,
        "name": os.path.basename(path),
        "stage": _detect_stage(path),
        "is_imported": is_imported,
        "plot_preview": plot_preview,
        "characters": characters,
        "outline": outline,
        "total_scenes": total_scenes,
        "written_scenes": written_scenes,
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/projects")
def list_projects():
    """List all NovelWriter projects found under ~/NovelWriter."""
    base = os.path.expanduser("~/NovelWriter")
    if not os.path.isdir(base):
        return {"projects": []}

    projects = []
    try:
        entries = sorted(os.listdir(base))
    except OSError:
        return {"projects": []}

    for name in entries:
        path = os.path.join(base, name)
        if not os.path.isdir(path):
            continue
        has_idea = os.path.exists(os.path.join(path, "idea.md"))
        has_import = os.path.exists(os.path.join(path, "import_meta.json"))
        if not (has_idea or has_import):
            continue

        stage = _detect_stage(path)
        total_scenes = 0
        written_scenes = 0
        outline_path = os.path.join(path, "outline.json")
        if os.path.exists(outline_path):
            try:
                with open(outline_path, encoding="utf-8") as f:
                    outline = json.load(f)
                drafts = os.path.join(path, "drafts")
                for ch in outline:
                    for sc in ch.get("scenes", []):
                        total_scenes += 1
                        sid = sc.get("scene_id")
                        if sid and os.path.exists(os.path.join(drafts, f"scene_{sid}.md")):
                            written_scenes += 1
            except (OSError, json.JSONDecodeError, TypeError):
                pass

        created_at = None
        try:
            created_at = int(os.path.getctime(path) * 1000)
        except OSError:
            pass

        projects.append({
            "name": name,
            "path": path,
            "stage": stage,
            "is_imported": has_import,
            "is_current": path == state.current_project_path,
            "total_scenes": total_scenes,
            "written_scenes": written_scenes,
            "created_at": created_at,
        })

    # Most-recently-created first
    projects.sort(key=lambda p: p.get("created_at") or 0, reverse=True)
    return {"projects": projects}





@router.get("/project/state")
def get_project_state():
    """Return the current project state (or {loaded: false})."""
    if not state.current_project_path:
        dlog("project.state", loaded=False)
        return {"loaded": False}
    dlog("project.state", loaded=True, path=state.current_project_path)
    return _load_project_state(state.current_project_path)


@router.post("/project/new")
def new_project(body: NewProjectBody):
    """
    Create a brand-new project folder, save the idea, and set it as current.
    The frontend should follow up with POST /api/init to start generation.
    """
    if not body.idea.strip():
        raise HTTPException(status_code=400, detail="idea must not be empty")

    base = os.path.expanduser(body.project_dir or "~/NovelWriter")
    os.makedirs(base, exist_ok=True)

    slug = _slugify(body.folder_name or body.idea.split("\n")[0])
    project_path = os.path.join(base, slug)

    # Append a numeric suffix if the folder already exists
    counter = 1
    candidate = project_path
    while os.path.exists(candidate):
        candidate = f"{project_path}-{counter}"
        counter += 1
    project_path = candidate

    os.makedirs(project_path)
    os.makedirs(os.path.join(project_path, "drafts"))

    with open(os.path.join(project_path, "idea.md"), "w", encoding="utf-8") as f:
        f.write(body.idea)

    state.current_project_path = project_path
    apply_config(project_path)

    return {
        "success": True,
        "path": project_path,
        "name": os.path.basename(project_path),
        "stage": "init",
    }


@router.post("/project/load")
def load_project(body: LoadProjectBody):
    """
    Load an existing NovelWriter project directory.
    Returns 422 if the directory looks like a generic writing folder (use /import instead).
    """
    path = os.path.expanduser(body.path.strip())
    dlog("project.load", path=path)

    if not os.path.isdir(path):
        raise HTTPException(status_code=404, detail="Directory not found")

    info = _scan_directory(path)

    if info["type"] == "invalid":
        raise HTTPException(status_code=400, detail=info.get("error", "Invalid directory"))

    if info["type"] in ("generic", "empty"):
        raise HTTPException(
            status_code=422,
            detail=(
                "This directory doesn't look like a NovelWriter project. "
                "Use POST /api/project/scan to preview, then POST /api/project/import to bring it in."
            ),
        )

    state.current_project_path = path
    apply_config(path)

    return {
        "success": True,
        "path": path,
        "name": os.path.basename(path),
        "stage": _detect_stage(path),
        "project_info": info,
    }


@router.post("/project/scan")
def scan_project(body: ScanBody):
    """
    Non-destructive scan of a directory.
    Returns structure info so the UI can decide whether to load or import.
    """
    return _scan_directory(body.path)


@router.post("/project/import")
def import_project(body: ImportBody):
    """
    Import a generic writing directory (folders of .md files).

    Creates a new NovelWriter project directory and copies the .md files
    into drafts/ with sequential scene IDs.  After this call the frontend
    should call POST /api/analyze to have the LLM extract plot, characters,
    and world from the existing content.
    """
    source_path = os.path.expanduser(body.source_path.strip())
    dlog("project.import", source_path=source_path, project_name=body.project_name)

    if not os.path.isdir(source_path):
        raise HTTPException(status_code=404, detail="Source directory not found")

    scan = _scan_directory(source_path)

    if scan["type"] == "invalid":
        raise HTTPException(status_code=400, detail="Invalid source directory")

    # If it's already a NovelWriter project, just load it
    if scan["type"] == "novelwriter":
        state.current_project_path = source_path
        apply_config(source_path)
        return {
            "success": True,
            "path": source_path,
            "name": os.path.basename(source_path),
            "stage": _detect_stage(source_path),
            "imported": False,
            "message": "Loaded as an existing NovelWriter project.",
        }

    if scan["type"] == "empty":
        raise HTTPException(status_code=400, detail="Source directory contains no .md files")

    # ── Create destination project folder ──────────────────────────────────
    base = os.path.expanduser(body.project_dir or "~/NovelWriter")
    os.makedirs(base, exist_ok=True)

    slug = _slugify(body.project_name or os.path.basename(source_path))
    project_path = os.path.join(base, slug)
    counter = 1
    while os.path.exists(project_path):
        project_path = os.path.join(base, f"{slug}-{counter}")
        counter += 1

    os.makedirs(project_path)
    drafts_dir = os.path.join(project_path, "drafts")
    os.makedirs(drafts_dir)

    # ── Copy .md files as scene_N.md ───────────────────────────────────────
    scene_id = 1
    content_samples: List[dict] = []

    for chapter in scan.get("chapters", []):
        for file_info in chapter.get("files", []):
            src = os.path.join(source_path, file_info["path"].replace("/", os.sep))
            dst = os.path.join(drafts_dir, f"scene_{scene_id}.md")
            try:
                shutil.copy2(src, dst)
                with open(src, "r", encoding="utf-8", errors="ignore") as f:
                    content_samples.append(
                        {
                            "scene_id": scene_id,
                            "chapter": chapter["name"],
                            "file": file_info["name"],
                            "content": f.read()[:2000],
                        }
                    )
            except OSError:
                pass
            scene_id += 1

    for file_info in scan.get("root_files", []):
        src = os.path.join(source_path, file_info["path"].replace("/", os.sep))
        dst = os.path.join(drafts_dir, f"scene_{scene_id}.md")
        try:
            shutil.copy2(src, dst)
            with open(src, "r", encoding="utf-8", errors="ignore") as f:
                content_samples.append(
                    {
                        "scene_id": scene_id,
                        "chapter": "Uncategorized",
                        "file": file_info["name"],
                        "content": f.read()[:2000],
                    }
                )
        except OSError:
            pass
        scene_id += 1

    # Save import metadata so the analyze job can access it
    # Cap content_samples so import_meta.json stays manageable for large books
    meta = {
        "source_path": source_path,
        "scan": scan,
        "content_samples": content_samples[:50],
    }
    with open(os.path.join(project_path, "import_meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    state.current_project_path = project_path
    apply_config(project_path)

    return {
        "success": True,
        "path": project_path,
        "name": os.path.basename(project_path),
        "stage": "imported",
        "scene_count": scene_id - 1,
        "message": (
            f"Imported {scene_id - 1} scene(s) from '{source_path}'. "
            "Run 'Analyze Content' to generate plot, characters, and world from existing material."
        ),
    }


@router.post("/project/close")
def close_project():
    """Unload the current project."""
    state.current_project_path = None
    return {"success": True}


@router.get("/project/browse")
def browse_folder():
    """
    Open the OS native folder-picker dialog and return the chosen path.
    macOS: osascript   |   Linux: zenity / kdialog   |   Windows: PowerShell
    """
    try:
        if sys.platform == "darwin":
            result = subprocess.run(
                [
                    "osascript",
                    "-e",
                    'POSIX path of (choose folder with prompt "Select project folder:")',
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )
            path = result.stdout.strip().rstrip("/")

        elif sys.platform == "win32":
            script = (
                'Add-Type -AssemblyName System.Windows.Forms;'
                '$f=New-Object System.Windows.Forms.FolderBrowserDialog;'
                '$f.Description="Select project folder";'
                'if($f.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK){$f.SelectedPath}'
            )
            result = subprocess.run(
                ["powershell", "-Command", script],
                capture_output=True,
                text=True,
                timeout=60,
            )
            path = result.stdout.strip()

        else:
            # Linux — try zenity first, fall back to kdialog
            try:
                result = subprocess.run(
                    ["zenity", "--file-selection", "--directory", "--title=Select project folder"],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                path = result.stdout.strip()
            except FileNotFoundError:
                result = subprocess.run(
                    ["kdialog", "--getexistingdirectory"],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                path = result.stdout.strip()

        if not path or not os.path.isdir(path):
            return {"cancelled": True, "path": None}

        return {"cancelled": False, "path": path}

    except subprocess.TimeoutExpired:
        return {"cancelled": True, "path": None}
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=501,
            detail=f"No native folder picker available on this OS: {exc}",
        )
