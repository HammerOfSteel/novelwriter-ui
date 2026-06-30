# NovelWriter UI

A Pinokio app wrapping [NovelWriter](https://github.com/KudoShusak/NovelWriter) with a polished dark-themed web UI.

Generates full novels (70k–100k words) **entirely locally** using Ollama — plot, characters, world, chapter outline, and scene-by-scene prose.

---

## Features

| | |
|---|---|
| **New Novel** | Enter an idea, pick a folder name, and let the AI generate plot, characters, world, and outline before writing scene by scene. |
| **Import Existing** | Point at any directory that already contains `.md` files (chapters in subfolders, flat files — any structure). The app scans the content, copies it in, and uses the LLM to extract the plot, characters, and world, then continues from where you left off. |
| **Settings** | Per-project `config_override.json`: Ollama URL, model, context length, think mode, language (English / Japanese), viewpoint, and writing style. |
| **Live Logs** | Every generation step streams in real-time via SSE to a collapsible log panel at the bottom of the dashboard. |
| **Pipeline view** | Sidebar stage indicator — Init → Outline → Write → Done — with checkmarks and progress bar. |

---

## Requirements

- [Pinokio](https://pinokio.computer) (for one-click install/run)
- [Ollama](https://ollama.ai) running locally with at least one model pulled  
  e.g. `ollama pull llama3.2`

---

## Usage

### One-click (Pinokio)

1. Open Pinokio → **Discover** → search for *NovelWriter UI* — or add the repo URL directly.
2. Click **Install** (installs Python venv, builds the SvelteKit frontend).
3. Click **Start** → **Open Panel**.

### Development / Manual

```bash
# Backend
cd /path/to/novelwriter-ui.git
python -m venv env
source env/bin/activate
pip install -r requirements.txt
uvicorn backend.server:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev          # dev server with HMR on :5173 (proxies /api → :8000)
# or
npm run build        # static build served by FastAPI
```

---

## Architecture

```
novelwriter-ui.git/
├── novelwriter/              ← git submodule (NovelWriter engine, unchanged)
├── backend/
│   ├── server.py             ← FastAPI app + static SPA serving
│   ├── state.py              ← global singletons (project path, job runner)
│   ├── config_manager.py     ← per-project config_override.json management
│   ├── job_runner.py         ← background thread + SSE log queue
│   ├── generators_en.py      ← English-prompt Generator subclass
│   └── routers/
│       ├── status.py         ← GET /api/status
│       ├── ollama.py         ← GET /api/ollama/models
│       ├── project.py        ← new · load · scan · import · close
│       ├── pipeline.py       ← init · outline · write · reconstruct · analyze
│       ├── settings.py       ← GET/POST /api/settings
│       └── stream.py         ← GET /api/stream (SSE)
├── frontend/
│   ├── src/
│   │   ├── routes/
│   │   │   ├── +page.svelte          ← Home (new novel + open/import)
│   │   │   ├── project/+page.svelte  ← Dashboard
│   │   │   └── settings/+page.svelte ← Settings
│   │   └── lib/
│   │       ├── api.ts                ← typed fetch wrappers
│   │       ├── stores.ts             ← Svelte stores
│   │       └── components/           ← PrereqBar · StageIndicator · OutlineGrid · LogPanel
│   └── build/                        ← compiled output (served by FastAPI)
├── install.js · start.js · update.js · reset.js · pinokio.js
├── requirements.txt
└── TODO.md
```

**Single port, single process.** FastAPI serves both the REST API (`/api/*`) and the compiled SvelteKit app (`/`). The `novelwriter/` submodule is imported directly — no subprocess spawning. `Config.BASE_DIR` is monkey-patched at runtime to the currently loaded project folder.

---

## Import workflow

If your writing project is just a folder of `.md` files:

1. Home page → **Open Project** → paste the path → **Scan**
2. The app detects chapter folders and root files, shows a summary
3. Click **Import & Continue** → files are copied into a new NovelWriter project under `~/NovelWriter/<name>`
4. On the Dashboard, click **🔍 Analyse Content** to run the LLM over your existing text and generate `plot.md`, `characters.json`, `world.json`, and `outline.json`
5. Continue writing new scenes from where you left off

---

## Configuration

Each project stores overrides in `<project-dir>/config_override.json`:

| Key | Default | Description |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `DEFAULT_MODEL` | — | Model name (e.g. `llama3.2:latest`) |
| `CONTEXT_LENGTH_SIZE` | `100000` | Token context window |
| `THINK_MODE` | `high` | `off` / `low` / `medium` / `high` |
| `NOVEL_LANGUAGE` | `English` | `English` or `Japanese` |
| `NOVEL_VIEWPOINT` | `Third person omniscient` | Narrative POV |
| `NOVEL_STYLE` | `Literary fiction` | Genre / prose style hint |
| `MAX_CONTEXT_CHARS` | `4000` | Characters of context passed per scene prompt |

