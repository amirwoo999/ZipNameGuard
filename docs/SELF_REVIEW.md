# Adversarial review

Historical initial review; see [PRE_RELEASE_AUDIT.md](../PRE_RELEASE_AUDIT.md) for
the subsequent independent re-audit and current release decision.

## Value and originality

The problem is evidenced, but adoption is untested. A shell script could catch
the simplest cases. Value depends on reusable, tested handling of implicit
directories, Windows devices, Unicode and stable CI reports. Equivalent tools may
exist outside the bounded search. README names alternatives and makes no claim
of algorithmic novelty or market leadership. Do not frame this as archive security.

## Risks addressed and review findings

- Full-prefix tuple/string indexing repeated work at each path depth. Replaced
  it with an iterative component trie and added a 2,000-level regression case.
- Python ZipInfo.filename truncates NUL names. Inspection uses orig_filename;
  real central-directory byte-patched regression verifies the full name is reported.
- Archive member names can contain terminal escapes. Text rendering JSON-escapes
  names and errors; subprocess test proves an ANSI escape is not emitted raw.
- Explicit directory entries can arrive after their children. Tests cover this
  and a subsequent differently cased directory without treating the normal case
  as a duplicate directory.
- Config booleans are Python integers for isinstance checks. Exact type checks
  reject boolean entry limits rather than silently treating them as one.
- Entry limits cannot prevent zipfile's initial metadata allocation. Docs now
  state the ordering clearly; no hard resource-bound or zip-bomb claim is made.
- A source checkout can conceal packaging defects. Build and install the wheel
  into a separate virtual environment and run the same suite there.

## Remaining risks and deliberate choices

Casefold/NFC is conservative and not filesystem emulation. Warnings for dot paths
can be noisy but are only fatal with explicit strict mode. Directory aliases are
policy failures even when children could merge. This favors release predictability.
No direct memory/CPU benchmark or real maintainer trial has been performed.
Version 0.1.0 remains an initial release candidate until remote CI and maintainer
trials provide more evidence. GitHub/PyPI names need checking at publication.

Dependencies: zero at runtime; pinned direct development tools. Transitive dev
dependencies are not hash-locked, so development environments are not guaranteed
bit-for-bit reproducible. GitHub Actions use maintained major-version refs;
pinning audited commit SHAs can follow when a real repository is established.
No unrelated project or global system configuration was modified.

## Maintainer judgment

This is worth trialing in a pipeline that distributes cross-platform ZIPs. It is
unnecessary for a project already using equivalent artifact checks, and should
not displace existing source hooks or a dedicated ZIP security analyzer. The next
proof of value must come from real archives and users rather than more features.
