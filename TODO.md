# NovelWriter UI — TODO

## Phase 1 ✅ Fork + repo setup
## Phase 2 ✅ Pinokio launcher scripts (`install.js` · `start.js` · `update.js` · `reset.js` · `pinokio.js`)
## Phase 3 ✅ FastAPI backend skeleton (all endpoints, job runner, SSE stream)
## Phase 4 ✅ SvelteKit app + Tailwind CSS setup
## Phase 5 ✅ Home screen: New Novel form + Open/Import card + prerequisite bar
## Phase 6 ✅ Dashboard: sidebar, stage pipeline indicator, four panels (plot/chars/outline/progress)
## Phase 7 ✅ Action bar — context-sensitive buttons per pipeline stage
## Phase 8 ✅ Live log panel (SSE → auto-scrolling LogPanel component)
## Phase 9 ✅ Settings screen + Ollama model dropdown

---

## In Progress / Next

### Feature: Import Existing Directory  ✅ (backend + UI built)
- [x] `POST /api/project/scan` — preview any directory, detect type
- [x] `POST /api/project/import` — copy .md files as scene_N.md, create project
- [x] `POST /api/analyze` — LLM analysis of imported content → plot/characters/world/outline
- [ ] **Test** the full import → analyse → continue writing flow end-to-end
- [ ] Add per-scene word count and preview tooltip in the Outline grid

### Feature: English language support  ✅ (backend)
- [x] `backend/generators_en.py` — all prompts rewritten in English
- [x] `NOVEL_LANGUAGE` setting (English / Japanese) wired through the pipeline
- [ ] Smoke-test English generation with a local model

### Phase 10 — Polish
- [ ] Add `open_file` endpoint (`POST /api/open?path=...`) so clicking a written scene opens the file in the OS default app
- [ ] Error boundary / empty state components in the frontend
- [ ] Recent projects list on the Home screen (persisted to `~/.novelwriter-ui.json`)
- [ ] Dark-mode icon + favicon (creative writing themed)
- [ ] Mobile / narrow-viewport layout pass
- [ ] Unit tests for `config_manager`, `job_runner`, `project` router, `pipeline` router

### Phase 11 — Nice-to-have
- [ ] In-browser Markdown viewer / editor for scene files
- [ ] Export novel: concatenate all `scene_N.md` files → single `.md` or `.docx`
- [ ] Custom system prompt / persona field in Settings
- [ ] Multi-model routing (e.g. fast model for summaries, large model for scenes)
- [ ] Chapter-level rewrite: select a chapter and regenerate all its scenes with a new direction prompt
