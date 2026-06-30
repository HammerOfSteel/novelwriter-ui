# NovelWriter UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Pinokio app with a SvelteKit + shadcn-svelte web UI wrapping the NovelWriter novel writing pipeline, runnable with one click from Pinokio.

**Architecture:** FastAPI Python backend imports NovelWriter modules directly and serves compiled SvelteKit static files on a single port. A background job thread handles long-running pipeline steps and streams progress via SSE. The NovelWriter fork lives as a git submodule at `novelwriter/`.

**Tech Stack:** Python 3.11 · FastAPI · uvicorn · sse-starlette · pytest · httpx · SvelteKit · TypeScript · shadcn-svelte · Tailwind CSS · Pinokio launcher scripts

---

## File Map

```
novelwriter-ui.git/
├── novelwriter/                        ← git submodule (HammerOfSteel/NovelWriter)
├── backend/
│   ├── __init__.py
│   ├── server.py                       ← FastAPI app entry, static file serving, SPA fallback
│   ├── state.py                        ← module-level singletons (JobRunner, project path)
│   ├── config_manager.py               ← load Config, patch BASE_DIR, apply config_override.json
│   ├── job_runner.py                   ← background thread, log queue, SSE generator
│   └── routers/
│       ├── __init__.py
│       ├── status.py                   ← GET /api/status, POST /api/prereqs/install
│       ├── ollama.py                   ← GET /api/ollama/models
│       ├── project.py                  ← POST /api/project/new|load, GET /api/project/state
│       ├── pipeline.py                 ← POST /api/outline|write|reconstruct
│       ├── settings.py                 ← GET/POST /api/settings
│       └── stream.py                   ← GET /api/stream (SSE)
├── tests/
│   ├── conftest.py
│   ├── test_config_manager.py
│   ├── test_job_runner.py
│   ├── test_status.py
│   ├── test_project.py
│   ├── test_pipeline.py
│   └── test_settings.py
├── frontend/
│   ├── package.json
│   ├── svelte.config.js
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── src/
│   │   ├── app.html
│   │   ├── app.css
│   │   ├── lib/
│   │   │   ├── api.ts                  ← typed fetch wrappers for all API endpoints
│   │   │   ├── stores.ts               ← Svelte writable stores (project, job, settings)
│   │   │   └── components/
│   │   │       ├── PrereqBar.svelte    ← prerequisite status bar with install buttons
│   │   │       ├── StageIndicator.svelte ← pipeline stage progress (Init→Outline→Write→Done)
│   │   │       ├── OutlineGrid.svelte  ← chapter/scene grid with written/pending status
│   │   │       └── LogPanel.svelte     ← SSE log stream, auto-scroll, spinner
│   │   └── routes/
│   │       ├── +layout.svelte
│   │       ├── +layout.ts
│   │       ├── +page.svelte            ← Home / project picker
│   │       ├── project/
│   │       │   └── +page.svelte        ← Dashboard
│   │       └── settings/
│   │           └── +page.svelte        ← Settings
│   └── build/                          ← compiled output, served by FastAPI
├── install.js
├── start.js
├── update.js
├── reset.js
├── pinokio.js
├── pinokio.json
├── TODO.md
└── README.md
```

---

### Task 1: Fork NovelWriter and Initialize the Repo

**Files:**
- Create: `.gitignore`
- Create: `.gitmodules` (via `git submodule add`)

- [ ] **Step 1: Fork KudoShusak/NovelWriter to your account**

```bash
cd ~/pinokio/api/novelwriter-ui.git
gh repo fork KudoShusak/NovelWriter --clone=false --fork-name NovelWriter
```

Expected output: `✓ Created fork HammerOfSteel/NovelWriter`

- [ ] **Step 2: Add the fork as a git submodule**

```bash
git submodule add https://github.com/HammerOfSteel/NovelWriter.git novelwriter
```

Expected: `Cloning into '...'` followed by `novelwriter` folder appearing with the NovelWriter files inside it.

- [ ] **Step 3: Create .gitignore**

```
# Python
env/
__pycache__/
*.pyc
.pytest_cache/

# Node
frontend/node_modules/
frontend/build/
frontend/.svelte-kit/

# Runtime
*.json.tmp
```

Save as `.gitignore` at the repo root.

- [ ] **Step 4: Commit**

```bash
git add .gitmodules novelwriter .gitignore
git commit -m "chore: add NovelWriter fork as submodule, init .gitignore"
```

---

### Task 2: Pinokio Metadata, TODO.md, README stub

**Files:**
- Create: `pinokio.json`
- Create: `TODO.md`
- Create: `README.md`

- [ ] **Step 1: Create pinokio.json**

```json
{
  "title": "NovelWriter UI",
  "description": "AI-assisted novel writing web UI powered by Ollama. Write 70k-100k character novels locally: plot generation, character building, scene-by-scene writing.",
  "icon": "icon.png",
  "version": "7.0"
}
```

- [ ] **Step 2: Download an icon**

```bash
curl -L "$(gh api repos/KudoShusak/NovelWriter --jq '.owner.avatar_url')" -o icon.png
```

If the above fails, create a placeholder: `touch icon.png`

- [ ] **Step 3: Create TODO.md**

```markdown
# NovelWriter UI — TODO

## Phase 1 ✅ Fork + repo setup
## Phase 2 — Pinokio launcher scripts (install/start/update/reset/pinokio.js)
## Phase 3 — FastAPI backend skeleton (all endpoints, job runner, SSE)
## Phase 4 — SvelteKit app init + shadcn-svelte setup
## Phase 5 — Home screen: new project + load existing + prerequisite bar
## Phase 6 — Dashboard: sidebar, stage indicator, four panels
## Phase 7 — Action bar with context-sensitive buttons
## Phase 8 — Live log panel (SSE → UI)
## Phase 9 — Settings screen + Ollama model dropdown
## Phase 10 — Polish: dark mode, error states, empty states, README
```

- [ ] **Step 4: Create README.md**

```markdown
# NovelWriter UI

A Pinokio app wrapping [NovelWriter](https://github.com/KudoShusak/NovelWriter) with a polished web interface.

Generates full novels (70k–100k chars) locally using Ollama: plot → characters → outline → scenes.

## Requirements
- Pinokio
- Ollama running with at least one model pulled

## Usage
Install and launch from Pinokio. Open the panel, create a new project or load an existing one.
```

- [ ] **Step 5: Commit**

```bash
git add pinokio.json TODO.md README.md icon.png
git commit -m "chore: add Pinokio metadata, TODO phases, README stub"
```

---

### Task 3: Backend Package Skeleton + Requirements

**Files:**
- Create: `backend/__init__.py`
- Create: `backend/routers/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `requirements.txt`
- Create: `requirements-dev.txt`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p backend/routers tests
```

- [ ] **Step 2: Create backend/__init__.py and backend/routers/__init__.py**

Both files are empty.

- [ ] **Step 3: Create tests/__init__.py**

Empty file.

- [ ] **Step 4: Create tests/conftest.py**

```python
import sys
import os

# Ensure project root is on sys.path so `backend` package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

- [ ] **Step 5: Create requirements.txt**

```
fastapi>=0.111.0
uvicorn[standard]>=0.29.0
requests>=2.31.0
sse-starlette>=2.1.0
```

- [ ] **Step 6: Create requirements-dev.txt**

```
pytest>=8.0.0
httpx>=0.27.0
pytest-asyncio>=0.23.0
```

- [ ] **Step 7: Commit**

```bash
git add backend/ tests/ requirements.txt requirements-dev.txt
git commit -m "chore: backend package skeleton, requirements files"
```

---

### Task 4: Config Manager + Tests

**Files:**
- Create: `backend/config_manager.py`
- Create: `tests/test_config_manager.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_config_manager.py
import os
import json
import tempfile
import sys
from unittest.mock import MagicMock

# Mock the novelwriter config module before importing config_manager
mock_config_module = MagicMock()
class MockConfig:
    OLLAMA_BASE_URL = "http://localhost:11434"
    DEFAULT_MODEL = "gpt-oss:120b"
    CONTEXT_LENGTH_SIZE = 100000
    THINK_MODE = "high"
    NOVEL_VIEWPOINT = "三人称神視点"
    NOVEL_STYLE = "指定なし"
    MAX_CONTEXT_CHARS = 4000
    BASE_DIR = "/old/path"
    CHARACTERS_FILE = "/old/path/characters.json"
    WORLD_FILE = "/old/path/world.json"
    PLOT_FILE = "/old/path/plot.md"
    OUTLINE_FILE = "/old/path/outline.json"
    DRAFTS_DIR = "/old/path/drafts"
    STATE_FILE = "/old/path/state.json"

mock_config_module.Config = MockConfig
sys.modules["config"] = mock_config_module

from backend.config_manager import apply_project_path, apply_overrides, get_settings, save_overrides


def test_apply_project_path_sets_base_dir():
    apply_project_path("/my/novel/project")
    assert MockConfig.BASE_DIR == "/my/novel/project"
    assert MockConfig.PLOT_FILE == "/my/novel/project/plot.md"
    assert MockConfig.DRAFTS_DIR == "/my/novel/project/drafts"


def test_apply_project_path_sets_english_defaults():
    apply_project_path("/some/path")
    assert MockConfig.NOVEL_VIEWPOINT == "Third person omniscient"
    assert MockConfig.NOVEL_STYLE == "Not specified"


def test_apply_overrides_from_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump({"DEFAULT_MODEL": "llama3.1:8b", "THINK_MODE": "low"}, f)
        tmp_path = f.name
    try:
        apply_overrides(tmp_path)
        assert MockConfig.DEFAULT_MODEL == "llama3.1:8b"
        assert MockConfig.THINK_MODE == "low"
    finally:
        os.unlink(tmp_path)


def test_apply_overrides_missing_file_is_noop():
    MockConfig.DEFAULT_MODEL = "gpt-oss:120b"
    apply_overrides("/nonexistent/override.json")  # should not raise
    assert MockConfig.DEFAULT_MODEL == "gpt-oss:120b"


def test_get_settings_returns_dict():
    settings = get_settings()
    assert "ollama_base_url" in settings
    assert "default_model" in settings
    assert "novel_viewpoint" in settings


def test_save_overrides_writes_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "config_override.json")
        save_overrides(path, {"default_model": "mistral:7b"})
        with open(path) as f:
            data = json.load(f)
        assert data["DEFAULT_MODEL"] == "mistral:7b"
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd ~/pinokio/api/novelwriter-ui.git
python -m pytest tests/test_config_manager.py -v 2>&1 | head -20
```

Expected: `ImportError` for `backend.config_manager`

- [ ] **Step 3: Implement backend/config_manager.py**

```python
# backend/config_manager.py
import os
import sys
import json
from typing import Any

# Add novelwriter submodule to sys.path
_NW_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "novelwriter")
if _NW_PATH not in sys.path:
    sys.path.insert(0, _NW_PATH)

from config import Config


def apply_project_path(project_path: str) -> None:
    """Override all Config path attributes to target project_path."""
    Config.BASE_DIR = project_path
    Config.CHARACTERS_FILE = os.path.join(project_path, "characters.json")
    Config.WORLD_FILE = os.path.join(project_path, "world.json")
    Config.PLOT_FILE = os.path.join(project_path, "plot.md")
    Config.OUTLINE_FILE = os.path.join(project_path, "outline.json")
    Config.DRAFTS_DIR = os.path.join(project_path, "drafts")
    Config.STATE_FILE = os.path.join(project_path, "state.json")
    # Force English output defaults
    Config.NOVEL_VIEWPOINT = "Third person omniscient"
    Config.NOVEL_STYLE = "Not specified"


def apply_overrides(override_file: str) -> None:
    """Read config_override.json and apply any matching Config attributes."""
    if not os.path.exists(override_file):
        return
    with open(override_file, encoding="utf-8") as f:
        overrides = json.load(f)
    for key, value in overrides.items():
        if hasattr(Config, key):
            setattr(Config, key, value)


def get_settings() -> dict[str, Any]:
    """Return current Config values as a serialisable dict."""
    return {
        "ollama_base_url": Config.OLLAMA_BASE_URL,
        "default_model": Config.DEFAULT_MODEL,
        "context_length_size": Config.CONTEXT_LENGTH_SIZE,
        "think_mode": Config.THINK_MODE,
        "novel_viewpoint": Config.NOVEL_VIEWPOINT,
        "novel_style": Config.NOVEL_STYLE,
        "max_context_chars": Config.MAX_CONTEXT_CHARS,
    }


# Maps settings-dict keys → Config attribute names
_SETTINGS_MAP = {
    "ollama_base_url": "OLLAMA_BASE_URL",
    "default_model": "DEFAULT_MODEL",
    "context_length_size": "CONTEXT_LENGTH_SIZE",
    "think_mode": "THINK_MODE",
    "novel_viewpoint": "NOVEL_VIEWPOINT",
    "novel_style": "NOVEL_STYLE",
    "max_context_chars": "MAX_CONTEXT_CHARS",
}


def save_overrides(override_file: str, settings: dict[str, Any]) -> None:
    """Persist settings as Config attribute names to override_file, and apply them live."""
    to_save = {}
    for settings_key, value in settings.items():
        config_key = _SETTINGS_MAP.get(settings_key)
        if config_key:
            to_save[config_key] = value
            setattr(Config, config_key, value)
    os.makedirs(os.path.dirname(os.path.abspath(override_file)), exist_ok=True)
    with open(override_file, "w", encoding="utf-8") as f:
        json.dump(to_save, f, indent=2)
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
python -m pytest tests/test_config_manager.py -v
```

Expected: `6 passed`

- [ ] **Step 5: Commit**

```bash
git add backend/config_manager.py tests/test_config_manager.py
git commit -m "feat(backend): config manager with project path override and settings persistence"
```

---

### Task 5: Job Runner + Tests

**Files:**
- Create: `backend/job_runner.py`
- Create: `tests/test_job_runner.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_job_runner.py
import time
import threading
from backend.job_runner import JobRunner


def test_initial_state_not_running():
    runner = JobRunner()
    assert runner.is_running() is False
    assert runner.current_job() is None


def test_submit_runs_job():
    runner = JobRunner()
    results = []
    def job():
        results.append("done")
    assert runner.submit("test_job", job) is True
    time.sleep(0.2)
    assert results == ["done"]


def test_second_submit_rejected_while_running():
    runner = JobRunner()
    barrier = threading.Barrier(2)
    def slow_job():
        barrier.wait()
        time.sleep(0.3)
    runner.submit("slow", slow_job)
    barrier.wait()
    assert runner.is_running() is True
    assert runner.submit("second", lambda: None) is False


def test_log_lines_available_after_job():
    runner = JobRunner()
    def job():
        runner.log("hello from job")
    runner.submit("log_test", job)
    time.sleep(0.2)
    msgs = runner.drain_log()
    assert any(m["type"] == "log" and m["line"] == "hello from job" for m in msgs)


def test_done_message_emitted_after_success():
    runner = JobRunner()
    runner.submit("done_test", lambda: None)
    time.sleep(0.2)
    msgs = runner.drain_log()
    assert any(m["type"] == "done" for m in msgs)


def test_error_message_emitted_on_exception():
    runner = JobRunner()
    def failing():
        raise ValueError("boom")
    runner.submit("fail_test", failing)
    time.sleep(0.2)
    msgs = runner.drain_log()
    error_msgs = [m for m in msgs if m["type"] == "error"]
    assert error_msgs and "boom" in error_msgs[0]["error"]
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
python -m pytest tests/test_job_runner.py -v 2>&1 | head -10
```

Expected: `ImportError` for `backend.job_runner`

- [ ] **Step 3: Implement backend/job_runner.py**

```python
# backend/job_runner.py
import queue
import threading
from typing import Callable, Optional


class JobRunner:
    def __init__(self):
        self._job_queue: queue.Queue = queue.Queue()
        self._log_queue: queue.Queue = queue.Queue()
        self._running = False
        self._current_job_name: Optional[str] = None
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def submit(self, name: str, fn: Callable, *args, **kwargs) -> bool:
        """Submit a job. Returns False if a job is already running."""
        if self._running:
            return False
        self._job_queue.put((name, fn, args, kwargs))
        return True

    def log(self, line: str) -> None:
        """Emit a log line from within a running job."""
        self._log_queue.put({"type": "log", "line": line})

    def is_running(self) -> bool:
        return self._running

    def current_job(self) -> Optional[str]:
        return self._current_job_name

    def drain_log(self) -> list:
        """Drain all currently queued log messages (non-blocking). For tests."""
        msgs = []
        while True:
            try:
                msgs.append(self._log_queue.get_nowait())
            except queue.Empty:
                break
        return msgs

    async def stream(self):
        """Async generator yielding log dicts for SSE EventSourceResponse."""
        import asyncio
        while True:
            try:
                msg = self._log_queue.get_nowait()
                yield msg
                if msg.get("type") in ("done", "error"):
                    return
            except queue.Empty:
                if not self._running:
                    return
                await asyncio.sleep(0.1)

    def _worker(self):
        while True:
            name, fn, args, kwargs = self._job_queue.get()
            self._running = True
            self._current_job_name = name
            try:
                fn(*args, **kwargs)
                self._log_queue.put({"type": "done"})
            except Exception as exc:
                self._log_queue.put({"type": "error", "error": str(exc)})
            finally:
                self._running = False
                self._current_job_name = None
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
python -m pytest tests/test_job_runner.py -v
```

Expected: `6 passed`

- [ ] **Step 5: Commit**

```bash
git add backend/job_runner.py tests/test_job_runner.py
git commit -m "feat(backend): job runner with background thread, log queue, SSE stream generator"
```

---

### Task 6: Shared State Module

**Files:**
- Create: `backend/state.py`

- [ ] **Step 1: Create backend/state.py**

```python
# backend/state.py
"""Module-level singletons shared across all routers."""
from backend.job_runner import JobRunner

job_runner = JobRunner()
_project_path: str | None = None


def set_project_path(path: str) -> None:
    global _project_path
    _project_path = path


def get_project_path() -> str | None:
    return _project_path
```

- [ ] **Step 2: Commit**

```bash
git add backend/state.py
git commit -m "feat(backend): shared state module (job runner singleton, project path)"
```

---

### Task 7: Status Router + Tests

**Files:**
- Create: `backend/routers/status.py`
- Create: `tests/test_status.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_status.py
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
from backend.routers.status import router

app = FastAPI()
app.include_router(router, prefix="/api")
client = TestClient(app)


def test_status_ollama_unreachable():
    with patch("backend.routers.status.requests.get", side_effect=Exception("refused")):
        resp = client.get("/api/status")
    assert resp.status_code == 200
    assert resp.json()["ollama"] is False
    assert "deps" in resp.json()


def test_status_ollama_reachable():
    mock_response = MagicMock()
    mock_response.status_code = 200
    with patch("backend.routers.status.requests.get", return_value=mock_response):
        resp = client.get("/api/status")
    assert resp.status_code == 200
    assert resp.json()["ollama"] is True


def test_deps_check_returns_bool():
    with patch("backend.routers.status.requests.get", side_effect=Exception()):
        resp = client.get("/api/status")
    assert isinstance(resp.json()["deps"], bool)
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
python -m pytest tests/test_status.py -v 2>&1 | head -10
```

Expected: `ImportError` for `backend.routers.status`

- [ ] **Step 3: Implement backend/routers/status.py**

```python
# backend/routers/status.py
import subprocess
import sys
import requests
from fastapi import APIRouter

router = APIRouter()


def _check_ollama(base_url: str = "http://localhost:11434") -> bool:
    try:
        r = requests.get(f"{base_url}/api/tags", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def _check_deps() -> bool:
    required = ["fastapi", "uvicorn", "requests", "sse_starlette"]
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            return False
    return True


@router.get("/status")
def get_status():
    return {"ollama": _check_ollama(), "deps": _check_deps()}


@router.post("/prereqs/install")
def install_prereqs():
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install",
         "fastapi", "uvicorn[standard]", "requests", "sse-starlette"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return {"ok": False, "error": result.stderr}
    return {"ok": True}
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
python -m pytest tests/test_status.py -v
```

Expected: `3 passed`

- [ ] **Step 5: Commit**

```bash
git add backend/routers/status.py tests/test_status.py
git commit -m "feat(backend): status router — Ollama health check, dep check, prereq install"
```

---

### Task 8: Remaining Routers + Tests

**Files:**
- Create: `backend/routers/ollama.py`
- Create: `backend/routers/project.py`
- Create: `backend/routers/pipeline.py`
- Create: `backend/routers/settings.py`
- Create: `backend/routers/stream.py`
- Create: `tests/test_project.py`
- Create: `tests/test_pipeline.py`
- Create: `tests/test_settings.py`

- [ ] **Step 1: Create backend/routers/ollama.py**

```python
# backend/routers/ollama.py
import requests
from fastapi import APIRouter
from backend.config_manager import get_settings

router = APIRouter()


@router.get("/ollama/models")
def get_models():
    settings = get_settings()
    base_url = settings["ollama_base_url"]
    try:
        r = requests.get(f"{base_url}/api/tags", timeout=5)
        r.raise_for_status()
        models = [m["name"] for m in r.json().get("models", [])]
        return {"models": models}
    except Exception as exc:
        return {"models": [], "error": str(exc)}
```

- [ ] **Step 2: Create backend/routers/project.py**

```python
# backend/routers/project.py
import os
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend import state
from backend.config_manager import apply_project_path, apply_overrides

router = APIRouter()


class NewProjectRequest(BaseModel):
    idea: str
    folder_name: str


class LoadProjectRequest(BaseModel):
    path: str


def _detect_stage(path: str) -> str:
    drafts = os.path.join(path, "drafts")
    outline = os.path.join(path, "outline.json")
    plot = os.path.join(path, "plot.md")
    if not os.path.exists(plot):
        return "init"
    if not os.path.exists(outline):
        return "outline"
    total, written = _count_scenes(path)
    if total > 0 and written >= total:
        return "done"
    return "write"


def _count_scenes(path: str) -> tuple:
    outline_file = os.path.join(path, "outline.json")
    drafts_dir = os.path.join(path, "drafts")
    if not os.path.exists(outline_file):
        return 0, 0
    with open(outline_file, encoding="utf-8") as f:
        outline = json.load(f)
    total = sum(len(ch.get("scenes", [])) for ch in outline)
    written = sum(
        1 for ch in outline for sc in ch.get("scenes", [])
        if os.path.exists(os.path.join(drafts_dir, f"scene_{sc['scene_id']}.md"))
    )
    return total, written


@router.post("/project/new")
def new_project(req: NewProjectRequest):
    projects_base = os.path.expanduser("~/Documents/NovelWriter_projects")
    project_path = os.path.join(projects_base, req.folder_name)
    if os.path.exists(project_path):
        raise HTTPException(400, f"Folder '{req.folder_name}' already exists at {projects_base}")
    os.makedirs(project_path, exist_ok=True)
    apply_project_path(project_path)
    state.set_project_path(project_path)

    def run_init():
        from generators import Generator
        from state_manager import StateManager
        from config import Config
        g = Generator()
        sm = StateManager()
        state.job_runner.log(f"Generating plot for: {req.idea[:80]}...")
        plot = g.generate_plot(req.idea)
        sm.save_text(Config.PLOT_FILE, plot)
        state.job_runner.log("Plot generated. Building characters...")
        g.generate_characters(plot)
        state.job_runner.log("Characters created. Building world settings...")
        g.generate_world(plot)
        state.job_runner.log("Init complete.")

    if not state.job_runner.submit("init", run_init):
        raise HTTPException(409, "A job is already running")
    return {"ok": True, "path": project_path}


@router.post("/project/load")
def load_project(req: LoadProjectRequest):
    path = os.path.expanduser(req.path)
    if not os.path.isdir(path):
        raise HTTPException(400, f"Directory not found: {path}")
    markers = ["plot.md", "outline.json", "drafts", "characters.json"]
    if not any(os.path.exists(os.path.join(path, m)) for m in markers):
        raise HTTPException(400, "No NovelWriter files found in that directory")
    apply_project_path(path)
    apply_overrides(os.path.join(path, "config_override.json"))
    state.set_project_path(path)
    return {"ok": True, "path": path, "stage": _detect_stage(path)}


@router.get("/project/state")
def get_project_state():
    path = state.get_project_path()
    if not path:
        raise HTTPException(400, "No project loaded")

    plot_summary = None
    plot_file = os.path.join(path, "plot.md")
    if os.path.exists(plot_file):
        with open(plot_file, encoding="utf-8") as f:
            plot_summary = f.read(500)

    characters = []
    chars_file = os.path.join(path, "characters.json")
    if os.path.exists(chars_file):
        with open(chars_file, encoding="utf-8") as f:
            chars_data = json.load(f)
        if isinstance(chars_data, list):
            characters = [c.get("name", str(c)) for c in chars_data]
        elif isinstance(chars_data, dict):
            characters = list(chars_data.keys())

    outline = []
    outline_file = os.path.join(path, "outline.json")
    if os.path.exists(outline_file):
        with open(outline_file, encoding="utf-8") as f:
            raw = json.load(f)
        drafts_dir = os.path.join(path, "drafts")
        for ch in raw:
            scenes = [
                {
                    "scene_id": sc["scene_id"],
                    "description": sc.get("description", ""),
                    "written": os.path.exists(
                        os.path.join(drafts_dir, f"scene_{sc['scene_id']}.md")
                    ),
                }
                for sc in ch.get("scenes", [])
            ]
            outline.append({
                "chapter_id": ch.get("chapter_id", 0),
                "chapter_title": ch.get("chapter_title", ""),
                "scenes": scenes,
            })

    total, written = _count_scenes(path)
    return {
        "path": path,
        "stage": _detect_stage(path),
        "plot_summary": plot_summary,
        "characters": characters,
        "outline": outline,
        "scenes_written": written,
        "scenes_total": total,
    }
```

- [ ] **Step 3: Create backend/routers/pipeline.py**

```python
# backend/routers/pipeline.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend import state

router = APIRouter()


class WriteRequest(BaseModel):
    count: int = 1


class ReconstructRequest(BaseModel):
    scene_id: int


@router.post("/outline")
def run_outline():
    if not state.get_project_path():
        raise HTTPException(400, "No project loaded")

    def job():
        from generators import Generator
        from state_manager import StateManager
        g = Generator()
        sm = StateManager()
        state.job_runner.log("Loading plot and characters...")
        plot = sm.load_plot()
        characters = sm.load_characters()
        world = sm.load_world()
        if not plot:
            raise ValueError("Plot not found. Run init first.")
        state.job_runner.log("Generating outline...")
        outline = g.generate_outline(plot, characters, world)
        state.job_runner.log(f"Outline complete: {len(outline)} chapters.")

    if not state.job_runner.submit("outline", job):
        raise HTTPException(409, "A job is already running")
    return {"ok": True}


@router.post("/write")
def run_write(req: WriteRequest):
    if not state.get_project_path():
        raise HTTPException(400, "No project loaded")

    def job():
        from generators import Generator
        from state_manager import StateManager
        from config import Config
        import os
        g = Generator()
        sm = StateManager()
        outline = sm.load_outline()
        characters = sm.load_characters()
        world = sm.load_world()
        current_state = sm.load_state() or {}
        if not outline:
            raise ValueError("Outline not found. Run outline first.")
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
                if scenes_written >= req.count:
                    state.job_runner.log(f"Reached limit of {req.count} scene(s).")
                    return
                state.job_runner.log(f"Writing scene {scene_id}...")
                os.makedirs(Config.DRAFTS_DIR, exist_ok=True)
                scene_text = g.write_scene(scene, previous_summary, characters, world, current_state)
                title = g.generate_title(scene_text)
                sm.save_text(scene_file, f"# {title}\n\n{scene_text}")
                current_state = g.update_state(scene_text, current_state, characters)
                sm.save_state(current_state)
                sm.save_state_snapshot(current_state, scene_id)
                summary = g.summarize_scene(scene_text)
                sm.save_text(summary_file, summary)
                previous_summary = summary
                scenes_written += 1
                state.job_runner.log(f"Scene {scene_id} saved.")
        if scenes_written == 0:
            state.job_runner.log("All scenes already written.")

    if not state.job_runner.submit("write", job):
        raise HTTPException(409, "A job is already running")
    return {"ok": True}


@router.post("/reconstruct")
def run_reconstruct(req: ReconstructRequest):
    if not state.get_project_path():
        raise HTTPException(400, "No project loaded")

    def job():
        from generators import Generator
        from state_manager import StateManager
        from config import Config
        import os
        g = Generator()
        sm = StateManager()
        state.job_runner.log(f"Reconstructing state up to scene {req.scene_id}...")
        characters = sm.load_characters()
        new_state = g.reconstruct_state(req.scene_id, characters)
        sm.save_state(new_state)
        scene_file = os.path.join(Config.DRAFTS_DIR, f"scene_{req.scene_id}.md")
        summary_file = os.path.join(Config.DRAFTS_DIR, f"scene_{req.scene_id}_summary.txt")
        if os.path.exists(scene_file):
            state.job_runner.log("Regenerating scene summary...")
            summary = g.summarize_scene(sm.load_text(scene_file))
            sm.save_text(summary_file, summary)
        state.job_runner.log("Reconstruct complete.")

    if not state.job_runner.submit("reconstruct", job):
        raise HTTPException(409, "A job is already running")
    return {"ok": True}
```

- [ ] **Step 4: Create backend/routers/settings.py**

```python
# backend/routers/settings.py
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from backend import state
from backend.config_manager import get_settings, save_overrides

router = APIRouter()


class SettingsUpdate(BaseModel):
    ollama_base_url: Optional[str] = None
    default_model: Optional[str] = None
    context_length_size: Optional[int] = None
    think_mode: Optional[str] = None
    novel_viewpoint: Optional[str] = None
    novel_style: Optional[str] = None
    max_context_chars: Optional[int] = None


@router.get("/settings")
def get_settings_endpoint():
    return get_settings()


@router.post("/settings")
def update_settings(req: SettingsUpdate):
    project_path = state.get_project_path()
    if not project_path:
        raise HTTPException(400, "No project loaded — load a project first")
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    if not updates:
        return get_settings()
    save_overrides(os.path.join(project_path, "config_override.json"), updates)
    return get_settings()
```

- [ ] **Step 5: Create backend/routers/stream.py**

```python
# backend/routers/stream.py
import json
from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse
from backend import state

router = APIRouter()


@router.get("/stream")
async def stream():
    """SSE endpoint — streams log messages from the active job."""
    async def generator():
        async for msg in state.job_runner.stream():
            yield {"data": json.dumps(msg)}

    return EventSourceResponse(generator())
```

- [ ] **Step 6: Write and run tests for project router**

```python
# tests/test_project.py
import os
import tempfile
from fastapi.testclient import TestClient
from fastapi import FastAPI
from unittest.mock import patch
from backend.routers.project import router
import backend.state as state_module

app = FastAPI()
app.include_router(router, prefix="/api")
client = TestClient(app)


def test_load_project_invalid_path():
    resp = client.post("/api/project/load", json={"path": "/nonexistent/path"})
    assert resp.status_code == 400


def test_load_project_empty_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        resp = client.post("/api/project/load", json={"path": tmpdir})
    assert resp.status_code == 400
    assert "NovelWriter files" in resp.json()["detail"]


def test_load_project_with_plot_md():
    with tempfile.TemporaryDirectory() as tmpdir:
        open(os.path.join(tmpdir, "plot.md"), "w").close()
        resp = client.post("/api/project/load", json={"path": tmpdir})
    assert resp.status_code == 200
    assert resp.json()["ok"] is True
    assert resp.json()["stage"] == "outline"


def test_get_state_no_project():
    state_module._project_path = None
    resp = client.get("/api/project/state")
    assert resp.status_code == 400


def test_get_state_with_project():
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "plot.md"), "w") as f:
            f.write("# My plot")
        state_module._project_path = tmpdir
        resp = client.get("/api/project/state")
    assert resp.status_code == 200
    assert "stage" in resp.json()
    assert "outline" in resp.json()
```

- [ ] **Step 7: Write and run tests for pipeline router**

```python
# tests/test_pipeline.py
from fastapi.testclient import TestClient
from fastapi import FastAPI
from unittest.mock import patch
from backend.routers.pipeline import router
import backend.state as state_module

app = FastAPI()
app.include_router(router, prefix="/api")
client = TestClient(app)


def test_outline_no_project():
    state_module._project_path = None
    resp = client.post("/api/outline")
    assert resp.status_code == 400


def test_outline_submits_job(tmp_path):
    state_module._project_path = str(tmp_path)
    with patch.object(state_module.job_runner, "submit", return_value=True) as mock_submit:
        resp = client.post("/api/outline")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True
    mock_submit.assert_called_once()


def test_outline_returns_409_if_job_running(tmp_path):
    state_module._project_path = str(tmp_path)
    with patch.object(state_module.job_runner, "submit", return_value=False):
        resp = client.post("/api/outline")
    assert resp.status_code == 409


def test_write_submits_job(tmp_path):
    state_module._project_path = str(tmp_path)
    with patch.object(state_module.job_runner, "submit", return_value=True) as mock_submit:
        resp = client.post("/api/write", json={"count": 2})
    assert resp.status_code == 200
    mock_submit.assert_called_once()
```

- [ ] **Step 8: Write and run tests for settings router**

```python
# tests/test_settings.py
import os
import tempfile
from fastapi.testclient import TestClient
from fastapi import FastAPI
from backend.routers.settings import router
import backend.state as state_module

app = FastAPI()
app.include_router(router, prefix="/api")
client = TestClient(app)


def test_get_settings_returns_expected_keys():
    resp = client.get("/api/settings")
    assert resp.status_code == 200
    data = resp.json()
    assert "ollama_base_url" in data
    assert "default_model" in data
    assert "novel_viewpoint" in data


def test_post_settings_no_project():
    state_module._project_path = None
    resp = client.post("/api/settings", json={"default_model": "llama3:8b"})
    assert resp.status_code == 400


def test_post_settings_persists(tmp_path):
    state_module._project_path = str(tmp_path)
    resp = client.post("/api/settings", json={"default_model": "mistral:7b"})
    assert resp.status_code == 200
    assert os.path.exists(os.path.join(str(tmp_path), "config_override.json"))
```

- [ ] **Step 9: Run all backend tests**

```bash
python -m pytest tests/ -v
```

Expected: all tests pass. Fix any failures before continuing.

- [ ] **Step 10: Commit**

```bash
git add backend/routers/ tests/
git commit -m "feat(backend): all routers — ollama, project, pipeline, settings, stream + tests"
```

---

### Task 9: FastAPI Server Entry Point

**Files:**
- Create: `backend/server.py`

- [ ] **Step 1: Create backend/server.py**

```python
# backend/server.py
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from backend.routers import status, ollama, project, pipeline, settings, stream

app = FastAPI(title="NovelWriter UI")

app.include_router(status.router, prefix="/api")
app.include_router(ollama.router, prefix="/api")
app.include_router(project.router, prefix="/api")
app.include_router(pipeline.router, prefix="/api")
app.include_router(settings.router, prefix="/api")
app.include_router(stream.router, prefix="/api")

_BUILD_DIR = Path(__file__).parent.parent / "frontend" / "build"


@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """Serve static files or fall back to index.html for SPA routing."""
    if not _BUILD_DIR.exists():
        return {"error": "Frontend not built. Run: cd frontend && npm run build"}
    file_path = _BUILD_DIR / full_path
    if file_path.is_file():
        return FileResponse(file_path)
    return FileResponse(_BUILD_DIR / "index.html")
```

- [ ] **Step 2: Verify the server imports cleanly**

```bash
python -c "from backend.server import app; print('OK', app.title)"
```

Expected: `OK NovelWriter UI`

- [ ] **Step 3: Commit**

```bash
git add backend/server.py
git commit -m "feat(backend): FastAPI server entry point with SPA static file serving"
```

---

### Task 10: Pinokio Launcher Scripts

**Files:**
- Create: `install.js`
- Create: `start.js`
- Create: `update.js`
- Create: `reset.js`
- Create: `pinokio.js`

- [ ] **Step 1: Create install.js**

```javascript
module.exports = {
  run: [
    {
      method: "shell.run",
      params: {
        message: "git submodule update --init --recursive"
      }
    },
    {
      method: "shell.run",
      params: {
        message: "uv venv --python 3.11 env"
      }
    },
    {
      method: "shell.run",
      params: {
        venv: "env",
        message: "uv pip install fastapi 'uvicorn[standard]' requests sse-starlette"
      }
    },
    {
      method: "shell.run",
      params: {
        path: "frontend",
        message: [
          "npm install",
          "npm run build"
        ]
      }
    }
  ]
}
```

- [ ] **Step 2: Create start.js**

```javascript
module.exports = {
  daemon: true,
  run: [
    {
      method: "shell.run",
      params: {
        venv: "env",
        message: "uvicorn backend.server:app --host 127.0.0.1 --port {{port}}",
        on: [{
          event: "/(http:\\/\\/[0-9.:]+)/",
          done: true
        }]
      }
    },
    {
      method: "local.set",
      params: {
        url: "{{input.event[1]}}"
      }
    }
  ]
}
```

- [ ] **Step 3: Create update.js**

```javascript
module.exports = {
  run: [
    {
      method: "shell.run",
      params: {
        message: [
          "git pull",
          "git submodule update --remote --merge"
        ]
      }
    },
    {
      method: "shell.run",
      params: {
        venv: "env",
        message: "uv pip install --upgrade fastapi 'uvicorn[standard]' requests sse-starlette"
      }
    },
    {
      method: "shell.run",
      params: {
        path: "frontend",
        message: [
          "npm install",
          "npm run build"
        ]
      }
    }
  ]
}
```

- [ ] **Step 4: Create reset.js**

```javascript
module.exports = {
  run: [
    {
      method: "shell.run",
      params: {
        message: [
          "rm -rf env",
          "rm -rf frontend/build",
          "rm -rf frontend/node_modules"
        ]
      }
    }
  ]
}
```

- [ ] **Step 5: Create pinokio.js**

```javascript
module.exports = {
  version: "7.0",
  title: "NovelWriter UI",
  description: "[MAC/LINUX] AI-assisted novel writing. Local Ollama, no API keys. Plot → Characters → Outline → Scenes.",
  icon: "icon.png",
  menu: async (kernel, info) => {
    const envReady = info.exists("env/pyvenv.cfg");
    const frontendBuilt = info.exists("frontend/build/index.html");
    const installed = envReady && frontendBuilt;

    const running = {
      install: info.running("install.js"),
      start:   info.running("start.js"),
      update:  info.running("update.js"),
      reset:   info.running("reset.js"),
    };

    if (running.install) return [{ default: true, icon: "fa-solid fa-plug",   text: "Installing", href: "install.js" }];
    if (running.update)  return [{ default: true, icon: "fa-solid fa-rotate", text: "Updating",   href: "update.js" }];
    if (running.reset)   return [{ default: true, icon: "fa-solid fa-eraser", text: "Resetting",  href: "reset.js"  }];

    if (!installed) {
      return [{ default: true, icon: "fa-solid fa-plug", text: "Install", href: "install.js" }];
    }

    if (running.start) {
      const local = info.local("start.js");
      if (local && local.url) {
        return [
          { default: true, icon: "fa-solid fa-rocket",         text: "Open Panel", href: local.url    },
          { icon: "fa-solid fa-terminal",                       text: "Terminal",   href: "start.js"  },
          { icon: "fa-solid fa-rotate",                         text: "Update",     href: "update.js" },
          { icon: "fa-regular fa-circle-xmark",                 text: "Reset",      href: "reset.js"  },
        ];
      }
      return [{ default: true, icon: "fa-solid fa-terminal", text: "Starting...", href: "start.js" }];
    }

    return [
      { default: true, icon: "fa-solid fa-power-off",  text: "Start",  href: "start.js"  },
      { icon: "fa-solid fa-rotate",                     text: "Update", href: "update.js" },
      { icon: "fa-regular fa-circle-xmark",             text: "Reset",  href: "reset.js"  },
    ];
  }
};
```

- [ ] **Step 6: Commit**

```bash
git add install.js start.js update.js reset.js pinokio.js
git commit -m "feat(pinokio): install/start/update/reset/pinokio launcher scripts"
```

---

### Task 11: SvelteKit + shadcn-svelte Setup

**Files:**
- Create: `frontend/` (SvelteKit project)

- [ ] **Step 1: Scaffold SvelteKit**

```bash
cd ~/pinokio/api/novelwriter-ui.git
npx sv create frontend --template minimal --types ts --no-add-ons
```

Select TypeScript when prompted; decline all optional add-ons.

- [ ] **Step 2: Install shadcn-svelte**

```bash
cd frontend
npx shadcn-svelte@latest init
```

When prompted: Style → **Default**, Base color → **Slate**, CSS variables → **Yes**

- [ ] **Step 3: Add required shadcn-svelte components**

```bash
npx shadcn-svelte@latest add button card input textarea select badge progress label tabs alert skeleton separator
```

- [ ] **Step 4: Install adapter-static**

```bash
npm install -D @sveltejs/adapter-static
```

- [ ] **Step 5: Replace svelte.config.js**

```javascript
import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

const config = {
  preprocess: vitePreprocess(),
  kit: {
    adapter: adapter({ fallback: 'index.html' })
  }
};

export default config;
```

- [ ] **Step 6: Verify build succeeds**

```bash
npm run build
```

Expected: exits 0, `build/index.html` exists.

- [ ] **Step 7: Commit**

```bash
cd ~/pinokio/api/novelwriter-ui.git
git add frontend/
git commit -m "feat(frontend): SvelteKit + shadcn-svelte + adapter-static scaffold"
```

---

### Task 12: API Client + Svelte Stores

**Files:**
- Create: `frontend/src/lib/api.ts`
- Create: `frontend/src/lib/stores.ts`

- [ ] **Step 1: Create frontend/src/lib/api.ts**

```typescript
// frontend/src/lib/api.ts

export interface StatusResponse { ollama: boolean; deps: boolean; }
export interface Scene { scene_id: number; description: string; written: boolean; }
export interface Chapter { chapter_id: number; chapter_title: string; scenes: Scene[]; }
export interface ProjectStateResponse {
  path: string;
  stage: 'init' | 'outline' | 'write' | 'done';
  plot_summary: string | null;
  characters: string[];
  outline: Chapter[];
  scenes_written: number;
  scenes_total: number;
}
export interface Settings {
  ollama_base_url: string; default_model: string;
  context_length_size: number; think_mode: string;
  novel_viewpoint: string; novel_style: string; max_context_chars: number;
}

async function req<T>(method: string, path: string, body?: unknown): Promise<T> {
  const opts: RequestInit = { method, headers: { 'Content-Type': 'application/json' } };
  if (body !== undefined) opts.body = JSON.stringify(body);
  const r = await fetch(`/api${path}`, opts);
  if (!r.ok) {
    const err = await r.json().catch(() => ({ detail: r.statusText }));
    throw new Error(err.detail ?? r.statusText);
  }
  return r.json();
}

export const api = {
  getStatus:      () => req<StatusResponse>('GET', '/status'),
  installPrereqs: () => req<{ ok: boolean }>('POST', '/prereqs/install'),
  getModels:      () => req<{ models: string[]; error?: string }>('GET', '/ollama/models'),
  newProject:     (idea: string, folder_name: string) =>
                    req<{ ok: boolean; path: string }>('POST', '/project/new', { idea, folder_name }),
  loadProject:    (path: string) =>
                    req<{ ok: boolean; path: string; stage: string }>('POST', '/project/load', { path }),
  getProjectState: () => req<ProjectStateResponse>('GET', '/project/state'),
  runOutline:     () => req<{ ok: boolean }>('POST', '/outline'),
  runWrite:       (count: number) => req<{ ok: boolean }>('POST', '/write', { count }),
  runReconstruct: (scene_id: number) => req<{ ok: boolean }>('POST', '/reconstruct', { scene_id }),
  getSettings:    () => req<Settings>('GET', '/settings'),
  saveSettings:   (s: Partial<Settings>) => req<Settings>('POST', '/settings', s),
};
```

- [ ] **Step 2: Create frontend/src/lib/stores.ts**

```typescript
// frontend/src/lib/stores.ts
import { writable } from 'svelte/store';
import type { ProjectStateResponse, Settings, StatusResponse } from './api';

export const prereqStatus   = writable<StatusResponse | null>(null);
export const projectState   = writable<ProjectStateResponse | null>(null);
export const settings       = writable<Settings | null>(null);
export const jobRunning     = writable(false);
export const jobName        = writable<string | null>(null);
export const logLines       = writable<string[]>([]);

export const resetLog  = () => logLines.set([]);
export const appendLog = (line: string) => logLines.update(ls => [...ls, line]);
```

- [ ] **Step 3: Build and verify**

```bash
cd frontend && npm run build
```

- [ ] **Step 4: Commit**

```bash
cd ~/pinokio/api/novelwriter-ui.git
git add frontend/src/lib/
git commit -m "feat(frontend): typed API client and Svelte stores"
```

---

### Task 13: App Layout + Routing

**Files:**
- Create: `frontend/src/routes/+layout.ts`
- Modify: `frontend/src/routes/+layout.svelte`

- [ ] **Step 1: Create frontend/src/routes/+layout.ts**

```typescript
export const ssr = false;
```

- [ ] **Step 2: Replace frontend/src/routes/+layout.svelte**

```svelte
<script lang="ts">
  import '../app.css';
  import { page } from '$app/stores';

  const nav = [
    { label: 'Home',      href: '/',         icon: '🏠' },
    { label: 'Dashboard', href: '/project',  icon: '📖' },
    { label: 'Settings',  href: '/settings', icon: '⚙️' },
  ];
</script>

<div class="min-h-screen bg-background text-foreground flex flex-col">
  <header class="border-b px-6 py-3 flex items-center gap-6">
    <span class="font-bold text-lg">📝 NovelWriter UI</span>
    <nav class="flex gap-4">
      {#each nav as item}
        <a href={item.href}
          class="text-sm font-medium transition-colors hover:text-foreground/80
                 {$page.url.pathname === item.href ? 'text-foreground' : 'text-foreground/60'}">
          {item.icon} {item.label}
        </a>
      {/each}
    </nav>
  </header>
  <main class="flex-1 p-6"><slot /></main>
</div>
```

- [ ] **Step 3: Create placeholder routes**

`frontend/src/routes/project/+page.svelte`:
```svelte
<h1 class="text-2xl font-bold">Dashboard</h1>
<p class="text-muted-foreground">Load a project from the home screen first.</p>
```

`frontend/src/routes/settings/+page.svelte`:
```svelte
<h1 class="text-2xl font-bold">Settings</h1>
```

- [ ] **Step 4: Build and verify**

```bash
cd frontend && npm run build
```

- [ ] **Step 5: Commit**

```bash
cd ~/pinokio/api/novelwriter-ui.git
git add frontend/src/routes/
git commit -m "feat(frontend): app layout with nav bar, SPA routing, placeholder routes"
```

---

### Task 14: PrereqBar + Home Screen

**Files:**
- Create: `frontend/src/lib/components/PrereqBar.svelte`
- Modify: `frontend/src/routes/+page.svelte`

- [ ] **Step 1: Create PrereqBar.svelte**

```svelte
<!-- frontend/src/lib/components/PrereqBar.svelte -->
<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '$lib/api';
  import { prereqStatus } from '$lib/stores';
  import { Badge } from '$lib/components/ui/badge';
  import { Button } from '$lib/components/ui/button';

  let installing = false;
  let installError = '';

  onMount(async () => {
    try { prereqStatus.set(await api.getStatus()); } catch {}
  });

  async function install() {
    installing = true; installError = '';
    try {
      await api.installPrereqs();
      prereqStatus.set(await api.getStatus());
    } catch (e: any) { installError = e.message; }
    finally { installing = false; }
  }
</script>

{#if $prereqStatus}
  <div class="flex flex-wrap items-center gap-3 rounded-lg border px-4 py-2 text-sm mb-4">
    <span class="font-medium">Prerequisites:</span>
    <Badge variant={$prereqStatus.ollama ? 'default' : 'destructive'}>
      Ollama {$prereqStatus.ollama ? '✓' : '✗'}
    </Badge>
    <Badge variant={$prereqStatus.deps ? 'default' : 'destructive'}>
      Python deps {$prereqStatus.deps ? '✓' : '✗'}
    </Badge>
    {#if !$prereqStatus.deps}
      <Button size="sm" on:click={install} disabled={installing}>
        {installing ? 'Installing…' : 'Install deps'}
      </Button>
    {/if}
    {#if !$prereqStatus.ollama}
      <span class="text-muted-foreground text-xs">Start Ollama: <code>ollama serve</code></span>
    {/if}
    {#if installError}<span class="text-destructive text-xs">{installError}</span>{/if}
  </div>
{/if}
```

- [ ] **Step 2: Replace frontend/src/routes/+page.svelte**

```svelte
<script lang="ts">
  import { goto } from '$app/navigation';
  import { api } from '$lib/api';
  import { projectState } from '$lib/stores';
  import PrereqBar from '$lib/components/PrereqBar.svelte';
  import { Button } from '$lib/components/ui/button';
  import { Input } from '$lib/components/ui/input';
  import { Textarea } from '$lib/components/ui/textarea';
  import { Label } from '$lib/components/ui/label';
  import * as Card from '$lib/components/ui/card';

  let newIdea = '';
  let newFolderName = '';
  let existingPath = '';
  let newError = '';
  let loadError = '';
  let loading = false;

  $: newFolderName = newIdea.split('\n')[0].trim().slice(0, 40)
    .toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '');

  async function createProject() {
    if (!newIdea.trim()) { newError = 'Enter an idea first'; return; }
    newError = ''; loading = true;
    try {
      await api.newProject(newIdea.trim(), newFolderName.trim());
      projectState.set(await api.getProjectState());
      goto('/project');
    } catch (e: any) { newError = e.message; }
    finally { loading = false; }
  }

  async function loadProject() {
    if (!existingPath.trim()) { loadError = 'Enter a folder path'; return; }
    loadError = ''; loading = true;
    try {
      await api.loadProject(existingPath.trim());
      projectState.set(await api.getProjectState());
      goto('/project');
    } catch (e: any) { loadError = e.message; }
    finally { loading = false; }
  }
</script>

<div class="max-w-3xl mx-auto space-y-6">
  <PrereqBar />
  <h1 class="text-3xl font-bold">NovelWriter UI</h1>
  <p class="text-muted-foreground">Write a novel locally with Ollama. No API keys, no cloud.</p>

  <div class="grid md:grid-cols-2 gap-6">
    <Card.Root>
      <Card.Header>
        <Card.Title>✨ New Project</Card.Title>
        <Card.Description>Start from a fresh idea</Card.Description>
      </Card.Header>
      <Card.Content class="space-y-3">
        <div class="space-y-1">
          <Label for="idea">Your idea</Label>
          <Textarea id="idea" placeholder="A detective in a neon-lit city discovers…"
            rows={5} bind:value={newIdea} />
        </div>
        <div class="space-y-1">
          <Label for="folder">Folder name</Label>
          <Input id="folder" bind:value={newFolderName} placeholder="my_novel" />
          <p class="text-xs text-muted-foreground">Saved to ~/Documents/NovelWriter_projects/</p>
        </div>
        {#if newError}<p class="text-sm text-destructive">{newError}</p>{/if}
        <Button class="w-full" on:click={createProject} disabled={loading}>
          {loading ? 'Creating…' : 'Create Project'}
        </Button>
      </Card.Content>
    </Card.Root>

    <Card.Root>
      <Card.Header>
        <Card.Title>📂 Open Existing</Card.Title>
        <Card.Description>Continue from a folder with plot/outline/drafts</Card.Description>
      </Card.Header>
      <Card.Content class="space-y-3">
        <div class="space-y-1">
          <Label for="path">Project folder path</Label>
          <Input id="path" bind:value={existingPath}
            placeholder="/Users/you/Documents/my_novel" />
          <p class="text-xs text-muted-foreground">
            Must contain plot.md, outline.json, or a drafts/ folder
          </p>
        </div>
        {#if loadError}<p class="text-sm text-destructive">{loadError}</p>{/if}
        <Button variant="outline" class="w-full" on:click={loadProject} disabled={loading}>
          {loading ? 'Loading…' : 'Open Project'}
        </Button>
      </Card.Content>
    </Card.Root>
  </div>
</div>
```

- [ ] **Step 3: Build and verify**

```bash
cd frontend && npm run build
```

- [ ] **Step 4: Commit**

```bash
cd ~/pinokio/api/novelwriter-ui.git
git add frontend/src/
git commit -m "feat(frontend): PrereqBar component and Home screen with new/load project"
```

---

### Task 15: StageIndicator + OutlineGrid + Dashboard

**Files:**
- Create: `frontend/src/lib/components/StageIndicator.svelte`
- Create: `frontend/src/lib/components/OutlineGrid.svelte`
- Create: `frontend/src/lib/components/LogPanel.svelte`
- Modify: `frontend/src/routes/project/+page.svelte`

- [ ] **Step 1: Create StageIndicator.svelte**

```svelte
<!-- frontend/src/lib/components/StageIndicator.svelte -->
<script lang="ts">
  export let stage: 'init' | 'outline' | 'write' | 'done' = 'init';
  const stages = [
    { key: 'init', label: 'Init' }, { key: 'outline', label: 'Outline' },
    { key: 'write', label: 'Write' }, { key: 'done', label: 'Done' },
  ];
  const order = stages.map(s => s.key);
  function status(key: string) {
    const cur = order.indexOf(stage), idx = order.indexOf(key);
    return idx < cur ? 'done' : idx === cur ? 'active' : 'pending';
  }
</script>

<div class="flex items-center gap-2 flex-wrap">
  {#each stages as s, i}
    {@const st = status(s.key)}
    <div class="flex items-center gap-2">
      <div class="flex items-center gap-1.5">
        <div class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold
          {st === 'done' ? 'bg-primary text-primary-foreground' :
           st === 'active' ? 'bg-primary/70 text-primary-foreground animate-pulse' :
           'bg-muted text-muted-foreground'}">
          {st === 'done' ? '✓' : i + 1}
        </div>
        <span class="text-sm {st === 'active' ? 'font-semibold' : 'text-muted-foreground'}">
          {s.label}
        </span>
      </div>
      {#if i < stages.length - 1}<div class="w-6 h-px bg-border" />{/if}
    </div>
  {/each}
</div>
```

- [ ] **Step 2: Create OutlineGrid.svelte**

```svelte
<!-- frontend/src/lib/components/OutlineGrid.svelte -->
<script lang="ts">
  import type { Chapter } from '$lib/api';
  import { Badge } from '$lib/components/ui/badge';
  export let outline: Chapter[] = [];
</script>

{#if outline.length === 0}
  <p class="text-muted-foreground text-sm">No outline yet.</p>
{:else}
  <div class="space-y-4">
    {#each outline as chapter}
      <div>
        <p class="text-sm font-semibold mb-1.5">
          {chapter.chapter_title || `Chapter ${chapter.chapter_id}`}
        </p>
        <div class="flex flex-wrap gap-1.5">
          {#each chapter.scenes as scene}
            <Badge variant={scene.written ? 'default' : 'outline'}
              class="text-xs cursor-default" title={scene.description}>
              S{scene.scene_id} {scene.written ? '✓' : '○'}
            </Badge>
          {/each}
        </div>
      </div>
    {/each}
  </div>
{/if}
```

- [ ] **Step 3: Create LogPanel.svelte**

```svelte
<!-- frontend/src/lib/components/LogPanel.svelte -->
<script lang="ts">
  import { createEventDispatcher, onDestroy } from 'svelte';
  import { jobRunning, jobName, logLines, appendLog, resetLog } from '$lib/stores';
  import * as Card from '$lib/components/ui/card';
  import { Button } from '$lib/components/ui/button';

  const dispatch = createEventDispatcher();
  let logEl: HTMLElement;
  let es: EventSource | null = null;

  $: if ($jobRunning && !es) startStream();

  function startStream() {
    es = new EventSource('/api/stream');
    es.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.type === 'log') {
        appendLog(msg.line);
        setTimeout(() => logEl?.scrollTo({ top: logEl.scrollHeight, behavior: 'smooth' }), 50);
      }
      if (msg.type === 'done') { appendLog('✓ Done'); stopStream(); dispatch('done'); }
      if (msg.type === 'error') { appendLog(`✗ Error: ${msg.error}`); stopStream(); dispatch('done'); }
    };
    es.onerror = () => { stopStream(); dispatch('done'); };
  }

  function stopStream() { es?.close(); es = null; jobRunning.set(false); }
  onDestroy(stopStream);
</script>

<Card.Root>
  <Card.Header class="pb-2 flex flex-row items-center justify-between">
    <Card.Title class="text-base flex items-center gap-2">
      Log
      {#if $jobRunning}
        <span class="w-2 h-2 rounded-full bg-primary animate-ping inline-block" />
      {/if}
    </Card.Title>
    <Button variant="ghost" size="sm" on:click={resetLog} disabled={$jobRunning}>Clear</Button>
  </Card.Header>
  <Card.Content>
    <div bind:this={logEl}
      class="bg-muted rounded-md p-3 h-40 overflow-y-auto font-mono text-xs space-y-0.5">
      {#if $logLines.length === 0}
        <p class="text-muted-foreground">No output yet.</p>
      {:else}
        {#each $logLines as line}<p class="leading-snug">{line}</p>{/each}
      {/if}
    </div>
  </Card.Content>
</Card.Root>
```

- [ ] **Step 4: Replace frontend/src/routes/project/+page.svelte**

```svelte
<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { api } from '$lib/api';
  import { projectState, jobRunning, jobName, resetLog } from '$lib/stores';
  import StageIndicator from '$lib/components/StageIndicator.svelte';
  import OutlineGrid from '$lib/components/OutlineGrid.svelte';
  import LogPanel from '$lib/components/LogPanel.svelte';
  import { Button } from '$lib/components/ui/button';
  import { Input } from '$lib/components/ui/input';
  import * as Card from '$lib/components/ui/card';
  import { Progress } from '$lib/components/ui/progress';
  import { Badge } from '$lib/components/ui/badge';

  let writeCount = 1;
  let reconstructId = 1;
  let actionError = '';

  onMount(async () => {
    try { projectState.set(await api.getProjectState()); }
    catch { goto('/'); }
  });

  async function runAction(name: string, fn: () => Promise<unknown>) {
    actionError = '';
    jobName.set(name); jobRunning.set(true); resetLog();
    try { await fn(); }
    catch (e: any) { actionError = e.message; jobRunning.set(false); jobName.set(null); }
  }

  async function afterJob() {
    jobRunning.set(false); jobName.set(null);
    projectState.set(await api.getProjectState());
  }

  $: progress = $projectState && $projectState.scenes_total > 0
    ? Math.round(($projectState.scenes_written / $projectState.scenes_total) * 100)
    : 0;
</script>

{#if !$projectState}
  <p class="text-muted-foreground">Loading project…</p>
{:else}
  <div class="flex gap-6">
    <aside class="w-56 shrink-0 space-y-4">
      <div>
        <p class="text-xs text-muted-foreground uppercase tracking-wide mb-1">Project</p>
        <p class="font-semibold text-sm">{$projectState.path.split('/').pop()}</p>
        <p class="text-xs text-muted-foreground break-all">{$projectState.path}</p>
      </div>
      <div>
        <p class="text-xs text-muted-foreground uppercase tracking-wide mb-2">Pipeline</p>
        <StageIndicator stage={$projectState.stage} />
      </div>
      <Button variant="ghost" size="sm" class="w-full justify-start" on:click={() => goto('/')}>
        ← Change project
      </Button>
    </aside>

    <div class="flex-1 space-y-4">
      <!-- Action bar -->
      <Card.Root>
        <Card.Header class="pb-2"><Card.Title class="text-base">Actions</Card.Title></Card.Header>
        <Card.Content class="flex flex-wrap items-center gap-2">
          {#if $projectState.stage === 'init' || $projectState.stage === 'outline'}
            <Button on:click={() => runAction('outline', api.runOutline)} disabled={$jobRunning}>
              Generate Outline
            </Button>
          {/if}
          {#if $projectState.stage === 'write'}
            <Button on:click={() => runAction('write', () => api.runWrite(1))} disabled={$jobRunning}>
              Write Next Scene
            </Button>
            <div class="flex items-center gap-1">
              <Input type="number" min="1" max="20" bind:value={writeCount} class="w-20 h-8 text-sm" />
              <Button variant="outline" size="sm"
                on:click={() => runAction('write', () => api.runWrite(writeCount))}
                disabled={$jobRunning}>
                Write {writeCount}
              </Button>
            </div>
          {/if}
          {#if $projectState.stage === 'write' || $projectState.stage === 'done'}
            <div class="flex items-center gap-1 ml-2">
              <Input type="number" min="1" bind:value={reconstructId} class="w-20 h-8 text-sm"
                placeholder="Scene #" />
              <Button variant="outline" size="sm"
                on:click={() => runAction('reconstruct', () => api.runReconstruct(reconstructId))}
                disabled={$jobRunning}>
                Reconstruct
              </Button>
            </div>
          {/if}
          {#if $jobRunning}
            <Badge variant="secondary" class="animate-pulse">⚙️ {$jobName}…</Badge>
          {/if}
          {#if $projectState.stage === 'done'}
            <Badge>✓ Complete</Badge>
          {/if}
          {#if actionError}
            <p class="text-sm text-destructive w-full">{actionError}</p>
          {/if}
        </Card.Content>
      </Card.Root>

      <!-- Stats -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Card.Root class="p-4">
          <p class="text-xs text-muted-foreground">Stage</p>
          <p class="font-semibold capitalize">{$projectState.stage}</p>
        </Card.Root>
        <Card.Root class="p-4">
          <p class="text-xs text-muted-foreground">Characters</p>
          <p class="font-semibold">{$projectState.characters.length}</p>
        </Card.Root>
        <Card.Root class="p-4">
          <p class="text-xs text-muted-foreground">Scenes</p>
          <p class="font-semibold">{$projectState.scenes_written} / {$projectState.scenes_total}</p>
        </Card.Root>
        <Card.Root class="p-4">
          <p class="text-xs text-muted-foreground">Progress</p>
          <Progress value={progress} class="mt-1" />
        </Card.Root>
      </div>

      <!-- Outline -->
      <Card.Root>
        <Card.Header class="pb-2"><Card.Title class="text-base">Outline</Card.Title></Card.Header>
        <Card.Content><OutlineGrid outline={$projectState.outline} /></Card.Content>
      </Card.Root>

      <!-- Plot excerpt -->
      {#if $projectState.plot_summary}
        <Card.Root>
          <Card.Header class="pb-2"><Card.Title class="text-base">Plot (excerpt)</Card.Title></Card.Header>
          <Card.Content>
            <p class="text-sm text-muted-foreground whitespace-pre-wrap">{$projectState.plot_summary}</p>
          </Card.Content>
        </Card.Root>
      {/if}

      <LogPanel on:done={afterJob} />
    </div>
  </div>
{/if}
```

- [ ] **Step 5: Build and verify**

```bash
cd frontend && npm run build
```

- [ ] **Step 6: Commit**

```bash
cd ~/pinokio/api/novelwriter-ui.git
git add frontend/src/
git commit -m "feat(frontend): Dashboard with StageIndicator, OutlineGrid, LogPanel, action bar"
```

---

### Task 16: Settings Screen

**Files:**
- Modify: `frontend/src/routes/settings/+page.svelte`

- [ ] **Step 1: Replace the settings placeholder**

```svelte
<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '$lib/api';
  import type { Settings } from '$lib/api';
  import { settings } from '$lib/stores';
  import { Button } from '$lib/components/ui/button';
  import { Input } from '$lib/components/ui/input';
  import { Label } from '$lib/components/ui/label';
  import * as Select from '$lib/components/ui/select';
  import * as Card from '$lib/components/ui/card';

  let form: Settings = {
    ollama_base_url: 'http://localhost:11434', default_model: '',
    context_length_size: 100000, think_mode: 'high',
    novel_viewpoint: 'Third person omniscient',
    novel_style: 'Not specified', max_context_chars: 4000,
  };
  let models: string[] = [];
  let saving = false, saved = false, error = '';
  const thinkModes = ['off', 'low', 'medium', 'high'];

  onMount(async () => {
    try { form = { ...(await api.getSettings()) }; } catch {}
    try { models = (await api.getModels()).models; } catch {}
  });

  async function save() {
    saving = true; saved = false; error = '';
    try {
      settings.set(await api.saveSettings(form));
      saved = true;
      setTimeout(() => saved = false, 2500);
    } catch (e: any) { error = e.message; }
    finally { saving = false; }
  }
</script>

<div class="max-w-xl space-y-6">
  <h1 class="text-2xl font-bold">Settings</h1>
  <p class="text-muted-foreground text-sm">
    Saved to <code>config_override.json</code> in the active project folder.
    Load a project before saving.
  </p>

  <Card.Root>
    <Card.Header><Card.Title class="text-base">Ollama</Card.Title></Card.Header>
    <Card.Content class="space-y-3">
      <div class="space-y-1">
        <Label for="url">Base URL</Label>
        <Input id="url" bind:value={form.ollama_base_url} />
      </div>
      <div class="space-y-1">
        <Label>Model</Label>
        {#if models.length > 0}
          <Select.Root bind:value={form.default_model}>
            <Select.Trigger class="w-full"><Select.Value placeholder="Select a model…" /></Select.Trigger>
            <Select.Content>
              {#each models as m}<Select.Item value={m}>{m}</Select.Item>{/each}
            </Select.Content>
          </Select.Root>
        {:else}
          <Input bind:value={form.default_model} placeholder="e.g. llama3.1:8b" />
          <p class="text-xs text-muted-foreground">Ollama not reachable — enter model name manually</p>
        {/if}
      </div>
      <div class="space-y-1">
        <Label for="ctx">Context length (tokens)</Label>
        <Input id="ctx" type="number" bind:value={form.context_length_size} />
      </div>
      <div class="space-y-1">
        <Label>Think mode</Label>
        <Select.Root bind:value={form.think_mode}>
          <Select.Trigger class="w-full"><Select.Value /></Select.Trigger>
          <Select.Content>
            {#each thinkModes as t}<Select.Item value={t}>{t}</Select.Item>{/each}
          </Select.Content>
        </Select.Root>
      </div>
    </Card.Content>
  </Card.Root>

  <Card.Root>
    <Card.Header><Card.Title class="text-base">Novel</Card.Title></Card.Header>
    <Card.Content class="space-y-3">
      <div class="space-y-1">
        <Label for="vp">Viewpoint</Label>
        <Input id="vp" bind:value={form.novel_viewpoint} />
      </div>
      <div class="space-y-1">
        <Label for="style">Style</Label>
        <Input id="style" bind:value={form.novel_style} placeholder="e.g. Light Novel, Literary…" />
      </div>
      <div class="space-y-1">
        <Label for="maxctx">Max context chars</Label>
        <Input id="maxctx" type="number" bind:value={form.max_context_chars} />
      </div>
    </Card.Content>
  </Card.Root>

  {#if error}<p class="text-sm text-destructive">{error}</p>{/if}
  {#if saved}<p class="text-sm text-green-600">Saved ✓</p>{/if}
  <Button on:click={save} disabled={saving}>{saving ? 'Saving…' : 'Save Settings'}</Button>
</div>
```

- [ ] **Step 2: Build and verify**

```bash
cd frontend && npm run build
```

- [ ] **Step 3: Commit**

```bash
cd ~/pinokio/api/novelwriter-ui.git
git add frontend/src/routes/settings/+page.svelte
git commit -m "feat(frontend): Settings screen with Ollama model dropdown and all config fields"
```

---

### Task 17: Final Integration Test + Push to GitHub

- [ ] **Step 1: Run the full backend test suite**

```bash
cd ~/pinokio/api/novelwriter-ui.git
python -m pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 2: Start the server and smoke-test**

```bash
source env/bin/activate
uvicorn backend.server:app --host 127.0.0.1 --port 8765
```

In a second terminal:

```bash
# Status endpoint
curl -s http://127.0.0.1:8765/api/status | python3 -m json.tool
# Expected: {"ollama": bool, "deps": true}

# Models endpoint
curl -s http://127.0.0.1:8765/api/ollama/models | python3 -m json.tool
# Expected: {"models": [...]} or {"models": [], "error": "..."}

# SPA
curl -s http://127.0.0.1:8765/ | head -3
# Expected: <!doctype html>
```

Kill server: `Ctrl+C`

- [ ] **Step 3: Update README.md**

```markdown
# NovelWriter UI

A Pinokio app wrapping [NovelWriter](https://github.com/KudoShusak/NovelWriter) with a
SvelteKit + shadcn-svelte web interface. Write full novels locally with Ollama — no API
keys, no cloud.

## Features
- **New project** — type an idea, generate plot + characters + outline automatically
- **Load existing** — point to any folder with `plot.md`, `outline.json`, or `drafts/`
- **Dashboard** — stage indicator, outline grid, scene status, progress bar
- **Live log** — watch scene generation in real time via SSE
- **Settings** — Ollama URL, model picker, context length, think mode, style, viewpoint
- **Prerequisite check** — inline install button if Python deps are missing

## Requirements
- [Pinokio](https://pinokio.computer)
- [Ollama](https://ollama.com) + at least one model: `ollama pull llama3.1:8b`

## Quick Start
1. Install from Pinokio — click **Install**, then **Start**, then **Open Panel**
2. Make sure Ollama is running
3. Create a new project or load an existing one

## API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/api/status` | GET | Ollama + dep health check |
| `/api/ollama/models` | GET | List pulled Ollama models |
| `/api/project/new` | POST | Create project from idea text |
| `/api/project/load` | POST | Load existing project folder |
| `/api/project/state` | GET | Current plot/outline/progress |
| `/api/outline` | POST | Generate chapter/scene outline |
| `/api/write` | POST | Write N scenes |
| `/api/reconstruct` | POST | Rebuild state from edited scene |
| `/api/stream` | GET | SSE log stream |
| `/api/settings` | GET/POST | Read/write config override |

## Development

```bash
python -m pytest tests/ -v        # backend tests
cd frontend && npm run dev         # frontend dev server
cd frontend && npm run build       # production build
```
```

- [ ] **Step 4: Create the GitHub repo and push**

```bash
cd ~/pinokio/api/novelwriter-ui.git
gh repo create HammerOfSteel/novelwriter-ui --public \
  --description "NovelWriter web UI — SvelteKit + FastAPI Pinokio app"
git remote add origin https://github.com/HammerOfSteel/novelwriter-ui.git
git push -u origin main
```

- [ ] **Step 5: Verify Pinokio picks it up**

Open Pinokio. The `novelwriter-ui.git` folder in `~/pinokio/api/` should appear automatically. Confirm it shows **Install** button. Click Install, then Start, then Open Panel — verify the Home screen loads.
