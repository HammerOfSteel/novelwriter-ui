"""
Compatibility shim — re-exports dlog and nwlog from backend.logger.
Existing imports of `from backend.debug_logger import dlog` continue to work.
"""
from backend.logger import dlog, nwlog  # noqa: F401
