# Development log

## October 30, 2026 — discovery and design

Inspected an empty Git workspace with Python 3.12.10, Git and Node available.
Compared ten opportunities before implementation. Selected an artifact filename
preflight because public issue reports reproduce a narrow, practical release
problem and the MVP fits a small, maintainable package. Originality is incremental.
Reviewed alternatives without copying their implementations. Research and design
are recorded before code. Chose a metadata-only policy checker rather than a
custom ZIP parser; deeper archive security belongs to specialist tools.

## Implementation and verification

Implemented pure metadata rules, frozen reports, a read-only scan boundary,
text/JSON CLI, explicit TOML settings and deterministic generated examples. The
initial 31-test suite passed. Ruff found formatting/import issues and an implicit
loop-variable closure capture; fixed them before rerunning quality checks.

Adversarial review replaced full-prefix path keys with an iterative trie, avoiding
repeated copying for deep paths. Added deep-nesting and explicit-directory alias
regressions. All 33 tests pass; Ruff lint/format and strict mypy pass. No runtime
dependencies. Direct dev tools are pinned; no global packages installed.

Measured seven-repeat warm-cache synthetic benchmark: 2,000 entries, 16,384,000
payload bytes, scan 9.639 ms median and CRC test 55.981 ms median. These are
different tasks; documentation makes no equivalent-work speedup claim. Nonportable
valid-CRC fixture produces the expected two filename findings.

Built wheel and source distribution successfully. Installed the wheel with
`--no-deps` into a separate clean virtual environment; confirmed imports resolve
to its site-packages, the console command prints version 0.1.0, pip check passes,
and all 33 tests pass against the installed wheel. Ran the actual README demo:
exactly three documented findings, expected exit code 1. Artifacts remain local
under dist; no public repository, package or announcement was created.

## Pre-release audit — October 30, 2026

Revalidated current public reports, including 2026 Go trailing-normalization and
ouch device/stream reports. Found much closer competition: pathward 0.2.0 already
offers dependency-free read-only portability validation. Installed pathward and
zipguard in a separate audit environment and tested default read-only operations.
Positioning is now release filename linting with accumulated diagnostics; novelty
and security claims were narrowed.

Built 36 deterministic raw-record fixtures and an approved hash manifest. Initial
adversarial failures exposed invalid-path exception leakage, parser warning leakage,
directory-attribute misclassification, alternate-name omission and component-length
gaps. Corrected these, added console device aliases and stronger CLI regressions.
The local suite now has 53 tests. All 235 statements and 94 recorded branches ran
under coverage with subprocess tracing; this is not a correctness certification.

Local filesystem probes confirmed case/dot/space aliases and demonstrated broader
casefold false positives. CI now targets three current OS runner labels and Python
3.11–3.15, but has not run. A clean-checkout/fresh-builder/fresh-wheel verification
harness passed locally, including exact README activation/install/demo commands.
Ruff, formatting and strict mypy pass. Directory scanning was evaluated and deferred.

Final audit recommendation remains NOT RELEASE READY pending actual cross-platform
matrix results. PRE_RELEASE_AUDIT.md is the current readiness record. Nothing was
published or uploaded; all artifacts and audit evidence remain local.
