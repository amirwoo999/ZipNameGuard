"""Reproducible synthetic metadata-vs-CRC comparison; no equivalent-work claim."""

import argparse
import json
import platform
import statistics
import sys
import tempfile
import time
from collections.abc import Callable
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from zipnameguard import scan_archive


def median_ms(operation: Callable[[], object], repeats: int) -> float:
    timings = []
    for _ in range(repeats):
        start = time.perf_counter()
        operation()
        timings.append((time.perf_counter() - start) * 1000)
    return round(statistics.median(timings), 3)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        path = root / "clean.zip"
        count, payload_bytes, repeats = 2000, 8192, 7
        with ZipFile(path, "w", compression=ZIP_DEFLATED) as archive:
            for index in range(count):
                archive.writestr(f"data/item-{index:05}.txt", b"x" * payload_bytes)

        def crc() -> str | None:
            with ZipFile(path) as archive:
                return archive.testzip()

        assert crc() is None
        assert not scan_archive(path).findings
        # Warm both paths before measurement; timings include open/metadata parse.
        result = {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "fixture": "synthetic repeated-byte clean ZIP; warm filesystem cache",
            "entries": count,
            "payload_bytes": count * payload_bytes,
            "archive_bytes": path.stat().st_size,
            "repeats": repeats,
            "crc_test_median_ms": median_ms(crc, repeats),
            "filename_scan_median_ms": median_ms(lambda: scan_archive(path), repeats),
        }
        bad = root / "nonportable.zip"
        with ZipFile(bad, "w") as archive:
            for name in ("SHOULDERS.md", "shoulders.md", "NUL.txt"):
                archive.writestr(name, b"valid payload")
        with ZipFile(bad) as archive:
            result["nonportable_crc_passes"] = archive.testzip() is None
        result["nonportable_finding_codes"] = [f.code for f in scan_archive(bad).findings]
        result["caveat"] = (
            "Different tasks: CRC checks payload integrity; filename scan checks metadata policy. "
            "Synthetic timings do not predict production speed or human time saved."
        )
    output = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(output, encoding="utf-8")
    print(output, end="")


if __name__ == "__main__":
    main()
