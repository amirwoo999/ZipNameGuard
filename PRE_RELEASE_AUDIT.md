# ZipNameGuard pre-release audit

Audit date: **October 30, 2026** (America/Chicago). Scope: local v0.1.0 candidate,
source, tests, documentation, packaging, competition and public problem evidence.
This supersedes the initial research's positioning and readiness conclusions.
No repository, package, CI run, announcement or archive was published.

## Decision

**NOT RELEASE READY.** The local code and documentation defects identified below
have been fixed and verification rerun. The recommendation remains to hold public
release until the configured Windows/Ubuntu/macOS matrix actually passes. Public
maintainer trials are useful next evidence, not something this audit pretends has
already happened. Existing functionality substantially overlaps pathward; market
novelty must not be the launch story.

The project is a credible small release utility, not an original portability
algorithm or a secure extraction engine. Use the one-sentence positioning:

> Cross-platform release linter for ZIP filenames.

## Evidence and current problem validation

The underlying problems are real. Recency and authority are distinguished here:

- [Go issue 80123](https://github.com/golang/go/issues/80123), opened June 23,
  2026, reports a module member with a trailing space becoming a different Windows
  filename, and identifies trailing-dot aliasing as a related gap. It was open
  when inspected. This is a report under investigation, not a validated security
  advisory or evidence that ZipNameGuard prevents exploitation.
- [ouch issue 1090](https://github.com/ouch-org/ouch/issues/1090), opened
  September 29, 2026, includes Windows 11 reproductions involving device names and
  colon/alternate-stream behavior. This audit did not execute device writes or
  reproduce that tool's extraction behavior; treat it as the reporter's evidence.
- [CPython issue 117779](https://github.com/python/cpython/issues/117779)
  describes inconsistent duplicate-entry handling. It is older (2024), but the
  representation and parsing ambiguity remain relevant to today's ZIP libraries.
- [libarchive issue 2489](https://github.com/libarchive/libarchive/issues/2489)
  contains a July 2026 explanation from the File Explorer ZIP integration owner
  about dot-component behavior. [Go issue 33778](https://github.com/golang/go/issues/33778)
  is historical corroboration of published case-collision failures, not our main
  claim of current demand.
- Current [hatchzip documentation](https://github.com/xevrion/hatchzip/blob/main/docs/how-it-works.md)
  explicitly describes duplicate/case path checks and file/link-versus-directory
  conflicts before extraction. Current implementations already take this class of
  problem seriously. That also reduces this project's novelty.

Primary technical references used in the rule inventory:

- **W**: [Microsoft naming rules](https://learn.microsoft.com/en-us/windows/win32/fileio/naming-a-file).
- **L**: [Microsoft path-length guidance](https://learn.microsoft.com/en-us/windows/win32/fileio/maximum-file-path-limitation).
- **A**: [Apple APFS filename FAQ](https://developer.apple.com/library/archive/documentation/FileManagement/Conceptual/APFS_Guide/FAQ/FAQ.html).
  This is explicitly retired documentation. It establishes historical APFS
  normalization behavior; it is not proof of every current macOS configuration.
- **K**: [Linux kernel ext4 directory documentation](https://kernel.org/doc/html/latest/filesystems/ext4/directory.html).
- **Z**: [PKWARE APPNOTE 6.3.10](https://pkware.cachefly.net/webdocs/casestudies/APPNOTE.TXT),
  especially filename, host-dependent attributes and Unicode path extra fields.
- **P**: [Python reserved-path documentation](https://docs.python.org/3/library/os.path.html#os.path.isreserved),
  including console names; it explicitly describes its rules as approximations.
- **C**: [Python zipfile documentation](https://docs.python.org/3/library/zipfile.html)
  and the actual installed Python 3.12.10 parser source inspected locally.

The local [filesystem observations](audit/filesystem-windows.json) provide stronger
evidence for this machine than general assumptions: `README.txt`/`readme.txt`,
`foo`/`foo.`, and `foo`/`foo ` referred to the same file. Composed/decomposed accents
and `straße`/`strasse` remained distinct. A 256-character ASCII component failed
creation. These are ordinary Python file operations on one temporary volume, not
an extraction-engine comparison or universal Windows behavior claim.

No recent issue report was found for every individual rule. Some rules are
supported by platform specifications and current implementations rather than
fresh community demand. No user/adoption/time-saving statistics are claimed.

## Competition: substantial overlap, narrow independent value

Read-only requests queried actual indexes. [Registry results](audit/registry-results.json)
record URLs and HTTP statuses. Versions **pathward 0.2.0** and **zipguard 0.2.0**
were installed into `.venv/audit-tools` from PyPI and exercised without extraction.
See [comparison script](audit/compare_competitors.py) and
[observed outcomes](audit/competitor-results.json). Default policies were used;
this is a bounded functional comparison, not an audit of competitors' security.

| Alternative | Supported / observed overlap | Limits for this workflow | Honest implication |
| --- | --- | --- | --- |
| [pathward](https://pypi.org/project/pathward/) | General-purpose, read-only ZIP/TAR inspection; rejects our case, trailing-dot/space, device, duplicate, file/directory and NFC fixtures. No runtime dependencies. | Library returns a manifest or raises at the first failure; no installed standalone lint CLI in the examined distribution. Its default policy also imposes extraction-oriented bounds. | Already provides essentially the same core general-purpose portability validation. A small wrapper may be enough for a Python application. ZipNameGuard's difference is accumulated diagnostics, related names, CLI/JSON and a release-only policy. |
| [zipguard](https://pypi.org/project/zipguard/) | CLI, JSON, dry run, policy configuration, duplicate rejection and symlink findings. Also no runtime dependencies. | In the examined dry run, basic case/dot/space/device/file-directory/NFC fixtures were allowed. Dry-run exit 0 also occurred for blocked entries; duplicate archives exited 2. JSON had a terminal preamble. | Close UX overlap, different security/extraction policy. Do not claim CLI, JSON, dry-run or zero dependencies are unique. These observations concern only version 0.2.0 on this host. |
| [Pure](https://github.com/ronomon/pure) | General-purpose ZIP static analyzer and CLI; source lists length, control characters, traversal, backslash, alternate-name and format checks. | Different emphasis: archive format/security analysis; reviewed docs/error definitions, not installed or benchmarked. Complete case/Windows-device collision parity was not established. | More capable for deeper ZIP inspection. Do not describe it as merely a CRC checker or claim its untested checks are absent. |
| [pre-commit hooks](https://github.com/pre-commit/pre-commit-hooks) | Case conflict hook indexes directory prefixes; Windows-name hook uses a filename filter in the hook manifest. | Acts on Git/source filenames, not final ZIP member metadata or duplicate entries. | Prefer these for source prevention. ZipNameGuard can catch packaging-generated members later. |
| [Go module ZIP package](https://pkg.go.dev/golang.org/x/mod/zip) | Validates module paths/case collisions and other module restrictions. | Go module structure and semantics rather than an arbitrary release ZIP. Recent trailing-normalization report exists. | Strong prior art; avoid duplicating it for Go module validation. |
| [hatchzip](https://github.com/xevrion/hatchzip/blob/main/docs/how-it-works.md) | Documents duplicate/case and file/directory checks before extraction. | Extraction engine with its own operation and resource model; only documentation reviewed. | Related validation exists. Standalone linting is a narrower interface, not a new class of capability. |
| Python `zipfile -t`, `ZipFile.testzip()`, archive listing tools | Names can be listed; CRC tests assess readable payload integrity. | CRC success is not filename portability; a custom script is needed for policy. | Useful complementary tools. Comparing their runtime to linting does not demonstrate equivalent-work speedup. |

Specific differences matter more than a checkbox total. pathward accepted our
two differently cased directories containing disjoint children; that is often a
harmless merge, not necessarily its bug. ZipNameGuard deliberately flags it as
release policy. pathward accepted a raw NUL-containing central name after Python
truncated the interpreted filename; ZipNameGuard retains `orig_filename` and
reports it. Do not generalize these fixtures into a security superiority claim.

**Conclusion:** another tool already implements much of the general-purpose
read-only validation. No exact drop-in replacement with the same accumulated
reporting policy was established in this bounded search. That is weaker than
proving no equivalent tool exists. Differentiation is useful but incremental.

## Complete rule inventory

There are **17 finding identifiers** after audit fixes. E = error; W = warning
(fatal only with `--strict`). `R:N` means line N of
[src/zipnameguard/rules.py](src/zipnameguard/rules.py), function `inspect_names`;
the extra-field helper is at R:23. Locations describe this audited source snapshot.
`corpus:name` refers to the exact-code/severity fixture in
[test_adversarial.py](tests/test_adversarial.py) and
[archive_corpus.py](tests/archive_corpus.py). Additional tests are named explicitly.

| Identifier | Example | Affected systems | Technical reason | Evidence | Severity | Location | Tests | Known limitations | Possible false positives | Possible false negatives |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `duplicate-entry` | Two `same` entries | All; extractor-dependent outcome | One destination identity has multiple records | C; CPython 117779 | E | R:65 | corpus:duplicate, duplicate-directories; test_duplicate | Names compared exactly; no content comparison | Intentional ZIP append/history or repeated harmless directories | Different bytes decoded to an alias need other rules; local-header aliases not analyzed |
| `empty-name` | Zero-length central name | All ordinary destination filesystems | No nonempty member path | Z, C | E | R:70 | corpus:empty-name; test_empty_name | Not a general format-validity verdict; unusual ZIP producers can represent this | Stream-oriented ZIP records with intentionally absent names | Dot/root-only paths use other diagnostics |
| `absolute-path` | `/etc/x`, `C:file` | Windows/macOS/Linux in different ways | Rooted or drive-qualified name is not portable archive-relative identity | Z §4.4.17; W | E | R:73 | corpus:root-directory, drive-relative; test_absolute_and_drive_paths | `C:file` is drive-relative, despite code's broad name | An extractor intentionally strips roots | Does not inspect local headers, alternate fields or extractor destination handling |
| `backslash-path` | `a\\b` | Windows versus Unix-style systems | Backslash can be a separator or a literal filename character | Z §4.4.17 | E | R:75 | corpus:mixed-separators; test_backslashes_and_noncanonical_paths | Treated as separator for policy analysis everywhere | Literal POSIX backslashes intentionally distributed | No claim about target extractor's actual rewrite |
| `directory-metadata` | Directory attributes on `d` without slash | Extractors on all systems | Attributes and name convention disagree about member type | Z host-dependent external attributes; local fixture | W | R:85 | corpus:directory-attribute; test_directory_metadata_variants | Treats either directory indicator as directory for trie purposes | Attribute-aware extractor accepts it correctly | Host systems other than Unix/DOS attribute conventions are not modeled exactly |
| `parent-path` | `a/../b` | All; extractor-dependent | Parent components are not a canonical archive-relative spelling | W path semantics; Z; C | E | R:93 | corpus:parent; test_parent_paths | No traversal resolution or extraction | Benign path intentionally normalized by a known extractor | Links, local headers, alternate fields or extraction races are outside scope |
| `noncanonical-path` | `./README`, `a//b` | Especially Explorer; normalizers on all OSes | Dot and repeated-separator handling varies | libarchive 2489; C | W | R:95 | corpus:leading-dot, repeated-separators, dot-directory | Benign spelling notice, not guaranteed failure | Common Unix-generated archives work fine | Other extractor-specific normalization is not enumerated |
| `windows-character` | `part:name`, question mark, NUL | Windows; NUL also invalid in ordinary Unix paths | Reserved punctuation/control bytes; colon may address a stream | W; ouch 1090 | E | R:107 | corpus:forbidden, nul; test_windows_characters; real central NUL regression | One diagnostic per member even if multiple components fail | POSIX-only delivery or a deliberately literal POSIX name | Newly reserved characters, encoding-extra overrides; not an ADS/extraction defense |
| `trailing-dot-space` | `foo.`, `foo ` | Common Win32 tools | Trimming/refusal can change path identity | W; Go 80123; local probe | E | R:114 | corpus:trailing-dot, trailing-space; test_trailing_characters | ASCII space/dot policy, not complete Win32 emulation | Extended namespace/API or POSIX target retains names | Other namespace-specific rewrites and filesystem-specific whitespace handling |
| `windows-device` | `CON`, `NUL.txt`, `COM1`, `CONIN$` | Windows | Device/console aliases are not ordinary file basenames | W, P; ouch 1090 | E | R:121 | corpus:devices/device-extensions covers ten names including console and superscript variants; test_windows_devices | Extension/space approximation; no device handles opened | Non-Windows-only distribution | Future Windows aliases and unusual namespace behavior |
| `long-component` | 256 ASCII characters; 86 Japanese characters | ext4 and common Windows volumes; others vary | Typical component limits count bytes or UTF-16 units differently | K, L; local probe | W | R:126 | corpus:long-ascii-component, long-utf8-component, valid-boundaries | Common 255 threshold; not a queried destination limit | Filesystems allowing longer names | Whole-path limits, decomposed filesystem lengths, encrypted names with smaller limits |
| `alternate-name-metadata` | Raw `safe`, 0x7075 name `NUL.txt` | Extractor/Python-version dependent | Unicode path extra field can supply a second naming authority | Z Unicode path extra field; inspected C parser | W | R:135; helper R:23 | corpus:alternate-name; test_alternate_name_field_after_unrelated_extra | Presence notice only; alternate names not linted | Matching, harmless alternate name still warned | Other extra-field conventions, local-header overrides and conflicting extra authorities |
| `symlink-entry` | Unix link metadata on `link` | Extractor/privilege dependent on all OSes | Link creation and treatment differ | Z attributes; C | W | R:143 | corpus:symlink; test_symlinks_and_special_files | Link payload/target is not read | Intentional, correctly handled links | Other host metadata and disguised links; no unsafe-link protection |
| `special-entry` | Unix FIFO mode | Mostly Unix; unsupported elsewhere | Nonregular file type may not be representable | Z attributes; current extraction implementations | W | R:149 | corpus:special; test_symlinks_and_special_files | Unix-origin mode only | Intentional specialist archives | Other creator-system conventions; no special-file extraction guarantee |
| `file-directory-conflict` | `thing` plus `thing/child` | Common filesystems on all OSes | One path cannot simultaneously be a regular file and directory | Namespace semantics; hatchzip; pathward fixture | E | R:163 | corpus:file-directory/directory-file; test_file_directory_conflicts_in_both_orders | Related member may be the child that introduced an implicit directory | Ambiguous directory attributes or extractor deliberately renames | Unsupported metadata interpretations or alternate naming authorities |
| `portable-name-collision` | `README`/`readme`, NFC/NFD, `foo`/`foo.` | Case-insensitive Windows/macOS; normalization-insensitive FS; optional Linux modes | Component trie compares NFC, full casefold and trimmed suffixes | W, A; Go 80123; local probe | E | R:170; key R:19 | corpus:case, nested-case, Unicode and trailing cases; test_related_member_index_and_determinism | Conservative policy, not NTFS/APFS equivalence; Python Unicode tables vary | `straße`/`strasse` on tested Windows; disjoint merged directories; case-sensitive targets | 8.3 aliases, destination-existing names, exact OS Unicode exclusions/versions |
| `normalized-path-collision` | `a/b` plus `a/./b` | Extractor-dependent across systems | Removing separator/dot spelling differences yields same file | C path normalization; Z | E | R:178 | corpus:mixed-separators/repeated-separators; test_normalized_path_alias | Uses lexical policy; directory merges covered separately | Extractor preserves the spelling literally | Nonlexical rewrites, links and destination state |

All these checks analyze archive metadata. None grants permission to extract.
Policy checks sometimes overlap: `foo.` legitimately yields both a suffix error
and a collision with `foo`; a colon after a single letter can also be drive syntax.
An initially mistaken test expectation around `a:b` was corrected by using
`part:name`; this was a fixture error, not a scanner defect.

### Missing checks, consciously not added

Full destination path limits depend on extraction root, filesystem, OS settings
and API; the 4,808-character `long-full-path` corpus member currently yields no
findings. This is an explicit coverage gap, not proof of portability. Also absent:
exact APFS/HFS+/NTFS Unicode models, short-name aliases, existing destination
collisions, legacy encoding selection, Unicode confusables/bidi, all creator-system
attributes and full extra-field naming reconciliation. No new platform rules
were invented from speculation. Length warnings, console aliases, directory
ambiguity and alternate-name notices were small, evidence-backed corrections.

## Bugs and corrections

Initial adversarial run: six failing assertions and one unexpected exception.
One failure was the drive-syntax fixture mistake noted above. The actionable
findings were:

1. **Invalid path exception leaked**: `scan_archive('bad\0path.zip')` raised raw
   ValueError. Now translated to ScanError with context. Regression:
   `test_nul_input_path_has_useful_api_error`.
2. **Parser warning broke output contract**: an empty 0x7075 Unicode name emitted
   a Python warning, with a local library path, on JSON-mode stderr. Parser
   UserWarnings are now operational failures with status 2. A controlled warning
   regression is version-independent; a separate real empty-field regression
   checks the JSON/stderr contract while allowing older parsers to ignore the
   extension (strict warning exit 1) and newer parsers to reject it (exit 2).
3. **Directory false positive**: Unix/DOS directory metadata without a trailing
   slash was indexed as a regular file. Now a warning explains the ambiguity;
   either directory indicator reserves the node as a directory. Corpus and DOS/
   slash-versus-mode regressions cover this policy.
4. **Alternate naming authority hidden**: raw `safe` plus a Unicode extra-field
   `NUL.txt` was reported without findings. Now extra-field presence warns that
   alternate names are not analyzed. This does not implement secure reconciliation.
5. **Long components silently passed**: added a conservative warning for common
   byte/code-unit bounds, with clean boundary cases to prevent off-by-one errors.
6. **Console aliases omitted**: added CONIN$/CONOUT$ to the device policy using
   Python's authoritative reserved-path description; corpus covers extensions.
7. **Claims and UX**: expanded platform context/remedies, exit help and scope
   warnings; changed headline; removed unsupported two-minute installation claim;
   qualified ZIP64 and whole-scan complexity; disclosed the closest competitor.

No known destructive runtime behavior was found: scanning remains read-only.
The primary remaining serious release issue is unverified cross-platform behavior,
not a discovered extraction bug. This tool does not implement extraction.

## Corpus and independent test assessment

[archive_corpus.py](tests/archive_corpus.py) writes explicit little-endian ZIP
records with fixed timestamps, UTF-8 flags and creator attributes. This avoids
host-dependent ZipInfo rewriting of backslashes. **36 archives** are generated
under `audit/corpus/`; ZIP binaries are ignored by Git and regenerate on demand.
[Approved manifest](tests/corpus-manifest.json) pins hashes, entry counts and
expected finding codes. The fixture writer follows the published record layout;
ordinary fixtures also pass Python CRC/read checks, providing a separate check
against a broken fixture generator.

Coverage includes every category requested: case, trailing dot/space, device
names/extensions, forbidden characters, duplicate files/directories, both
file/directory orders, nested aliases, leading dot, mixed/repeated separators,
long components/full paths, CJK/emoji/accents, NFC/NFD/Hangul/full casefold, CP437,
empty name/archive, unusual directories, links/special types, alternate names,
10,000-entry clean input and valid boundary cases. A separate 10,001-entry test
checks a configured cap at and over the boundary. A deep-path regression avoids
recursive traversal. The suite does not create device files or extract links.

The original tests were useful but insufficient: many only asserted membership
of a finding code. New tests require exact corpus code sequences, severities,
member-to-index correspondence, a checked-in byte-hash manifest and an exact JSON
golden report. CLI coverage now includes Unicode/dash-leading input paths, version
text, help warnings, size and entry config precedence, empty config, invalid UTF-8,
missing/directory config, stderr separation and useful errors. Permission failure
is mocked rather than relying on chmod behavior under administrator/root accounts.

Malformed fixtures cover truncated endings, central signatures, invalid UTF-8,
corrupt extra data and unsupported versions. Forty-five bounded central-field
mutations test exception containment; this is not exhaustive fuzzing. A small
ZIP64 central-directory fixture is read successfully; multi-gigabyte operation
and ZIP64 end-record extremes were not tested. Corrupt payload/local-header
fixtures deliberately receive no filename findings while actual member reads
fail: a regression documents the security/integrity non-goal.

The completed local suite has **53 tests** plus corpus subcases. Branch-aware
coverage includes CLI child processes via coverage.py 7.11.0. Coverage is a gap
locator, not a correctness proof; no release verdict is based on its percentage.
All 235 statements and 94 recorded branches executed in the local run, with zero
reported missing branches. See [coverage summary](audit/coverage-summary.json)
and `audit/coverage.json` locally. This does not cover every possible name or ZIP.

## Cross-platform verification status

Configured in [.github/workflows/ci.yml](.github/workflows/ci.yml):

- `windows-latest`, `ubuntu-latest`, `macos-latest`.
- Python 3.11, 3.12, 3.13, 3.14, 3.15: **15 combinations**, each running the
  complete suite, filesystem observation script and clean-build/wheel verifier.
- Separate Ruff, formatting, mypy and distribution-build job.
- Read-only permissions, checkout credentials disabled, Actions pinned to the
  v6 commit refs resolved from GitHub's API during this audit; manual dispatch
  configured. No automatic publishing/upload job.

**Executed:** Windows 11 / Python 3.12.10 only. **Not executed:** hosted GitHub
Actions, Ubuntu, macOS, or other Python versions. There is no configured Git remote
in this workspace. Uploading source or invoking a public workflow would violate
the instruction to keep this local, so no remote CI was attempted.

Rule expectations are host-independent, while filesystem probe observations
legitimately vary by volume's case/normalization settings. Permission exceptions
and OS error strings can differ. Python Unicode data and parser warnings differ
by runtime version. Tests assert semantics rather than host-specific strerror
text. JSON formatting/line endings and input archive path strings are not claimed
byte-identical across operating systems. Exact policy codes for the pinned corpus
are what the matrix is intended to confirm.

## README and CLI claims audit

Every README section was read against implementation and exercised commands.
Headline now describes filenames rather than implying extraction validation.
No-network/no-telemetry/no-extraction claims are supported by source review and
member-open prohibition/unchanged-byte tests; these tests are not an OS sandbox.
Configuration precedence is explicit and tested; warnings/default exit 0 and
strict exit 1 are documented. `--help` explains statuses and security scope.
Text names/errors remain ASCII JSON-escaped, preventing raw ANSI/control injection.
Messages identify the member, related path, platform/policy reason and remedy.

The README now explicitly disclaims protection against **Zip Slip, zip bombs,
malicious payloads, unsafe symlinks, malware and arbitrary extraction
vulnerabilities**. Detecting lexical `..` is not proof of containment for a later
extractor. Alternate names are warned about, not fully checked. A clean filename
report can coexist with corrupted payloads or local headers, as tests demonstrate.

Current benchmark rerun: 2,000 members, 16,384,000 uncompressed bytes,
278,022-byte repetitive synthetic ZIP, seven warm-cache repetitions. Median scan
**11.448 ms**, CRC **57.610 ms**, Python 3.12.10 / Windows 11.
[Raw measurements](benchmarks/audit-results.json). This is **not equivalent work**,
not a compelling performance differentiator, and not a measured developer-time
benefit. CPU/peak memory, realistic datasets and cold-cache behavior are unmeasured.
Historical measurements remain labeled as historical; the current README cites
the rerun. No new speed ratio is advertised.

## Directory scanning and identity

Directory scanning could catch generated staging-name mistakes before expensive
packaging on Linux, but it cannot represent duplicate ZIP entries or packaging
rewrites, and some bad names cannot coexist on the scan host. Existing source
hooks already cover many early checks. [Future-feature assessment](docs/DIRECTORY_SCANNING.md)
records costs, symlink/race policies, proposed subcommands and compatibility.
**No directory scanning or subcommand migration was implemented.**

Exact-name queries returned PyPI/npm/crates.io HTTP 404 and GitHub repository-name
search HTTP 200 with zero public matches. Search also covered ZipNameGuard,
zipnameguard, zip-name-guard and nearby names. This is a discoverability snapshot,
not name reservation, proof of availability, private-repository visibility or
legal/trademark clearance. `zipguard` is already a developer tool and other
products use similar names. The word Guard can suggest security functionality;
keep the filename-linter description prominent. No obvious exact-name conflict
requires an immediate rename, but recheck before release.

## Reproducible local release verification

[audit/verify_release.py](audit/verify_release.py) copies only project source and
fixtures into a disposable checkout within a checked workspace sandbox. It removes
PYTHONPATH/PYTHONHOME from subprocesses, builds in a fresh builder environment,
installs the resulting wheel with `--no-deps` in another environment, and runs
the tests from outside that checkout. This prevents an editable/source import from
concealing a broken wheel. It executes the README's real activation/install/demo
commands in PowerShell without changing execution policy, or Bash on Unix hosts.

The executable transcript and statuses are recorded in
[audit/verification-windows.json](audit/verification-windows.json), including
metadata, commands, stdout/stderr and artifact hashes. Temporary paths are replaced
with `<SANDBOX>`/`<WORKSPACE>` and user-home prefixes with `<USER>`. Artifacts are
local under `dist/`, with SHA256SUMS.
This automates repeatable verification, not a claim of bit-identical builds with
unlocked backend/transitive dependencies or differing build timestamps.

Commands executed during the audit (PowerShell; paths relative to checkout):

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe tests\archive_corpus.py --output audit\corpus
.\.venv\Scripts\python.exe audit\check_registries.py
.\.venv\Scripts\python.exe -m venv .venv\audit-tools
.\.venv\audit-tools\Scripts\python.exe -m pip install pathward==0.2.0 zipguard==0.2.0 coverage==7.11.0
.\.venv\audit-tools\Scripts\python.exe audit\compare_competitors.py
.\.venv\audit-tools\Scripts\python.exe -m pip install --no-deps -e .
$env:COVERAGE_FILE = Join-Path (Get-Location) 'audit\.coverage'
.\.venv\audit-tools\Scripts\python.exe -m coverage run --rcfile audit\coverage.ini -m unittest discover -s tests
.\.venv\audit-tools\Scripts\python.exe -m coverage combine --append
.\.venv\audit-tools\Scripts\python.exe -m coverage report -m
.\.venv\audit-tools\Scripts\python.exe -m coverage json -o audit\coverage.json
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\ruff.exe format --check .
.\.venv\Scripts\mypy.exe
.\.venv\Scripts\python.exe audit\probe_filesystem.py --output audit\filesystem-windows.json
.\.venv\Scripts\python.exe benchmarks\benchmark.py --output benchmarks\audit-results.json
.\.venv\Scripts\python.exe audit\verify_release.py --output audit\verification-windows.json --artifacts dist
```

The release verifier's recorded subcommands include fresh `venv`, `pip install
build==1.3.0`, `python -m build`, wheel `pip install --no-deps`, `pip check`, version
and metadata inspection, the complete installed-wheel suite, valid/invalid corpus
CLI invocations and exact README source installation. It asserts name/version
agreement, the console entry point, MIT metadata, minimum Python and that all
Requires-Dist entries are optional dev requirements. No global packages or system
settings are modified. Build/runtime internet access is needed for installer
dependencies; scanning itself has no network calls.

Observed verification results:

| Check | Result |
| --- | --- |
| Fresh source distribution and wheel build | Passed |
| Clean wheel install with `--no-deps`; `pip check` | Passed |
| Imports resolve beneath the fresh environment, outside source checkout | Passed |
| Name/version 0.1.0, MIT, Python >=3.11, console entry point, dev-only dependencies | Passed |
| All 53 tests against the installed wheel | Passed |
| Representative strict valid/invalid/operational cases | Expected exit 0 / 1 / 2; valid JSON |
| README PowerShell venv activation, source install and demo | Passed without execution-policy changes; three findings, demo exit 1 |
| Ruff, formatting and strict mypy | Passed |
| Other OSes / hosted CI | Not run; release gate remains open |

The completed verifier transcript is the source of truth for local command
results. Artifact hashes can change between builds; consult the transcript and
current `dist/SHA256SUMS` rather than an earlier distribution from this workspace.

## Independent answers and final recommendation

**Is the problem real?** Yes: recent reports, primary platform rules and this
machine's probe agree on relevant failures. This does not establish adoption.

**Meaningfully differentiated?** Modestly, as a release CLI with accumulated,
related-path diagnostics. No, as a new underlying validation capability: pathward
already offers most of that in a dependency-free inspection library.

**Would I install it?** For a cross-platform ZIP release pipeline after the matrix
passes, yes, if accumulated CLI findings are useful. For an embedded Python
workflow I would first consider existing pathward inspection or existing checks.

**Is v0.1 scope appropriate?** Yes. Keep metadata-only ZIP filename linting.
Directory scanning, security guarantees, auto-renaming and more formats should
not be added to justify the project.

**Serious bugs?** Several reliability/false-result defects were fixed and regressed.
No known remaining destructive scanner bug was demonstrated. Remaining gaps can
produce false positives/negatives and are documented; missing cross-platform
execution is a serious validation gap for this positioning.

**Misleading claims?** Earlier differentiation and verification wording was too
easy to overread; it has been qualified. Whole-scan linearity and blanket ZIP64
support were stronger than demonstrated and have been narrowed. Security scope,
casefold false positives and unsupported destination lengths are now explicit.

**Ready for public release?** Not yet. Require successful matrix results and a
review of any OS/version differences first. Do not substitute test counts or
branch coverage for that gate. A small maintainer trial should then validate
whether the CLI convenience earns an additional tool in the workflow.

Three strongest reasons to use it:

1. Check the final artifact, including generated names, with one CI command.
2. Receive multiple actionable findings and both involved names without extraction.
3. Get deterministic policy ordering, terminal-safe text and structured JSON with
   no runtime dependencies.

Three strongest reasons not to use it:

1. Existing pathward/source hooks or a short local policy script may already suffice.
2. Conservative normalization can be noisy, while destination-specific compatibility
   and extraction safety remain outside scope.
3. It is an unproven new project with no successful cross-platform matrix or real
   maintainer adoption evidence yet.

**Final recommendation: NOT RELEASE READY; retain locally.** Local fixable issues
were addressed and verification rerun. Remaining gates require evidence from
other environments, not additional speculative features. Nothing was published.
