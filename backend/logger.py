"""
Always-on structured logger for NovelWriter UI backend.

  nwlog(tag, message, **kwargs)   — always emits at INFO to stdout
  dlog(tag, **kwargs)             — only when DEBUG_MODE is True

Both appear in uvicorn stdout → captured in Pinokio logs/api/start.js/latest.
"""
import logging
import sys

# ---------------------------------------------------------------------------
# Dedicated stdout handler so output is visible regardless of root-logger level
# ---------------------------------------------------------------------------

_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(logging.Formatter(
    "%(asctime)s  NW  %(message)s",
    datefmt="%H:%M:%S",
))

_log = logging.getLogger("novelwriter")
_log.setLevel(logging.DEBUG)
_log.propagate = False
if not _log.handlers:
    _log.addHandler(_handler)


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def nwlog(tag: str, msg: str = "", **kwargs) -> None:
    """Always-on INFO log.  Shows up in every run, no toggle needed."""
    parts = [f"[{tag}]"]
    if msg:
        parts.append(msg)
    if kwargs:
        parts += [f"{k}={v!r}" for k, v in kwargs.items()]
    _log.info("  ".join(parts))


def dlog(tag: str, **kwargs) -> None:
    """Debug log — only emitted when DEBUG_MODE is True."""
    if not _debug_enabled():
        return
    parts = [f"[{tag}]"] + [f"{k}={v!r}" for k, v in kwargs.items()]
    _log.debug("  ".join(parts))


def _debug_enabled() -> bool:
    try:
        from config import Config  # noqa: PLC0415
        return bool(getattr(Config, "DEBUG_MODE", False))
    except ImportError:
        return False
