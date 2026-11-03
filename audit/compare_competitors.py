"""Run read-only competitor operations on the local corpus; no security verdicts."""

import importlib.metadata
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pathward

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests"))
from archive_corpus import corpus, zip_bytes  # noqa: E402


def main() -> None:
    results = {}
    executable = Path(sys.executable).with_name(
        "zipguard.exe" if sys.platform == "win32" else "zipguard"
    )
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        for name, case in corpus().items():
            archive = root / f"{name}.zip"
            archive.write_bytes(zip_bytes(case.members))
            try:
                manifest = pathward.inspect_archive(archive)
                pathward_result = {"accepted": True, "files": manifest.files}
            except Exception as error:
                pathward_result = {
                    "accepted": False,
                    "exception": type(error).__name__,
                    "message": str(error),
                }
            process = subprocess.run(
                [
                    str(executable),
                    str(archive),
                    "--dry-run",
                    "--format",
                    "json",
                    "--out",
                    str(root / "unused-destination"),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
                env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            )
            try:
                start = process.stdout.find("{")
                parsed = json.loads(process.stdout[start:])
                zipguard_result = {
                    "json_preamble_present": bool(process.stdout[:start].strip()),
                    "aborted": parsed.get("aborted"),
                    "abort_reason": parsed.get("abort_reason"),
                    "summary": parsed.get("summary"),
                    "entries": [
                        {key: entry.get(key) for key in ("name", "decision", "reason")}
                        for entry in parsed.get("entries", [])[:12]
                    ],
                    "entries_truncated": len(parsed.get("entries", [])) > 12,
                }
            except ValueError:
                zipguard_result = process.stdout.replace(str(root), "<TEMP>")[:2000]
            results[name] = {
                "pathward": pathward_result,
                "zipguard": {
                    "exit": process.returncode,
                    "output": zipguard_result,
                    "stderr": process.stderr,
                },
            }
        if (root / "unused-destination").exists():
            raise RuntimeError("Unexpected destination write during competitor dry run")
    output = {
        "versions": {name: importlib.metadata.version(name) for name in ("pathward", "zipguard")},
        "note": "Default policies; raw evidence, not a comprehensive security comparison.",
        "cases": results,
    }
    (ROOT / "audit" / "competitor-results.json").write_text(
        json.dumps(output, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    for name, result in results.items():
        print(
            name,
            "pathward accepts:",
            result["pathward"]["accepted"],
            "zipguard exit:",
            result["zipguard"]["exit"],
        )


if __name__ == "__main__":
    main()
