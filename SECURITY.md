# Security scope

ZipNameGuard is a filename portability checker, not an archive security validator.
A successful scan is not permission to extract untrusted files. Only the central
directory is inspected. CRCs, local headers, extra-field filename overrides,
payloads, encryption, link targets and overlap attacks are outside the current
scope. The program never extracts or executes entries, but Python must parse
untrusted ZIP metadata in-process.

There is no protection guarantee against Zip Slip, zip bombs, malicious payloads,
unsafe symlinks, malware or arbitrary extraction vulnerabilities. Diagnostics are
filename-policy findings, not a secure-extraction decision. A Unicode path extra
field triggers a warning; the alternate name is not recursively analyzed.

The default byte cap is checked before parsing; the entry cap is checked after
metadata is loaded. These caps do not provide a hard RAM/CPU guarantee. Run
adversarial inputs inside your own OS sandbox and resource limits.

There is no public security contact or GitHub repository configured yet. Before
publishing, enable GitHub private vulnerability reporting. Do not put sensitive
files, credentials, or a weaponized archive into a public issue. A harmless fixture
creation script is preferred for ordinary portability bugs.
