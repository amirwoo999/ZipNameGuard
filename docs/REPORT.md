# Final project report

Historical initial-build report. The later [pre-release audit](../PRE_RELEASE_AUDIT.md)
supersedes its readiness assessment, measurements, test count and competition review.

## 1. Problem

Release ZIPs can have readable payloads and valid CRCs while their member names
collide or cannot be represented normally on another platform. Source checks
also miss filenames generated during packaging. Release maintainers need a
repeatable final-artifact filename policy check.

## 2. Evidence

[Go issue 33778](https://github.com/golang/go/issues/33778) records a real published
module whose two differently cased Markdown filenames caused an extraction
failure. [libarchive issue 2489](https://github.com/libarchive/libarchive/issues/2489)
documents File Explorer's handling of dot path components, with an explanation
from a maintainer of that integration. [r-lib/zip issue 70](https://github.com/r-lib/zip/issues/70)
discusses filename restrictions and cross-platform implications.

These establish real failure modes. They do not prove unmet mass demand or
forecast stars, users or contributions. The tool's positioning remains a hypothesis
until release maintainers try it. [RESEARCH.md](RESEARCH.md) compares ten ideas,
scores seven dimensions, reviews alternatives and explains selection.

## 3. Solution

Built **ZipNameGuard 0.1.0**, an installable dependency-free Python CLI and API
that scans ZIP member names without extraction or decompression. Reports include
both conflicting members, stable finding codes, archive entry indexes, remedies,
JSON output, explicit TOML config, strict warning mode and CI exit statuses.

This is an incremental release-tooling contribution. Existing pre-commit hooks,
Go's module ZIP checks, Pure and extraction tools already solve related problems.
Install this when a small standalone check of the final ZIP fits your pipeline;
use specialist alternatives for deeper security analysis or source-tree hooks.

## 4. Technical architecture

Python 3.11+ and the standard library. zipfile handles format parsing; a
component trie compares paths under a documented conservative normalization
policy and retains implicit directories. Frozen dataclasses carry findings and
reports. A read-only scanning boundary translates archive failures into ScanError.
The argparse CLI owns TOML configuration, output and status aggregation. No
services, network access, telemetry, plugins or runtime dependencies.

## 5. Repository structure

- `src/zipnameguard/rules.py`: pure filename policy and trie.
- `src/zipnameguard/scan.py`: resource caps, metadata read and error boundary.
- `src/zipnameguard/models.py`: immutable public result data.
- `src/zipnameguard/cli.py`: configuration, terminal-safe text and JSON, statuses.
- `tests/`: unit, generated ZIP regression and subprocess CLI tests.
- `examples/`: deterministic demo producer and TOML configuration.
- `benchmarks/`: repeatable benchmark and actual local JSON measurements.
- `.github/`: six-platform/version test combinations, quality/build job, templates.
- `pyproject.toml`, `MANIFEST.in`: install/build metadata and source distribution.
- `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, `LICENSE`, `CHANGELOG.md`: public
  project documentation and MIT licensing.
- `docs/`: discovery, architecture, development log, critical review and this report.

## 6. Testing

33 automated tests passed on Windows 11 with Python 3.12.10. Tests cover clean and
empty ZIPs, duplicate names, implicit/explicit directories, file/directory
conflicts in both orders, Windows characters/devices including superscript digits,
NFC/case aliases, backslashes, absolute/drive/parent paths, NUL name truncation,
control-character escaping, symlink metadata, deep nesting, limits, malformed and
missing inputs, strict mode, config precedence/validation, multiple-archive status
aggregation, deterministic JSON and CLI help/version.

A regression reproduces the original class of problem: CRC check passes while
portability policy fails. A mock forbids opening ZIP member streams; archive bytes
and directory contents are verified unchanged after a scan. This asserts no
member-stream inspection or extraction, not a guarantee about every byte buffered
internally by Python during metadata reads.

Ruff lint and format checks and strict mypy passed. Distribution build and clean
wheel installation are included in the verification log. Cross-platform CI is
configured, but has not run on GitHub; macOS/Linux support remains unverified here.
Run the entire suite with `python -m unittest discover -s tests -v`.

## 7. Benchmark

Synthetic warm-cache fixture: 2,000 entries; 16,384,000 payload bytes; 278,022-byte
ZIP. Seven measured repetitions with Python 3.12.10 on Windows 11. Median filename
scan: **9.639 ms**. Median Python CRC check: **55.981 ms**. A separate nonportable
fixture passes CRC but yields `portable-name-collision` and `windows-device`.

This comparison demonstrates complementary detection, not equivalent algorithms
or a production speed claim. CRC testing decompresses/checks payloads; name
inspection applies metadata policy. Fixture is repetitive synthetic data, not a
representative dataset. CPU, peak memory and human time saved were not measured.
See `benchmarks/results.json`; rerun with
`python benchmarks/benchmark.py --output benchmarks/results.json`.

Current manual workflow has no single universal baseline command. The new
workflow is one scan command after installation; no quantified manual-time saving
is claimed. Next validation: ask maintainers to use it on actual release ZIPs and
record actionable findings, false positives and integration friction.

## 8. Limitations

ZIP only. Conservative NFC/casefold/trailing-character policy can overreport
compared with specific filesystems. Alias-directory merging is deliberately
flagged. No CRC or local-header validation, extra-field filename interpretation,
link-target inspection, compression compatibility guarantee, destination path
length checks, exact NTFS/APFS emulation, 8.3 alias detection or malware/zip-bomb
protection. Entry count is capped after zipfile parses the directory, so this is
not a hard RAM limit. Use OS isolation for hostile inputs. No real-user trials,
public package, remote CI results, usage statistics or trademark clearance.

## 9. Future development

First: real maintainer trials, false-positive review and regression fixtures from
redistributable archives. Then: platform profiles, documented per-rule suppression,
SARIF, TAR and optional destination-aware path limits. Keep extraction and
automatic renaming outside the core. Contributor work should be tied to a
reproducible archive problem rather than speculative features.

## 10. Open-source launch plan

1. Review your author identity (currently Amir), MIT notice, working name and
   public-facing text. Recheck GitHub/PyPI name availability before publishing.
2. Create a GitHub repository named `zipnameguard`, add the prepared files, push,
   and inspect all CI matrix results. Enable private vulnerability reporting and
   dependency-update notifications. No repository or announcement was published
   by this session.
3. Test the demo and installation from the distribution on Windows, Linux and
   macOS; resolve CI failures before tagging. Build with `python -m build`.
4. Tag `v0.1.0`, attach wheel and sdist with checksums, and publish a release
   explaining the central-directory-only scope. Optionally publish to PyPI using
   trusted publishing after namespace/account setup; avoid token-based automation.
5. Invite a few cross-platform release maintainers to run it on real artifacts.
   Collect false positives and failures before advertising broad compatibility.
6. Share a short demo in a relevant community following its posting rules, link
   the benchmark caveat and alternatives, and ask for real-world fixtures.

Suggested topics: zip, cli, python, cross-platform, windows, release-engineering,
developer-tools, continuous-integration. Ten identity candidates and naming
research are in RESEARCH.md. No guarantee of attention or adoption is appropriate.

## 11. Suggested GitHub description

Read-only ZIP filename portability checks for release pipelines, with actionable
diagnostics, JSON output, and no runtime dependencies.

## 12. Suggested release post

I built ZipNameGuard after investigating ZIPs that pass CRC checks but contain
filenames that break on another platform: case collisions, Windows device names,
and conflicting directory paths.

It checks the final ZIP without extracting it, reports both sides of collisions,
and supports JSON output and CI exit codes. Python 3.11+, no runtime dependencies.
It checks filename policy, not payload integrity or extraction safety.

I'm looking for feedback from maintainers who ship ZIP releases across platforms,
especially real examples where the policy misses a problem or flags too much.

Attach the actual repository URL when published; no placeholder link is presented
as an existing release.
