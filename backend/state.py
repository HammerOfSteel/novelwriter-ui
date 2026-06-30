"""
Module-level singletons shared across all API routers.

Routers import `state` directly and read/write `current_project_path`.
The JobRunner is created lazily on first access to avoid import-order issues.
"""
from typing import Optional

# The absolute path to the currently loaded project directory.
# None means no project is open.
current_project_path: Optional[str] = None

# Lazy singleton for the background job runner.
_job_runner = None


def get_job_runner():
    """Return (and lazily create) the global JobRunner instance."""
    global _job_runner
    if _job_runner is None:
        from backend.job_runner import JobRunner
        _job_runner = JobRunner()
    return _job_runner
