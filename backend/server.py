"""
NovelWriter UI — FastAPI application entry point.

Serves the SvelteKit compiled frontend as static files and exposes the
/api/* routes. NovelWriter modules are imported directly (no subprocess).
"""
import sys
import os

# Ensure the novelwriter/ submodule directory is importable
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "novelwriter"))

from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.types import Scope

from backend.routers import status, ollama, project, pipeline, settings, stream, test_connection
from backend.debug_logger import dlog


# ---------------------------------------------------------------------------
# SPA-aware static file server
# ---------------------------------------------------------------------------

class SPAStaticFiles(StaticFiles):
    """
    Extends StaticFiles so that any path that doesn't match a real file
    (e.g. /settings, /project) falls back to index.html, enabling
    client-side routing in the SvelteKit SPA.
    """

    async def get_response(self, path: str, scope: Scope):  # type: ignore[override]
        try:
            response = await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            if exc.status_code == 404:
                response = await super().get_response("index.html", scope)
            else:
                raise
        # Never cache index.html so the browser always picks up rebuilt assets
        if path in ("", "index.html"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        return response

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="NovelWriter UI",
    version="1.0.0",
    description="AI-assisted novel writing — local Ollama backend",
)

# Allow local SvelteKit dev server to talk to the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers  (must be registered BEFORE the static mount)
# ---------------------------------------------------------------------------

app.include_router(status.router, prefix="/api", tags=["status"])
app.include_router(ollama.router, prefix="/api", tags=["llm"])
app.include_router(test_connection.router, prefix="/api", tags=["llm"])
app.include_router(project.router, prefix="/api", tags=["project"])
app.include_router(pipeline.router, prefix="/api", tags=["pipeline"])
app.include_router(settings.router, prefix="/api", tags=["settings"])
app.include_router(stream.router, prefix="/api", tags=["stream"])


@app.on_event("startup")
async def _on_startup():
    import logging
    logging.getLogger("novelwriter.debug").setLevel(logging.DEBUG)
    # Ensure uvicorn propagates debug logs
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    dlog("server", event="startup", root=str(_ROOT))

# ---------------------------------------------------------------------------
# Static file serving (SPA fallback)
# ---------------------------------------------------------------------------

FRONTEND_BUILD = Path(_ROOT) / "frontend" / "build"

if FRONTEND_BUILD.exists():
    app.mount(
        "/",
        SPAStaticFiles(directory=str(FRONTEND_BUILD), html=True),
        name="static",
    )
else:
    @app.get("/")
    async def root():
        return JSONResponse(
            {
                "message": (
                    "NovelWriter UI API is running. "
                    "The frontend has not been built yet — "
                    "run `npm run build` inside the frontend/ directory."
                )
            }
        )
