"""
Simple debug logger for NovelWriter UI backend.

Call `dlog(tag, **kwargs)` anywhere. Messages appear in uvicorn's stdout
(visible in the Pinokio dev console) only when DEBUG_MODE is True.
"""
import logging

_log = logging.getLogger("novelwriter.debug")


def _debug_enabled() -> bool:
    try:
        from config import Config  # noqa: PLC0415
        return bool(getattr(Config, "DEBUG_MODE", False))
    except ImportError:
        return False


def dlog(tag: str, **kwargs) -> None:
    """Emit a debug log line if DEBUG_MODE is enabled."""
    if not _debug_enabled():
        return
    parts = [f"[{tag}]"] + [f"{k}={v!r}" for k, v in kwargs.items()]
    _log.debug("  ".join(parts))
