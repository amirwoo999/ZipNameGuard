"""Command-line configuration, rendering, and CI exit statuses."""

import argparse
import json
import sys
import tomllib
from dataclasses import asdict
from pathlib import Path
from typing import Any

from . import __version__
from .models import Report
from .scan import DEFAULT_MAX_ARCHIVE_BYTES, DEFAULT_MAX_ENTRIES, ScanError, scan_archive


def _positive(value: str) -> int:
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a positive integer") from exc
    if number <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def _configuration(path: str | None) -> dict[str, Any]:
    if path is None:
        return {}
    with Path(path).open("rb") as stream:
        data = tomllib.load(stream)
    if set(data) != {"zipnameguard"} or not isinstance(data["zipnameguard"], dict):
        raise ValueError("Config must contain only a [zipnameguard] table.")
    settings: dict[str, Any] = data["zipnameguard"]
    allowed = {"strict", "max_archive_bytes", "max_entries"}
    unknown = set(settings) - allowed
    if unknown:
        raise ValueError(f"Unknown config keys: {', '.join(sorted(unknown))}")
    for key, value in settings.items():
        if key == "strict":
            if type(value) is not bool:
                raise ValueError("strict must be a boolean")
        elif type(value) is not int or value <= 0:
            raise ValueError(f"{key} must be a positive integer")
    return settings


def _print_report(report: Report) -> None:
    # ASCII JSON escaping is deliberate: no untrusted ANSI escapes or newlines.
    print(
        f"{json.dumps(report.archive)}: {report.entries} entries, "
        f"{len(report.findings)} filename-policy findings"
    )
    for finding in report.findings:
        related = (
            f"; related {json.dumps(finding.related_member)}" if finding.related_member else ""
        )
        print(
            f"  {finding.severity.upper()} {finding.code} entry {finding.entry_index} "
            f"{json.dumps(finding.member)}{related}\n    {finding.message}"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Cross-platform release linter for ZIP filenames. No extraction.",
        epilog="Exit: 0 no policy errors; 1 errors (or strict warnings); 2 input/config failure. "
        "A clean report does not mean extraction is safe. Full destination path limits "
        "and payloads are not checked.",
    )
    parser.add_argument("archives", nargs="+", help="ZIP files to check (quote paths with spaces)")
    parser.add_argument("--version", action="version", version=f"ZipNameGuard {__version__}")
    parser.add_argument("--json", action="store_true", help="emit a versioned JSON report")
    parser.add_argument(
        "--strict",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="fail on warnings as well as errors",
    )
    parser.add_argument("--config", help="explicit TOML configuration file")
    parser.add_argument(
        "--max-archive-bytes",
        type=_positive,
        default=None,
        help=f"input size cap (default {DEFAULT_MAX_ARCHIVE_BYTES})",
    )
    parser.add_argument(
        "--max-entries",
        type=_positive,
        default=None,
        help=f"entry cap after metadata parsing (default {DEFAULT_MAX_ENTRIES})",
    )
    args = parser.parse_args(argv)
    try:
        settings = _configuration(args.config)
    except (OSError, ValueError) as exc:
        error = {"archive": None, "message": str(exc)}
        if args.json:
            print(json.dumps({"schema_version": 1, "reports": [], "errors": [error]}))
        else:
            print(f"Configuration error: {json.dumps(str(exc))}", file=sys.stderr)
        return 2
    strict = args.strict if args.strict is not None else settings.get("strict", False)
    size = args.max_archive_bytes or settings.get("max_archive_bytes", DEFAULT_MAX_ARCHIVE_BYTES)
    count = args.max_entries or settings.get("max_entries", DEFAULT_MAX_ENTRIES)
    reports: list[Report] = []
    errors: list[dict[str, str]] = []
    status = 0
    for path in args.archives:
        try:
            report = scan_archive(path, max_archive_bytes=size, max_entries=count)
        except ScanError as exc:
            errors.append({"archive": path, "message": str(exc)})
            if not args.json:
                print(f"{json.dumps(path)}: {json.dumps(str(exc))}", file=sys.stderr)
            status = 2
            continue
        reports.append(report)
        if report.has_errors or (strict and report.findings):
            status = max(status, 1)
        if not args.json:
            _print_report(report)
    if args.json:
        print(
            json.dumps(
                {
                    "schema_version": 1,
                    "reports": [asdict(report) for report in reports],
                    "errors": errors,
                },
                indent=2,
            )
        )
    return status
