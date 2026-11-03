# Contributing

Start with the README installation instructions, then install `.[dev]` in your
virtual environment. Run `python -m unittest discover -s tests -v`, `ruff check .`,
`ruff format --check .`, `mypy`, and `python -m build` before submitting a change.
Runtime dependencies are intentionally empty. Explain any proposed new dependency.

Bug reports should include Python/OS versions, the command, actual output,
expected output, and a minimal ZIP creation script. Avoid uploading proprietary
or sensitive archives. Test fixtures should be generated with zipfile in temporary
directories, so the test suite works on Windows without creating illegal disk names.

Prioritize false positives, missed collisions and extractor behavior supported by
reproducible evidence. New rules need a documented policy and regression cases.
Changes to finding codes or JSON fields affect consumers; document them in the
changelog and assess whether a schema-version change is required. Keep report
order deterministic. Do not auto-rename, extract, execute or read member payloads.

Pull requests should explain the user problem, behavior change, tests and limits.
Contributions are provided under the repository's MIT license. Do not copy code
from another project without compatible licensing and attribution.
