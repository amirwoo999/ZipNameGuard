# Changelog

## 0.1.0 — unreleased

Pre-release audit: corrected directory-attribute interpretation, contained parser
warnings in the error contract, handled invalid NUL input paths, added console
device names and conservative component-length/alternate-name warnings. Added a
36-archive deterministic corpus, stronger CLI tests, clean-release verification,
filesystem probes and a broader CI matrix. Public release remains on hold; see
PRE_RELEASE_AUDIT.md.

- Read-only ZIP member filename portability checks.
- Case/NFC/trailing-character collisions and implicit directory conflicts.
- Win32 names, path hazards, duplicate entries and link metadata diagnostics.
- Text/JSON CLI, explicit TOML configuration, CI exit codes and Python API.
- Generated regression fixtures, reproducible benchmark and cross-platform CI.

Initial release candidate; public adoption and remote CI results are unverified.
