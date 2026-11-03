"""Conservative, host-independent filename policy for ZIP metadata."""

import re
import stat
import struct
import unicodedata
from dataclasses import dataclass, field
from zipfile import ZipInfo

from .models import Finding

_ILLEGAL = re.compile(r'[<>:"|?*\x00-\x1f]')
_DRIVE = re.compile(r"^[A-Za-z]:")
_DEVICES = {"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$"} | {
    prefix + suffix for prefix in ("COM", "LPT") for suffix in "123456789¹²³"
}


def _key(component: str) -> str:
    return unicodedata.normalize("NFC", component.rstrip(" .")).casefold()


def _has_unicode_path(extra: bytes) -> bool:
    offset = 0
    while offset + 4 <= len(extra):
        identifier, length = struct.unpack_from("<HH", extra, offset)
        if identifier == 0x7075:
            return True
        offset += 4 + length
    return False


@dataclass
class _Node:
    spelling: str
    member: str
    is_directory: bool
    children: dict[str, "_Node"] = field(default_factory=dict)


def inspect_names(entries: list[ZipInfo]) -> tuple[Finding, ...]:
    """Inspect names in archive order, retaining implicit directory identities."""
    findings: list[Finding] = []
    roots: dict[str, _Node] = {}
    exact_entries: dict[str, str] = {}

    for index, entry in enumerate(entries):
        # zipfile.filename can be sanitized/truncated; orig_filename preserves NULs.
        name = entry.orig_filename

        def emit(
            code: str,
            message: str,
            related: str | None = None,
            *,
            warning: bool = False,
            _name: str = name,
            _index: int = index,
        ) -> None:
            findings.append(
                Finding(code, "warning" if warning else "error", _name, _index, message, related)
            )

        if name in exact_entries:
            emit("duplicate-entry", "Remove the duplicate archive entry.", exact_entries[name])
        else:
            exact_entries[name] = name

        if not name:
            emit("empty-name", "Give this member a nonempty relative path.")
            continue
        if name.startswith(("/", "\\")) or _DRIVE.match(name):
            emit("absolute-path", "Store a relative path without a drive or leading separator.")
        if "\\" in name:
            emit("backslash-path", "Use forward slashes for ZIP path separators.")
        # Backslashes are separators for collision analysis, but always fail policy.
        path = name.replace("\\", "/")
        slash_directory = path.endswith("/")
        mode = entry.external_attr >> 16 if entry.create_system == 3 else 0
        attribute_directory = stat.S_ISDIR(mode) or bool(entry.external_attr & 0x10)
        is_directory = slash_directory or attribute_directory
        if (attribute_directory and not slash_directory) or (
            slash_directory and stat.S_IFMT(mode) not in (0, stat.S_IFDIR)
        ):
            emit(
                "directory-metadata",
                "Extractors may disagree on file/directory type; "
                "align attributes and trailing slash.",
                warning=True,
            )
        raw_parts = path.rstrip("/").split("/")
        if ".." in raw_parts:
            emit("parent-path", "Remove parent-directory segments from the member path.")
        if any(part in ("", ".") for part in raw_parts) or path.endswith("//"):
            emit(
                "noncanonical-path",
                "Some extractors (including Windows Explorer) mishandle dot paths; "
                "remove dot segments and repeated separators.",
                warning=True,
            )

        parts = [part for part in raw_parts if part not in ("", ".")]
        for part in parts:
            if part == "..":
                continue
            if _ILLEGAL.search(part):
                emit(
                    "windows-character",
                    "Rename a component containing a Win32 reserved character.",
                )
                break
        for part in parts:
            if part not in (".", "..") and part.endswith((" ", ".")):
                emit(
                    "trailing-dot-space",
                    "Windows tools may trim trailing dots/spaces; rename the component.",
                )
                break
        for part in parts:
            if part.split(".", 1)[0].rstrip(" ").upper() in _DEVICES:
                emit("windows-device", "Rename a component using a Windows reserved device name.")
                break

        for part in parts:
            if len(part.encode("utf-8")) > 255 or len(part.encode("utf-16-le")) // 2 > 255:
                emit(
                    "long-component",
                    "A component exceeds 255 UTF-8 bytes or UTF-16 units; "
                    "shorten it for ext4 and common Windows volumes.",
                    warning=True,
                )
                break

        if _has_unicode_path(entry.extra):
            emit(
                "alternate-name-metadata",
                "Unicode path extra metadata can override names in some extractors; "
                "this report checks only the raw central-directory name.",
                warning=True,
            )

        if entry.create_system == 3 and stat.S_ISLNK(mode):
            emit(
                "symlink-entry",
                "Symlink handling varies by extractor; the link target was not inspected.",
                warning=True,
            )
        elif entry.create_system == 3 and stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR):
            emit("special-entry", "Special file metadata is not portable.", warning=True)

        # Unsafe parent paths have no meaningful destination identity here.
        if ".." in parts:
            continue
        # A trie avoids copying/hashing every complete prefix for deeply nested paths.
        children = roots
        for depth, part in enumerate(parts):
            key = _key(part)
            final = depth == len(parts) - 1
            directory = not final or is_directory
            previous = children.get(key)
            if previous is not None:
                if previous.is_directory != directory:
                    emit(
                        "file-directory-conflict",
                        "A file blocks a directory required by another entry on common "
                        "filesystems; rename one path.",
                        previous.member,
                    )
                elif previous.spelling != part:
                    emit(
                        "portable-name-collision",
                        "Case/normalization-insensitive filesystems (common on Windows/macOS) "
                        "may merge these paths; rename one. "
                        "Policy: NFC, casefold, trim dots/spaces.",
                        previous.member,
                    )
                elif final and not directory and name != previous.member:
                    emit(
                        "normalized-path-collision",
                        "Distinct member paths normalize to the same file.",
                        previous.member,
                    )
            else:
                previous = _Node(part, name, directory)
                children[key] = previous
            children = previous.children

    return tuple(findings)
