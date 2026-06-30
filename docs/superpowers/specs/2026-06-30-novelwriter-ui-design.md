# NovelWriter UI — Design Spec
**Date:** 2026-06-30  
**Status:** Approved  

---

## Overview

A Pinokio app that wraps [KudoShusak/NovelWriter](https://github.com/KudoShusak/NovelWriter) — a local AI-assisted novel writing pipeline — with a polished web UI. The UI replaces the CLI entirely for normal use. Users can start a novel from a fresh idea or load an existing project folder (one that already contains `plot.md`, `outline.json`, `drafts/`, etc.).

**Language:** English only (NovelWriter defaults to Japanese; config defaults will be overridden to English).  
**Stack:** SvelteKit + shadcn-svelte (frontend) · FastAPI + Python (backend) · Pinokio launcher.  
**Workflow model:** Dashboard — all pipeline stages visible at once; no wizard.

---

## Architecture

```
novelwriter-ui.git/
├── novelwriter/              ← git submodule (forked from KudoShusak/NovelWriter)
├── backend/
│   └── server.py             ← FastAPI app, imports novelwriter modules directly
├── frontend/
│   ├── src/routes/           ← SvelteKit pages
│   └── build/                ← compiled static files served by FastAPI
├── install.js
├── start.js
├── update.js
├── reset.js
├── pinokio.js
├── pinokio.json
├── TODO.md
└── README.md
```

**Single process, single port.** FastAPI serves both the API and the compiled SvelteKit static files. Pinokio captures the URL via the standard SSE regex pattern. The `novelwriter/` directory is a git submodule pointing at the fork — keeping upstream changes separable via `git submodule update`.

**NovelWriter integration:** The backend imports `novelwriter.generators`, `novelwriter.state_manager`, and `novelwriter.config` directly (no subprocess spawning). The `Config.BASE_DIR` is monkey-patched at runtime to the currently loaded project path, so all file reads/writes target the user's chosen folder without modifying the upstream source.

---

## Screens

### 1. Home / Project Picker
Shown when no project is loaded.

- **Prerequisite status bar** (top): shows Ollama ✓/✗ and Python deps ✓/✗ with inline "Install" buttons. Ollama check hits `GET http://localhost:11434/api/tags`; deps check probes for `fastapi`, `uvicorn`, `requests` in the venv.
- **New Project card**: textarea for the novel idea, a folder name field (defaults to a slugified version of the first line of the idea), and a "Create Project" button.
- **Open Existing Project card**: text input for a directory path (absolute). On submit, the backend validates the folder (checks for at least one of `plot.md`, `outline.json`, or `drafts/`) and returns the detected stage. Invalid paths show an inline error.

### 2. Dashboard (active project)
Shown once a project is loaded.

- **Left sidebar**: project name, full folder path, stage pipeline indicator — `Init → Outline → Write → Done` — with checkmarks for completed stages and a pulsing indicator on the active one.
- **Main area — four panels:**
  - **Plot** — collapsible card showing the first 500 chars of `plot.md` with a "View full" link that opens the file in the OS default app (`open <path>` via the backend).
  - **Characters** — count + list of character names from `characters.json`.
  - **Outline** — chapter/scene grid. Each scene tile shows its ID, title (if written), and status: `pending` / `written`. Clicking a written scene opens `drafts/scene_N.md` in the OS default app.
  - **Progress** — `X of Y scenes written`, progress bar.
- **Action bar** (context-sensitive):
  - Stage `init` not done → "Generate Plot & Characters" button.
  - Plot done, outline not done → "Generate Outline" button.
  - Outline done → "Write Next Scene" button + "Write N Scenes" input+button + "Reconstruct Scene X" input+button.
  - All scenes written → "Complete ✓" badge.
- **Live log panel** (bottom, collapsible): SSE stream from the active generation job. Auto-scrolls. Shows spinner while a job is running; shows "Done" or error message on completion.

### 3. Settings
Accessible from the sidebar any time.

| Setting | Maps to | Default |
|---|---|---|
| Ollama Base URL | `Config.OLLAMA_BASE_URL` | `http://localhost:11434` |
| Model | `Config.DEFAULT_MODEL` | dropdown from `/api/ollama/models` |
| Context Length | `Config.CONTEXT_LENGTH_SIZE` | `100000` |
| Think Mode | `Config.THINK_MODE` | `high` (select: off / low / medium / high) |
| Novel Style | `Config.NOVEL_STYLE` | `Light Novel` (text input) |
| Viewpoint | `Config.NOVEL_VIEWPOINT` | `Third person omniscient` (text input) |
| Max Context Chars | `Config.MAX_CONTEXT_CHARS` | `4000` |

Settings are persisted to `config_override.json` inside the active project folder — not written back to `config.py`. On project load the backend reads this file (if present) and merges it over the `Config` defaults.

---

## Backend API

All endpoints are under `/api`. FastAPI serves the SvelteKit `build/` directory at `/`.

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/status` | Returns `{ ollama: bool, deps: bool }` |
| `POST` | `/api/prereqs/install` | Runs `uv pip install requests` in the active venv |
| `GET` | `/api/ollama/models` | Proxies Ollama's `/api/tags`, returns list of model names |
| `POST` | `/api/project/new` | Body: `{ idea: str, folder_name: str }`. Creates folder, runs `init`. |
| `POST` | `/api/project/load` | Body: `{ path: str }`. Validates folder, detects stage, returns state. |
| `GET` | `/api/project/state` | Returns current plot summary, characters, outline with scene statuses. |
| `POST` | `/api/outline` | Queues outline generation job. |
| `POST` | `/api/write` | Body: `{ count: int }`. Queues write job. |
| `POST` | `/api/reconstruct` | Body: `{ scene_id: int }`. Queues reconstruct job. |
| `GET` | `/api/stream` | SSE endpoint. Streams log lines from the active job. Sends `{ done: true }` on completion and `{ error: "..." }` on failure. |
| `GET` | `/api/settings` | Returns current config override. |
| `POST` | `/api/settings` | Body: partial config fields. Merges and saves `config_override.json`. |

**Job runner:** A single `threading.Thread` with a `queue.Queue`. Only one job runs at a time. The SSE endpoint is a generator that drains a `log_queue` deque populated by the job thread. If a job is already running when a new one is submitted, the API returns `409 Conflict`.

**Config override:** At project load, `Config` class attributes are patched in-place from `config_override.json`. `Config.BASE_DIR` is always overridden to the loaded project path regardless of the override file.

---

## Pinokio Launcher Scripts

**`install.js`**
1. Init the `novelwriter/` submodule (`git submodule update --init`).
2. Create Python 3.11 venv at `env/` via `uv venv --python 3.11`.
3. `uv pip install fastapi uvicorn requests`.
4. `npm install` in `frontend/`.
5. `npm run build` in `frontend/`.

**`start.js`** (daemon: true)
- Activate venv, run `uvicorn backend.server:app --host 127.0.0.1 --port {{port}}`.
- Capture URL via `/(http:\/\/[0-9.:]+)/` → `local.set { url }`.

**`update.js`**
- `git pull`, `git submodule update --remote`, reinstall deps, rebuild frontend.

**`reset.js`**
- Delete `env/` and `frontend/build/`. Preserve all project data (user's project folders are outside the install dir).

**`pinokio.js`** — dynamic menu:
- No venv → "Install" (default)
- Venv exists, not running → "Start" (default)
- Running + url set → "Open Panel" (default) + Terminal + Update + Reset

---

## TODO.md Phases

The `TODO.md` in the repo root will track implementation in these phases:

| Phase | Scope |
|---|---|
| 1 | Fork repo, create Pinokio app repo, add git submodule, Pinokio JSON/icon |
| 2 | `install.js`, `start.js`, `update.js`, `reset.js`, `pinokio.js` |
| 3 | FastAPI skeleton — all endpoints stubbed, job runner, SSE |
| 4 | SvelteKit app init, shadcn-svelte setup, routing scaffolding |
| 5 | Home screen: new project + load existing + prerequisite bar |
| 6 | Dashboard: sidebar, stage indicator, four panels |
| 7 | Action bar with context-sensitive buttons |
| 8 | Live log panel (SSE → UI) |
| 9 | Settings screen + Ollama model dropdown |
| 10 | Polish: dark mode, error states, empty states, README |

---

## Out of Scope

- Built-in file editor for scenes/plot/characters (user edits files externally)
- Multi-project management (one active project at a time per panel)
- Authentication
- Export / publishing pipeline
