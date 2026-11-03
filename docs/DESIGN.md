# MVP and architecture (written before implementation)

## Scope

Must have: ZIP central-directory inspection without extraction; unsafe absolute,
parent and backslash paths; Win32 illegal names and trailing characters;
duplicate and case/Unicode-normalized collisions including implicit directories;
file/directory conflicts; symlink notice; text/JSON output; meaningful exit codes;
multiple archives; tests; installable package; CI.

Should have: per-rule suppression, SARIF, target profiles, real maintainer trials.
Future: TAR, destination-specific path limits, local header consistency, signed
release provenance. No auto-renaming, extraction, malware or zip-bomb guarantees.

## Design

Python >=3.11; standard library runtime. `zipfile` parses ZIP metadata; `argparse`
provides the CLI; `tomllib` reads explicit TOML config; dataclasses carry reports.
Setuptools builds wheels; unittest tests; Ruff and mypy are development checks.
No web service, framework, shelling out or telemetry.

Modules: models (immutable findings/reports), rules (pure metadata policy), scan
(filesystem boundary), cli (config, rendering and status). Public API:
`scan_archive(path, *, max_archive_bytes, max_entries)` -> Report; errors raise
`ScanError`. JSON schema version 1 uses archive reports and operational errors.
Finding fields: code, severity, member, entry index (zero based), related member,
message. No timestamps in reports. Order follows archive entries and rule order.

Config is optional and explicitly selected with `--config`; flags override file
values, which override defaults. No environment-variable settings: ambient
configuration would reduce reproducibility. Diagnostics go to stdout; operational
errors go to stderr in text mode and into the JSON envelope in JSON mode. No log
files or content logging. Exit 0 clean (or warnings), 1 policy errors (or warnings
with strict mode), 2 input/config/read failures. Highest exit status wins.

Portability policy is conservative: NFC + Python Unicode casefold plus trimming
trailing dots/spaces predicts common aliases, not exact NTFS/APFS behavior.
Directories with alternate spellings are reported even if their contents could
merge without overwriting. Dot segments/repeated separators are warnings because
some extractors normalize these; strict mode makes warnings fail CI.

Index components with a trie, comparing implicit and explicit directories.
Expected rule processing is linear in total path characters plus findings;
the standard-library metadata parser also sorts local-header offsets, adding an
entry-count sorting cost to the complete scan.
Memory is linear in entries/prefixes. Central directories are loaded by zipfile;
archive-size limit is checked on the opened handle before parsing; entry limit
is checked after parsing. Neither is a sandbox. Do not decompress payloads.

Security: treat names as untrusted and JSON-escape them in text output to prevent
terminal control injection. Never execute or extract members, follow member
symlinks, or modify archives. Use `ZipInfo.orig_filename` because `filename` can
truncate NUL names. Metadata is untrusted; no claim of integrity or extraction
safety. Encrypted payloads and unsupported compression can still have names
checked; their contents are not validated. Resource caps reduce accidental misuse
but hostile archives should be handled in an OS sandbox.

Tests: pure rule tests, ZIP fixtures generated in temporary directories, subprocess
CLI tests, corrupt/unreadable inputs, config failures, control characters,
ordering, JSON schema behavior, entry limits and no-payload-read assertions.
CI matrix: Windows, Linux, macOS on Python 3.11 and 3.12; lint/types/build separately.
Only the local Windows environment can be claimed as executed until CI runs.

## Success criteria and benchmark plan

One scan command produces both involved member names for all seeded collision
cases. No payload reads or extraction writes. Clean archive passes. JSON parses
and exit codes make a CI gate. Compare `ZipFile.testzip()` (CRC integrity check)
against scan on an intentionally nonportable archive with valid CRCs; show the
different findings rather than treating them as equivalent algorithms. Also time
both on a synthetic clean archive and report medians, payload bytes, entry count,
environment and limitations. No developer-time or adoption claims without trials.
