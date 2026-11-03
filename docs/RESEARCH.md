# Discovery and opportunity analysis

Research date: October 30, 2026. Scores are engineering judgments, not measured
market demand. Public reports prove failure modes, not willingness to adopt a
new tool. No interviews, user counts, or adoption forecasts have been fabricated.

## Ten opportunities

Score order throughout: usefulness / originality / technical value / feasibility /
open-source potential / adoption likelihood / reputation value. Overall is the
unweighted arithmetic mean, rounded to two decimals. Likelihood is comparative,
not a statistical probability. Contributor potential means plausible work, not
evidence that volunteers will arrive.

### 1. ZIP release filename preflight — selected

Problem: a readable ZIP can contain names that fail or alias on another system.
Users: release maintainers, dataset publishers, game asset teams. Workaround:
list names, write checks, or extract on Windows. Existing solutions: zipinfo and
CRC tests inspect archives; pre-commit checks source filenames; Go checks module
ZIPs; Pure performs broader format security analysis; hatchzip checks collisions
as part of extraction. Proposed solution: a dependency-free Python CLI that
checks the final ZIP without extraction and emits actionable, stable JSON.
Its niche is artifact-level filename policy in CI, not a new ZIP parser or security
scanner. Difficulty: moderate. Scope: small utility. Usefulness: narrow but clear.
Adoption: plausible in cross-platform release pipelines, unvalidated. Originality:
incremental packaging and diagnostics, not a novel algorithm. Contributors could
add platform profiles and real-world regression fixtures. Engineering value:
Unicode, implicit directory collisions, malformed metadata, deterministic APIs.
Scores: **9 / 5 / 8 / 9 / 8 / 7 / 8 = 7.71**.

Evidence: [Go collision report](https://github.com/golang/go/issues/33778),
[File Explorer path report](https://github.com/libarchive/libarchive/issues/2489),
[colon discussion](https://github.com/r-lib/zip/issues/70).
Alternatives: [pre-commit hooks](https://github.com/pre-commit/pre-commit-hooks),
[Pure](https://github.com/ronomon/pure),
[hatchzip](https://github.com/xevrion/hatchzip/blob/main/docs/how-it-works.md).
These are complementary tools and may be better choices for their own scopes.

### 2. Compose environment provenance explainer

Problem: developers confuse host interpolation and container variables. Users:
Compose operators. Workaround: `docker compose config`, inspect shell and env
files. Existing tool is authoritative but provenance requires interpretation.
Solution: explain each value's origin with secret redaction. Moderate; medium
project. Useful, but reproducing changing Compose semantics is costly. Adoption
plausible; originality low. Contributors: syntax support and fixtures. Serious
engineering: precedence and safe diagnostics. Scores: **8/5/7/6/7/7/7 = 6.71**.
[Report](https://github.com/docker/compose/issues/9442),
[existing precedence documentation](https://docs.docker.com/compose/how-tos/environment-variables/envvars-precedence/).

### 3. Offline Python installation readiness report

Problem: an apparently populated cache may not support an offline install. Users:
air-gapped Python teams. Workaround: actual offline installation or wheelhouse.
Solution: explain missing target artifacts before transfer. Difficult; medium.
Useful; cache internals and environment markers reduce feasibility. Existing uv
offline mode already detects failures; a new checker risks duplicating resolution.
Adoption uncertain; contributor potential: target matrices. Engineering: package
metadata/resolution. Scores: **8/6/9/4/7/6/8 = 6.86**.
[uv cache behavior](https://github.com/astral-sh/uv/blob/main/docs/concepts/cache.md).
Evidence here establishes constraints; new-tool demand is weak.

### 4. Executable shadowing diagnostics

Problem: Windows Python commands can resolve unexpectedly. Users: Windows devs.
Workaround: `where`, `Get-Command`, interpreter introspection. Solution: one report
of candidates, PATH ordering, aliases and environment mismatch. Moderate; small.
Existing shell commands solve much of this; shell-specific behavior limits a
universal tool. Adoption modest; originality low. Contributors: shell adapters.
Engineering: platform semantics. Scores: **7/4/6/8/6/6/6 = 6.14**.
[Python Windows behavior](https://github.com/python/cpython/blob/main/Doc/using/windows.rst).
Demand evidence is weaker than for the selected idea.

### 5. Read-only worktree cleanup planner

Problem: stale worktree directories and branch metadata confuse cleanup. Users:
parallel-development teams. Workaround: list, status, prune dry run and repair.
Solution: combine into a conservative explanation report. Moderate; small.
Git already supplies most mechanisms, so incremental value is limited. Adoption
plausible but crowded. Contributors: workflow adapters. Engineering: avoid data
loss and handle locked/offline trees. Scores: **7/4/6/8/6/6/6 = 6.14**.
[Git worktree manual](https://git-scm.com/docs/git-worktree).
Documentation establishes edge cases, not unsatisfied demand.

### 6. WSL localhost diagnosis bundle

Problem: network reachability differs between host and guest. Users: Windows web
developers. Workaround: curl both sides, inspect mode, ports and firewall.
Solution: read-only probe matrix and narrowly supported explanations. Difficult;
medium. Existing docs and diagnostics cover pieces; permission and version
variance are substantial. Adoption plausible; contributors: Windows fixtures.
Engineering: networking and reproducibility. Scores: **8/5/8/5/7/6/8 = 6.71**.
[Specific relay report](https://github.com/microsoft/WSL/issues/41860),
[existing implementation documentation](https://wsl.dev/technical-documentation/localhost/).

### 7. CI artifact contents contract

Problem: hidden files may be omitted from uploaded artifacts. Users: CI owners.
Workaround: explicit inclusion flags and inspect downloads. Solution: compare
artifact contents against a manifest. Moderate; small. Existing upload options
address the reported cause; manifest tools already exist. Adoption uncertain;
contributors: CI adapters. Engineering: globs and portable paths. Scores:
**7/5/6/8/6/6/6 = 6.29**.
[User report](https://github.com/actions/upload-artifact/issues/614),
[existing options](https://github.com/actions/upload-artifact).

### 8. Local LLM context memory advisor

Problem: context settings affect memory use and offloading. Users: local AI devs.
Workaround: adjust context and inspect `ollama ps`. Solution: explain observed
context/offload changes using measurements. Difficult; medium. Existing Ollama
auto defaults and status output address much of it; model-specific predictions
can mislead. Adoption uncertain. Contributors: empirical model profiles.
Engineering: measurement and hardware variability. Scores:
**8/4/8/5/7/6/7 = 6.43**.
[Ollama context and memory documentation](https://docs.ollama.com/context-length).
This supports the tradeoff, not a missing feature claim.

### 9. Docker cache retention planner

Problem: cache storage grows; pruning trades disk space for rebuild work. Users:
container developers. Workaround: `buildx du` and `prune`. Solution: read-only
retention recommendations. Moderate; medium. Existing prune space/age controls
already solve much of it. Adoption modest; originality low. Contributors:
builder adapters. Engineering: shared-layer accounting. Scores:
**7/4/7/7/6/5/7 = 6.14**.
[Existing prune controls](https://github.com/docker/buildx/blob/master/docs/reference/buildx_prune.md).
New-tool demand remains weak.

### 10. Order-dependent pytest failure minimizer

Problem: test order can expose hidden shared state. Users: Python maintainers.
Workaround: seeded random order and manual subset reduction. Solution: replay
and minimize a failing predecessor sequence. Difficult; medium. Existing
pytest-randomly/random-order cover discovery; minimization is valuable but
expensive and nondeterminism complicates confidence. Contributors: strategies
and plugin compatibility. Engineering: process isolation and delta debugging.
Scores: **8/6/9/5/8/6/8 = 7.14**.
[Empirical study](https://arxiv.org/abs/2101.09077),
[pytest-randomly](https://github.com/pytest-dev/pytest-randomly).

## Selection and rejection test

Choose **ZipNameGuard**, a working name. A maintainer would install it to gate
the final distributed artifact with one command on Linux or Windows, including
generated files not present in Git. It removes manual filename inspection and
the need to reproduce the same policy script in each repository. The value over
a quick script is handling directory prefixes, duplicate entries, Unicode
normalization, reserved devices, stable diagnostics, tests and documented limits.

Existing tools adequately solve related problems. This project's narrower value
is a lightweight standalone filename-policy report, with no extraction and no
runtime dependencies. Pure is preferable for deeper format/security analysis;
pre-commit is preferable for preventing source-tree mistakes. This is not a
claim that no equivalent tool exists. Search was bounded, not exhaustive.
Recommendation trigger: a report identifies the two exact members that would
alias before a release ships. Adoption must still be validated with maintainers.

## Identity candidates

ZipNameGuard (chosen), ArchiveNameCheck, MemberPathLint, ZipPathSentry,
ReleaseNameLint, ZipNameLens, ArchivePathGate, ZipPathCheck, MemberNameGuard,
ArchiveNameProbe. Search found existing ZipPort projects, so that name was
rejected. Exact searches for ZipNameGuard/zip-nameguard did not surface an obvious
major project; this is not trademark or registry clearance. Recheck before release.
Tagline: **Catch archive filename surprises before your users do.**
Description: **Read-only ZIP filename portability checks for release pipelines,
with actionable diagnostics, JSON output, and no runtime dependencies.**
Topics: zip, cli, python, cross-platform, windows, release-engineering,
developer-tools, continuous-integration.
