"""
Background job runner with SSE log streaming.

Only one job runs at a time. Routers call `runner.submit(fn, *args)` to queue a
job. The SSE endpoint consumes `runner.sse_generator()` which yields dicts:
  {"type": "log",       "message": "..."}
  {"type": "done",      "message": "Job complete."}
  {"type": "error",     "message": "..."}
  {"type": "heartbeat"}   — sent every ~20 s while idle to keep the connection alive
"""
import queue
import threading
import traceback
from typing import Callable, Iterator, Optional


class JobStatus:
    IDLE = "idle"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"


class JobRunner:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._log_queue: queue.Queue = queue.Queue(maxsize=2000)
        self._status: str = JobStatus.IDLE
        self._job_name: Optional[str] = None
        self._error: Optional[str] = None
        self._thread: Optional[threading.Thread] = None

    # ------------------------------------------------------------------
    # Public properties
    # ------------------------------------------------------------------

    @property
    def status(self) -> str:
        return self._status

    @property
    def is_running(self) -> bool:
        return self._status == JobStatus.RUNNING

    @property
    def job_name(self) -> Optional[str]:
        return self._job_name

    # ------------------------------------------------------------------
    # Called from the job thread
    # ------------------------------------------------------------------

    def log(self, message: str) -> None:
        """Append a log line (safe to call from any thread)."""
        self._enqueue({"type": "log", "message": message})

    def _enqueue(self, item: dict) -> None:
        try:
            self._log_queue.put_nowait(item)
        except queue.Full:
            pass  # Drop the message rather than blocking

    # ------------------------------------------------------------------
    # Job submission
    # ------------------------------------------------------------------

    def submit(self, func: Callable, *args, name: str = "job", **kwargs) -> bool:
        """
        Submit a job function.

        The function signature must be: fn(log_fn, *args, **kwargs)
        where `log_fn` is a callable that accepts a single string.

        Returns True if the job was accepted, False if one is already running.
        """
        with self._lock:
            if self._status == JobStatus.RUNNING:
                return False
            self._status = JobStatus.RUNNING
            self._job_name = name
            self._error = None
            self._drain_queue()

        def _run() -> None:
            try:
                func(self.log, *args, **kwargs)
                self._enqueue({"type": "done", "message": "Job complete."})
                self._status = JobStatus.DONE
            except Exception as exc:  # noqa: BLE001
                detail = traceback.format_exc()
                self._error = str(exc)
                self._enqueue({"type": "error", "message": f"{exc}\n\n{detail}"})
                self._status = JobStatus.ERROR

        self._thread = threading.Thread(target=_run, daemon=True, name=f"job-{name}")
        self._thread.start()
        return True

    # ------------------------------------------------------------------
    # SSE generator (consumed by stream router)
    # ------------------------------------------------------------------

    def sse_generator(self) -> Iterator[dict]:
        """
        Blocking generator that yields dicts from the log queue.
        Yields a heartbeat when the queue is empty for 20 seconds.
        Stops after emitting a "done" or "error" item.
        """
        while True:
            try:
                item = self._log_queue.get(timeout=20)
                yield item
                if item.get("type") in ("done", "error"):
                    return
            except queue.Empty:
                yield {"type": "heartbeat"}
                # Stop if no job is running and queue is empty
                if self._status not in (JobStatus.RUNNING,):
                    return

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _drain_queue(self) -> None:
        """Discard all pending log items (call while holding _lock)."""
        while not self._log_queue.empty():
            try:
                self._log_queue.get_nowait()
            except queue.Empty:
                break
