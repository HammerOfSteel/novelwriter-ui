"""
Pipeline endpoints — queue LLM generation jobs.

  POST /api/init         — generate plot, characters, world
  POST /api/outline      — generate outline
  POST /api/write        — write next N scenes
  POST /api/reconstruct  — reconstruct story state up to scene X
  POST /api/analyze      — analyze imported content (extract plot/chars/world)
"""
from __future__ import annotations

import json
import os
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import backend.state as state
from backend.config_manager import get_current_config
from backend.debug_logger import dlog

router = APIRouter()


# ---------------------------------------------------------------------------
# Request bodies
# ---------------------------------------------------------------------------


class WriteBody(BaseModel):
    count: int = 1


class ReconstructBody(BaseModel):
    scene_id: int


# ---------------------------------------------------------------------------
# Job functions  (each receives `log` as first arg from JobRunner.submit)
# ---------------------------------------------------------------------------


def _get_generator(language: str):
    """Return the appropriate Generator class based on language setting."""
    if language.lower() == "english":
        from backend.generators_en import GeneratorEN  # noqa: PLC0415
        return GeneratorEN
    else:
        from generators import Generator  # noqa: PLC0415
        return Generator


def _job_init(log, idea: str, language: str) -> None:
    """Generate plot → characters → world."""
    Gen = _get_generator(language)
    gen = Gen()

    log("Generating plot…")
    plot = gen.generate_plot(idea)
    log(f"Plot generated ({len(plot):,} chars).")

    log("Generating characters…")
    chars = gen.generate_characters(plot)
    log(f"Characters generated ({len(chars)} total).")

    log("Generating world settings…")
    gen.generate_world(plot)
    log("World settings generated.")

    log("Initialization complete!")


def _job_outline(log, language: str) -> None:
    """Generate chapter/scene outline."""
    Gen = _get_generator(language)
    gen = Gen()

    from state_manager import StateManager  # noqa: PLC0415
    sm = StateManager()

    plot = sm.load_plot()
    if not plot:
        raise RuntimeError("No plot found. Run Init first.")

    characters = sm.load_characters()
    world = sm.load_world()

    log("Generating outline…")
    outline = gen.generate_outline(plot, characters, world)
    log(f"Outline generated: {len(outline)} chapter(s).")


def _job_write(log, count: int, language: str) -> None:
    """Write the next `count` unwritten scenes."""
    Gen = _get_generator(language)
    gen = Gen()

    from state_manager import StateManager  # noqa: PLC0415
    from config import Config  # noqa: PLC0415
    sm = StateManager()

    outline = sm.load_outline()
    if not outline:
        raise RuntimeError("No outline found. Generate Outline first.")

    characters = sm.load_characters()
    world = sm.load_world()
    current_state = sm.load_state() or {}

    scenes_written = 0
    previous_summary = ""

    for chapter in outline:
        for scene in chapter.get("scenes", []):
            scene_id = scene.get("scene_id")
            scene_file = os.path.join(Config.DRAFTS_DIR, f"scene_{scene_id}.md")
            summary_file = os.path.join(Config.DRAFTS_DIR, f"scene_{scene_id}_summary.txt")

            if os.path.exists(scene_file):
                if os.path.exists(summary_file):
                    previous_summary = sm.load_text(summary_file)
                continue

            if scenes_written >= count:
                log(f"Reached limit of {count} scene(s). Stopping.")
                return

            log(f"Writing scene {scene_id} — {chapter.get('chapter_title', '')}…")
            scene_text = gen.write_scene(scene, previous_summary, characters, world, current_state)

            log("Generating title…")
            title = gen.generate_title(scene_text)
            final = f"# {title}\n\n{scene_text}"
            sm.save_text(scene_file, final)

            log(f"Updating narrative state…")
            current_state = gen.update_state(scene_text, current_state, characters)
            sm.save_state(current_state)
            sm.save_state_snapshot(current_state, scene_id)

            log("Summarising scene…")
            summary = gen.summarize_scene(scene_text)
            sm.save_text(summary_file, summary)
            previous_summary = summary

            scenes_written += 1
            log(f"Scene {scene_id} written and saved.")

    if scenes_written == 0:
        log("All scenes are already written!")


def _job_reconstruct(log, scene_id: int, language: str) -> None:
    """Re-derive story state by replaying all written scenes up to `scene_id`."""
    Gen = _get_generator(language)
    gen = Gen()

    from state_manager import StateManager  # noqa: PLC0415
    from config import Config  # noqa: PLC0415
    sm = StateManager()

    characters = sm.load_characters()
    outline = sm.load_outline()
    if not outline:
        raise RuntimeError("No outline found.")

    current_state: dict = {}
    log(f"Reconstructing state up to scene {scene_id}…")

    done = False
    for chapter in outline:
        for scene in chapter.get("scenes", []):
            sid = scene.get("scene_id")
            scene_file = os.path.join(Config.DRAFTS_DIR, f"scene_{sid}.md")
            if os.path.exists(scene_file):
                scene_text = sm.load_text(scene_file)
                current_state = gen.update_state(scene_text, current_state, characters)
                sm.save_state_snapshot(current_state, sid)
                log(f"Replayed scene {sid}.")
            if sid >= scene_id:
                done = True
                break
        if done:
            break

    sm.save_state(current_state)
    log(f"Reconstruction complete (up to scene {scene_id}).")


def _job_analyze(log) -> None:
    """
    Analyse an imported writing directory:
    Generates plot, characters, world, and outline from the imported content.
    """
    project_path = state.current_project_path
    if not project_path:
        raise RuntimeError("No project loaded.")

    meta_file = os.path.join(project_path, "import_meta.json")
    if not os.path.exists(meta_file):
        raise RuntimeError("No import metadata found. Was this project imported via /api/project/import?")

    with open(meta_file, "r", encoding="utf-8") as f:
        meta = json.load(f)

    samples = meta.get("content_samples", [])
    if not samples:
        raise RuntimeError("No content samples found in import metadata.")

    # Build a combined excerpt for the LLM
    content_summary = "\n\n---\n\n".join(
        f"[Chapter: {s['chapter']} | File: {s['file']}]\n{s['content']}"
        for s in samples[:12]
    )

    from backend.generators_en import GeneratorEN  # noqa: PLC0415
    gen = GeneratorEN()

    # ── Plot ─────────────────────────────────────────────────────────────
    plot_path = os.path.join(project_path, "plot.md")
    if not os.path.exists(plot_path):
        log("Analysing content and generating plot summary…")
        plot = gen.analyze_and_generate_plot(content_summary)
        with open(plot_path, "w", encoding="utf-8") as f:
            f.write(plot)
        log(f"Plot saved ({len(plot):,} chars).")
    else:
        log("Plot already exists — skipping.")
        with open(plot_path, "r", encoding="utf-8") as f:
            plot = f.read()

    # ── Characters ───────────────────────────────────────────────────────
    chars_path = os.path.join(project_path, "characters.json")
    if not os.path.exists(chars_path):
        log("Extracting characters from content…")
        gen.generate_characters(plot)
        log("Characters saved.")
    else:
        log("Characters already exist — skipping.")

    # ── World ────────────────────────────────────────────────────────────
    world_path = os.path.join(project_path, "world.json")
    if not os.path.exists(world_path):
        log("Extracting world settings…")
        gen.generate_world(plot)
        log("World settings saved.")
    else:
        log("World settings already exist — skipping.")

    # ── Outline ──────────────────────────────────────────────────────────
    outline_path = os.path.join(project_path, "outline.json")
    if not os.path.exists(outline_path):
        log("Generating outline from imported structure…")
        chapters_structure = meta.get("scan", {}).get("chapters", [])
        outline = gen.generate_outline_from_structure(chapters_structure, content_summary)
        with open(outline_path, "w", encoding="utf-8") as f:
            json.dump(outline, f, indent=2, ensure_ascii=False)
        log(f"Outline saved ({len(outline)} chapter(s)).")
    else:
        log("Outline already exists — skipping.")

    log("Analysis complete! Your project is ready to continue writing.")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


def _assert_project():
    if not state.current_project_path:
        raise HTTPException(status_code=400, detail="No project is loaded.")


def _submit(func, *args, name: str):
    runner = state.get_job_runner()
    dlog("pipeline.submit", job=name, project=state.current_project_path)
    ok = runner.submit(func, *args, name=name)
    if not ok:
        dlog("pipeline.submit", job=name, rejected=True, running=runner.job_name)
        raise HTTPException(status_code=409, detail="Another job is already running.")
    return {"queued": True, "job": name}


@router.post("/init")
async def init_project(body: Optional[dict] = None):
    """Queue: generate plot, characters, and world."""
    _assert_project()
    path = state.current_project_path

    idea = ""
    idea_file = os.path.join(path, "idea.md")
    if os.path.exists(idea_file):
        with open(idea_file, "r", encoding="utf-8") as f:
            idea = f.read().strip()
    if not idea and body:
        idea = body.get("idea", "")
    if not idea:
        raise HTTPException(status_code=400, detail="No idea found for this project.")

    cfg = get_current_config()
    return _submit(_job_init, idea, cfg.get("NOVEL_LANGUAGE", "English"), name="init")


@router.post("/outline")
async def generate_outline():
    """Queue: generate the chapter/scene outline."""
    _assert_project()
    cfg = get_current_config()
    return _submit(_job_outline, cfg.get("NOVEL_LANGUAGE", "English"), name="outline")


@router.post("/write")
async def write_scenes(body: WriteBody):
    """Queue: write the next N scenes."""
    _assert_project()
    cfg = get_current_config()
    return _submit(_job_write, body.count, cfg.get("NOVEL_LANGUAGE", "English"), name="write")


@router.post("/reconstruct")
async def reconstruct_state(body: ReconstructBody):
    """Queue: rebuild story state by replaying scenes up to scene_id."""
    _assert_project()
    cfg = get_current_config()
    return _submit(
        _job_reconstruct,
        body.scene_id,
        cfg.get("NOVEL_LANGUAGE", "English"),
        name="reconstruct",
    )


@router.post("/analyze")
async def analyze_import():
    """Queue: extract plot/characters/world from imported content."""
    _assert_project()
    return _submit(_job_analyze, name="analyze")
