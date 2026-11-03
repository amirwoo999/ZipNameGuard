# ZipNameGuard

Cross-platform release linter for ZIP filenames.

**Catch archive filename surprises before your users do.**

A ZIP can pass a CRC check and still contain `README` and `readme`, a Windows
device name such as `NUL.txt`, or paths that different extractors interpret
differently. ZipNameGuard checks the **final artifact**, including generated
files, without extracting or decompressing its contents.

Version 0.1.0 is a local release candidate, **not yet recommended for public release**.
See [the pre-release audit](PRE_RELEASE_AUDIT.md) for remaining gates. No hosted
package or public repository has been published. Python 3.11+; no runtime dependencies.

## Quick start

From a downloaded or cloned checkout:

```console
python -m venv .venv
```

Activate it on Windows PowerShell with `.venv\Scripts\Activate.ps1`, or on
Linux/macOS with `source .venv/bin/activate`. Then:

```console
python -m pip install .
python examples/create_demo.py
zipnameguard demo.zip
```

The demo intentionally exits **1** and reports:

```text
"demo.zip": 4 entries, 3 filename-policy findings
  ERROR portable-name-collision entry 1 "readme.md"; related "README.md"
    Case/normalization-insensitive filesystems (common on Windows/macOS) may merge these paths; rename one. Policy: NFC, casefold, trim dots/spaces.
  ERROR windows-device entry 2 "assets/CON.txt"
    Rename a component using a Windows reserved device name.
  ERROR windows-character entry 3 "logs/12:30.txt"
    Rename a component containing a Win32 reserved character.
```

## Usage

```console
zipnameguard release.zip
zipnameguard --strict --json release.zip assets.zip
zipnameguard --config examples/zipnameguard.toml release.zip
zipnameguard --max-archive-bytes 1073741824 --max-entries 200000 trusted-large.zip
python -m zipnameguard --help
```

Pass archive paths explicitly; shell wildcard expansion differs across platforms.
Use `--` before paths beginning with `-`. Names are escaped in terminal output.

Exit codes: **0** no errors; **1** filename-policy errors (or warnings with
`--strict`); **2** input/configuration failures. Multiple inputs are all processed;
status 2 takes priority. JSON output has `schema_version`, `reports`, and `errors`.
Reports contain `archive`, `entries`, and `findings`. Findings contain `code`,
`severity`, `member`, zero-based `entry_index`, `message`, and nullable
`related_member`. Invocation/argument errors use argparse's stderr output, even
with `--json`; successfully parsed invocations use the JSON envelope.

## What it checks

- Errors: duplicate entries; file/directory conflicts; case, NFC Unicode, and
  trailing-dot/space aliases, including implicit directory prefixes.
- Errors: absolute/drive paths, parent segments, backslashes, Win32 reserved
  characters and device names, trailing dots/spaces, and empty names.
- Warnings: dot segments or repeated separators; Unix symlink/special-file metadata;
  inconsistent directory attributes; components exceeding 255 UTF-8 bytes or
  UTF-16 code units; Unicode path extra fields whose alternate names are not analyzed.

The policy is intentionally conservative. Casefold and NFC are **not exact models
of every filesystem**. Differently spelled directories are flagged even when
their children could merge without overwriting. Fix the archive producer rather
than silently renaming files during extraction. Symlink targets are not read.
Full Unicode casefold is broader than the comparison used by some filesystems:
for example, `straße` and `strasse` were distinct in the local Windows probe but
fail this conservative policy. Unicode behavior also depends on Python's Unicode
database version. Pin a Python version for reproducible policy decisions.

## Before and after

Before: list archive members, manually inspect names, write platform checks, or
discover failures when extracting on another OS. A CRC check alone does not check
filename portability. After: run `zipnameguard --strict release.zip` as a CI gate.
This does not replace CRC testing.

For source repositories, use
[pre-commit's filename hooks](https://github.com/pre-commit/pre-commit-hooks).
For deeper ZIP format/security analysis, consider
[Pure](https://github.com/ronomon/pure). For a Python library that already performs
read-only archive inspection with many of the same checks, consider
[pathward](https://pypi.org/project/pathward/). It also has no runtime dependencies
and handles TAR. Go already validates its own module ZIPs. ZipNameGuard offers a
focused CLI that accumulates filename findings, related paths and JSON results;
the underlying checks substantially overlap existing tools. See
[the current competitive audit](PRE_RELEASE_AUDIT.md), which supersedes the
initial [opportunity research](docs/RESEARCH.md).

## Configuration

Optional explicit TOML (`--config path.toml`):

```toml
[zipnameguard]
strict = true
max_archive_bytes = 268435456
max_entries = 100000
```

Flags override config, then defaults. `--no-strict` overrides strict config.
Unknown keys and wrong types fail. No auto-discovery or environment settings.
The input size cap is 256 MiB; entry cap is 100,000. The entry cap is applied
**after** Python loads the central directory; it is not a hard memory bound.

## Python API and architecture

```python
from zipnameguard import ScanError, scan_archive

try:
    report = scan_archive("release.zip")
except ScanError as error:
    print(error)
else:
    for finding in report.findings:
        print(finding.code, repr(finding.member), repr(finding.related_member))
```

`scan.py` opens an archive read-only; `rules.py` uses a trie for paths and implicit
directories; frozen models represent findings; `cli.py` owns configuration and
rendering. Rule processing scales with path characters and findings; memory scales
with metadata and path prefixes. Python's ZIP parser also sorts header offsets,
so the complete scan is not strictly linear in entry count. See [design](docs/DESIGN.md).

## Benchmarks

Run `python benchmarks/benchmark.py --output benchmarks/results.json` after
installation. It compares metadata scanning with Python's CRC check and reproduces
an archive whose CRCs pass despite filename errors. These perform different work:
CRC validates payload integrity, while this tool checks filename policy. Synthetic
warm-cache timing is recorded in [results](benchmarks/results.json); no claim of
production speedup or measured developer time saved is made.

Audit rerun: Windows 11, Python 3.12.10, 2,000 entries, 16,384,000 uncompressed
bytes, seven repetitions: filename scan median **11.448 ms**, CRC check median
**57.610 ms**. See [audit measurements](benchmarks/audit-results.json).
A separate valid-CRC fixture produces a case-collision error and a Windows-device
error. These different tasks do not establish a useful performance advantage.

## Limits and security

ZIP only; ZIP64 parsing is delegated to Python (tested with small ZIP64 metadata,
not a multi-gigabyte archive). Does not validate payload CRCs,
local-header consistency, compression support in a target extractor, malformed
extra fields, Unicode path extra-field overrides, encryption, link targets,
permissions, destination path lengths, 8.3 aliases, malware, or zip bombs.
The central directory is the sole naming authority for this report. A clean
report does **not** certify safe extraction or compatibility with every extractor.
**This is not a secure extraction engine. It does not provide protection from
Zip Slip, zip bombs, malicious payloads, unsafe symlinks, malware, or arbitrary
archive extraction vulnerabilities.** Spotting a path spelling is not protection
for a later extraction operation. Warnings are not fatal unless `--strict` is used.
In particular, a long complete path can produce no findings: the destination
prefix, filesystem and extraction API are unknown.
No network calls, telemetry, member execution, extraction, or archive modification.
Use an OS sandbox/resource limits for hostile input. See [SECURITY.md](SECURITY.md).

## Development and contributing

```console
python -m pip install -e ".[dev]"
python -m unittest discover -s tests -v
ruff check .
ruff format --check .
mypy
python -m build
```

Tests generate byte-deterministic archives without requiring invalid names on disk.
CI is **configured**, not yet verified, for Linux, macOS and Windows on Python
3.11–3.15. Only Windows/Python 3.12.10 has run locally. See [CONTRIBUTING.md](CONTRIBUTING.md),
[development log](docs/DEVELOPMENT_LOG.md), and [final report](docs/REPORT.md).

## Roadmap

Maintainer trials and real archive regressions first. Then configurable platform
profiles and rule suppression with reasons, SARIF output, TAR support, and optional
destination-aware path limits. Directory scanning is evaluated in
[the future-feature note](docs/DIRECTORY_SCANNING.md), not implemented in v0.1.
Auto-renaming and extraction are outside scope.

## License

[MIT](LICENSE), copyright Amir. Chosen to permit easy adoption in release tooling.
