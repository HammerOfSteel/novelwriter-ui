"""
/api/stream        — SSE log stream from the running job
/api/job/status    — current job status (polling fallback)
/api/open          — open a file in the OS default application
"""
import json
import os
import subprocess
import sys

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

import backend.state as state
from backend.debug_logger import dlog

router = APIRouter()


@router.get("/stream")
async def stream_logs():
    """
    Server-Sent Events endpoint.
    Each event is a JSON object on the `data:` line.

    Event types:
      {"type": "log",       "message": "..."}
      {"type": "done",      "message": "Job complete."}
      {"type": "error",     "message": "..."}
      {"type": "heartbeat"}
    """
    runner = state.get_job_runner()
    dlog("sse", event="connect", job=runner.job_name, is_running=runner.is_running)

    async def _generate():
        for item in runner.sse_generator():
            dlog("sse", event="emit", type=item.get("type"))
            yield f"data: {json.dumps(item)}\n\n"
        dlog("sse", event="disconnect")

    return StreamingResponse(
        _generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.get("/job/status")
async def job_status():
    """Polling fallback: returns the current job runner state."""
    runner = state.get_job_runner()
    return {
        "status": runner.status,
        "job_name": runner.job_name,
        "is_running": runner.is_running,
    }


@router.post("/open")
async def open_file(path: str = Query(..., description="Absolute path to open")):
    """
    Open a file or directory in the OS default application.
    Safe: only opens paths that belong to the current project.
    """
    project_path = state.current_project_path
    if not project_path:
        raise HTTPException(status_code=400, detail="No project loaded.")

    abs_path = os.path.abspath(path)
    if not abs_path.startswith(os.path.abspath(project_path)):
        raise HTTPException(status_code=403, detail="Path is outside the current project.")

    if not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail="File not found.")

    try:
        if sys.platform == "darwin":
            subprocess.Popen(["open", abs_path])
        elif sys.platform == "win32":
            os.startfile(abs_path)  # type: ignore[attr-defined]
        else:
            subprocess.Popen(["xdg-open", abs_path])
        return {"success": True}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not open file: {exc}")
