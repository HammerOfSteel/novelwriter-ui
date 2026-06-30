"""
/api/stream        — SSE log stream from the running job
/api/job/status    — current job status (polling fallback)
/api/job/reset     — force-clear a stuck job state
/api/open          — open a file in the OS default application
"""
import asyncio
import functools
import json
import os
import queue as _queue_module
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

    Uses run_in_executor so the blocking queue.get never freezes the event loop.
    """
    runner = state.get_job_runner()
    dlog("sse", event="connect", job=runner.job_name, is_running=runner.is_running)
    loop = asyncio.get_running_loop()

    async def _generate():
        while True:
            try:
                # Run the blocking queue.get in a thread so the event loop stays free
                item = await loop.run_in_executor(
                    None,
                    functools.partial(runner._log_queue.get, timeout=20),
                )
            except _queue_module.Empty:
                item = {"type": "heartbeat"}

            dlog("sse", event="emit", type=item.get("type"))
            yield f"data: {json.dumps(item)}\n\n"

            if item.get("type") in ("done", "error"):
                dlog("sse", event="disconnect", reason=item.get("type"))
                return
            if item.get("type") == "heartbeat" and not runner.is_running:
                # Nothing running and queue empty — keep stream alive but don't loop forever
                # The frontend will reconnect if needed
                dlog("sse", event="disconnect", reason="idle")
                return

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


@router.post("/job/reset")
async def reset_job():
    """
    Force-clear a stuck job state.
    Safe to call at any time — if a real job is running it will still complete,
    but the frontend will show as idle and buttons become clickable again.
    """
    runner = state.get_job_runner()
    was = runner.status
    runner._status = "idle"
    runner._job_name = None
    runner._drain_queue()
    dlog("job_runner.reset", was=was)
    return {"ok": True, "was": was}


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
