"""ZIP member filename policy checks; no extraction or payload inspection."""

from .models import Finding, Report
from .scan import ScanError, scan_archive

__all__ = ["Finding", "Report", "ScanError", "scan_archive"]
__version__ = "0.1.0"
