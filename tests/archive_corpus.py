"""Deterministic ZIP corpus using explicit records, independent of host path rewriting.

Record layouts follow PKWARE APPNOTE sections 4.3.7, 4.3.12, 4.3.16.
This is a tiny fixture writer, not an extractor or production ZIP implementation.
"""

import argparse
import hashlib
import json
import stat
import struct
import zlib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Member:
    name: str | bytes
    data: bytes = b"fixture\n"
    mode: int = stat.S_IFREG | 0o644
    extra: bytes = b""
    flags: int = 0x800
    method: int = 0
    dos_attributes: int = 0


def zip_bytes(members: tuple[Member, ...]) -> bytes:
    """Write stored, fixed-date ZIP records, including otherwise unwriteable names."""
    local = bytearray()
    central = bytearray()
    for member in members:
        name = member.name.encode("utf-8") if isinstance(member.name, str) else member.name
        checksum = zlib.crc32(member.data)
        offset = len(local)
        local.extend(
            struct.pack(
                "<IHHHHHIIIHH",
                0x04034B50,
                20,
                member.flags,
                member.method,
                0,
                33,
                checksum,
                len(member.data),
                len(member.data),
                len(name),
                len(member.extra),
            )
        )
        local.extend(name + member.extra + member.data)
        central.extend(
            struct.pack(
                "<IHHHHHHIIIHHHHHII",
                0x02014B50,
                (3 << 8) | 20,
                20,
                member.flags,
                member.method,
                0,
                33,
                checksum,
                len(member.data),
                len(member.data),
                len(name),
                len(member.extra),
                0,
                0,
                0,
                (member.mode << 16) | member.dos_attributes,
                offset,
            )
        )
        central.extend(name + member.extra)
    end = struct.pack(
        "<IHHHHIIH", 0x06054B50, 0, 0, len(members), len(members), len(central), len(local), 0
    )
    return bytes(local + central + end)


def unicode_extra(raw: bytes, alternate: str) -> bytes:
    data = struct.pack("<BI", 1, zlib.crc32(raw)) + alternate.encode("utf-8")
    return struct.pack("<HH", 0x7075, len(data)) + data


@dataclass(frozen=True)
class Case:
    members: tuple[Member, ...]
    codes: tuple[str, ...]
    note: str = ""


def corpus() -> dict[str, Case]:
    def named(*names: str) -> tuple[Member, ...]:
        return tuple(Member(name) for name in names)

    devices = ("CON", "PRN", "AUX", "NUL", "COM1", "LPT1", "COM¹", "LPT³", "CONIN$", "CONOUT$")
    forbidden = ("<", ">", ":", '"', "|", "?", "*", "\x01", "\x1f")
    return {
        "valid-basic": Case(
            (
                Member("README.txt"),
                Member("dir/file.txt"),
                Member("dir/", b"", stat.S_IFDIR | 0o755),
            ),
            (),
        ),
        "valid-unicode": Case(named("日本語.txt", "café.txt", "😀.txt", "İ.txt", "ı.txt"), ()),
        "valid-boundaries": Case(named("a" * 255, "é" * 127, "COM0", "COM10", ".hidden"), ()),
        "legacy-cp437": Case((Member(b"caf\x82.txt", flags=0),), ()),
        "case": Case(named("README.txt", "readme.txt"), ("portable-name-collision",)),
        "trailing-dot": Case(
            named("foo", "foo."), ("trailing-dot-space", "portable-name-collision")
        ),
        "trailing-space": Case(
            named("foo", "foo "), ("trailing-dot-space", "portable-name-collision")
        ),
        "devices": Case(named(*devices), ("windows-device",) * len(devices)),
        "device-extensions": Case(
            named(*(name + ".tar.gz" for name in devices)), ("windows-device",) * len(devices)
        ),
        "forbidden": Case(
            named(*(f"part{char}name" for char in forbidden)),
            ("windows-character",) * len(forbidden),
        ),
        "nul": Case(named("before\x00after"), ("windows-character",)),
        "duplicate": Case(named("same", "same"), ("duplicate-entry",)),
        "duplicate-directories": Case(
            (Member("d/", b"", stat.S_IFDIR | 0o755),) * 2, ("duplicate-entry",)
        ),
        "file-directory": Case(named("thing", "thing/child"), ("file-directory-conflict",)),
        "directory-file": Case(named("thing/child", "thing"), ("file-directory-conflict",)),
        "nested-case": Case(named("Assets/a.txt", "assets/b.txt"), ("portable-name-collision",)),
        "leading-dot": Case(named("./README.txt"), ("noncanonical-path",)),
        "mixed-separators": Case(
            named("a/b", "a\\b"), ("backslash-path", "normalized-path-collision")
        ),
        "repeated-separators": Case(
            named("a/b", "a//b"), ("noncanonical-path", "normalized-path-collision")
        ),
        "long-ascii-component": Case(named("x" * 256), ("long-component",)),
        "long-utf8-component": Case(named("日" * 86), ("long-component",)),
        "long-full-path": Case(
            named("segment/" * 600 + "file.txt"),
            (),
            "Known gap: complete destination path limits are not checked.",
        ),
        "unicode-nfc-nfd": Case(named("café.txt", "cafe\u0301.txt"), ("portable-name-collision",)),
        "unicode-hangul": Case(named("가.txt", "가.txt"), ("portable-name-collision",)),
        "unicode-casefold-policy": Case(
            named("straße", "strasse"),
            ("portable-name-collision",),
            "Conservative full-casefold policy; not exact NTFS behavior.",
        ),
        "empty-name": Case(named(""), ("empty-name",)),
        "dot-directory": Case((Member("./", b"", stat.S_IFDIR | 0o755),), ("noncanonical-path",)),
        "root-directory": Case(
            (Member("/", b"", stat.S_IFDIR | 0o755),), ("absolute-path", "noncanonical-path")
        ),
        "parent": Case(named("a/../b"), ("parent-path",)),
        "drive-relative": Case(named("C:file"), ("absolute-path", "windows-character")),
        "symlink": Case((Member("link", b"../outside", stat.S_IFLNK | 0o777),), ("symlink-entry",)),
        "special": Case((Member("fifo", b"", stat.S_IFIFO | 0o600),), ("special-entry",)),
        "directory-attribute": Case(
            (Member("d", b"", stat.S_IFDIR | 0o755), Member("d/child")), ("directory-metadata",)
        ),
        "alternate-name": Case(
            (Member("safe", extra=unicode_extra(b"safe", "NUL.txt")),), ("alternate-name-metadata",)
        ),
        "many-entries": Case(
            tuple(Member(f"data/{index:05}.txt", b"") for index in range(10000)), ()
        ),
        "empty-archive": Case((), ()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for name, case in corpus().items():
        content = zip_bytes(case.members)
        (args.output / f"{name}.zip").write_bytes(content)
        manifest[name] = {
            "sha256": hashlib.sha256(content).hexdigest(),
            "entries": len(case.members),
            "expected_codes": case.codes,
            "note": case.note,
        }
    (args.output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    print(f"Created {len(manifest)} deterministic archives in {args.output}")


if __name__ == "__main__":
    main()
