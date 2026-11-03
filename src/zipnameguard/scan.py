"""Read-only filesystem boundary around the pure filename rules."""

import os
import warnings
import zipfile
from pathlib import Path

from .models import Report
from .rules import inspect_names

DEFAULT_MAX_ARCHIVE_BYTES = 256 * 1024 * 1024
DEFAULT_MAX_ENTRIES = 100_000


class ScanError(Exception):
    """An archive could not be completely inspected."""


def scan_archive(
    path: str | Path,
    *,
    max_archive_bytes: int = DEFAULT_MAX_ARCHIVE_BYTES,
    max_entries: int = DEFAULT_MAX_ENTRIES,
) -> Report:
    """Check central-directory names, without opening any member payload.

    The byte cap precedes parsing; the entry cap follows zipfile's metadata load.
    These limits are not a memory sandbox for adversarial archives.
    """
    if type(max_archive_bytes) is not int or max_archive_bytes <= 0:
        raise ValueError("max_archive_bytes must be a positive integer")
    if type(max_entries) is not int or max_entries <= 0:
        raise ValueError("max_entries must be a positive integer")
    try:
        with open(path, "rb") as stream:
            if os.fstat(stream.fileno()).st_size > max_archive_bytes:
                raise ScanError(
                    f"Archive exceeds {max_archive_bytes} bytes; increase --max-archive-bytes "
                    "only for a trusted input."
                )
            with warnings.catch_warnings():
                # A library warning must not leak absolute paths or corrupt JSON stderr.
                # Reject parser ambiguity instead of returning a deceptively clean report.
                warnings.simplefilter("error", UserWarning)
                archive = zipfile.ZipFile(stream)
            with archive:
                entries = archive.infolist()
                if len(entries) > max_entries:
                    raise ScanError(
                        f"Archive has {len(entries)} entries, "
                        f"exceeding --max-entries {max_entries}."
                    )
                return Report(str(path), len(entries), inspect_names(entries))
    except (OSError, ValueError, UserWarning, zipfile.BadZipFile, NotImplementedError) as exc:
        raise ScanError(f"Cannot inspect archive: {exc}") from exc
