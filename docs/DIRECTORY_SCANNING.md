# Directory scanning: defer beyond v0.1

Scanning a staging directory before ZIP creation could catch Windows device names,
forbidden characters, trailing dots/spaces, Unicode/case aliases and long
components earlier, especially on Linux build runners. It can reduce iteration
time when packaging is expensive. Generated release assets are a better candidate
than Git source trees, which already have pre-commit filename hooks.

It cannot replace the final ZIP scan: directory enumeration cannot represent
duplicate ZIP entries, and packaging can rewrite paths, add extra metadata,
generate new members or change link/directory attributes. On a case-insensitive
host some conflicting names cannot coexist in a directory in the first place.
Archive members may also contain names the build host cannot create.

Adding it would require deliberate policies for symlinks and junctions (do not
follow by default), ignored files, inaccessible paths, traversal bounds, snapshot
races, deterministic enumeration, relative display paths and destination-volume
lengths. The current rules accept ZipInfo metadata; a future directory adapter
should share a neutral member model rather than fabricating ZIP attributes.

Proposed future UX: `zipnameguard scan ./dist-directory` and
`zipnameguard archive release.zip`, with compatibility for the existing positional
archive command during a documented migration. These commands are proposals and
are **not implemented**. Do not introduce subcommands in the current release.

Priority: medium after the release matrix and maintainer trials. Validate with a
maintainer whose packaging step is measurably expensive; otherwise source hooks
and the final-archive check may already be enough.
