"""Observe a temporary filesystem using harmless names; never extract a ZIP."""

import argparse
import json
import platform
import tempfile
import unicodedata
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent / "verification-sandbox"
    root.mkdir(exist_ok=True)
    results = {}
    with tempfile.TemporaryDirectory(prefix="fs-probe-", dir=root) as temporary:
        base = Path(temporary).resolve()
        base.relative_to(root.resolve())
        for index, (name, pair) in enumerate(
            {
                "ascii_case": ("README.txt", "readme.txt"),
                "trailing_dot": ("foo", "foo."),
                "trailing_space": ("foo", "foo "),
                "canonical_unicode": ("café", "cafe\u0301"),
                "full_casefold": ("straße", "strasse"),
            }.items()
        ):
            directory = base / str(index)
            directory.mkdir()
            first, second = (directory / member for member in pair)
            first.write_bytes(b"first")
            try:
                second.write_bytes(b"second")
                results[name] = {
                    "same_file": first.samefile(second),
                    "first_content_after": first.read_text(encoding="ascii"),
                    "names": sorted(entry.name for entry in directory.iterdir()),
                }
            except OSError as error:
                results[name] = {"error": str(error), "errno": error.errno}
        long_name = base / ("x" * 256)
        try:
            long_name.write_bytes(b"fixture")
            results["ascii_component_256"] = {"created": True}
        except OSError as error:
            results["ascii_component_256"] = {
                "created": False,
                "errno": error.errno,
                "winerror": getattr(error, "winerror", None),
            }
    output = {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "unicode_version": unicodedata.unidata_version,
        "scope": "Only this temporary directory/volume and normal Python file APIs.",
        "observations": results,
    }
    args.output.write_text(json.dumps(output, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
