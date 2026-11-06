# Recovered history publication safety audit

**Verdict:** No blocking secret, credential, or prohibited runtime/cache artifact identified. Local commit and bundle preparation can proceed within authorized scope. This is a bounded security audit, not manufacturing or firmware qualification.

## Scope

- Historical HEAD: `be51692d6b7c3069d20602cfb518370028179307`. Scanned all 3,632 unique reachable blobs across 18 commits, totaling 1,336,182,096 uncompressed bytes. Git integrity check passed.
- All 7 ZIP containers, including nested archives, were read successfully: 706 entries, 225,742,221 expanded bytes.
- Supplement commit: `4c90cdc95c7d1d29ab5fecf72cc5d24407b86714`. Scope is 855 files, 89,913,303 bytes. Of 853 previously scanned files, 851 were verified unchanged by SHA-256; updated validation/REPORT.md and validation/results.json were read in full. Newly added PUBLICATION_STATUS.json and UNRECOVERED_WORK_NOTES.md were also read in full. These four files are under pcb/experiments/resume-20261106-recovery-status; exact hashes are in AUDIT_COUNTS.json.

## Findings

- Zero high-risk credential signatures or suspicious secret assignments found.
- Historical low-signal matches: 8 email records and 11 local-path records, classified as public vendor copyright contacts, PSpice component identifiers, compressed-byte false positives, generic Inkscape environment paths, and vendor model author paths. No user-sensitive data was established.
- Broad filename checks found 1,632 historical QA-log records and 52 supplement QA logs. These are intentional engineering evidence, not automatically prohibited runtime payloads. No detected credential files, environment-secret files, dependency caches, virtual environments, executable libraries, or Python bytecode caches. KiCad preferences are nonblocking configuration evidence.
- Supplement personal-data matches were public copyright contacts in 11 vendor-file copies. The four added/updated status and validation files contain no credentials or sensitive personal data.
- Largest historical blob: `1e22d862ed1ffb81e84307952cab675e2c300b14`, `pcb/experiments/v7-c124-series-with-connector-ground/evidence/actual-D-frozen.zip`, 54,579,147 bytes (about 52.05 MiB). No blob exceeds 100 MiB. Existing Git packs total 122.66 MiB. Actual negotiated push-pack size was not measured.

## Limits and publication state

Byte-pattern scans included recursively decompressed ZIP entries, but no image OCR or semantic extraction of compressed PDF streams. Unknown or obfuscated credentials can evade detection. Identical historical blobs were deduplicated and represented by one path. Future edits are outside scope.

No push or credential creation was performed by the auditor. The reviewed publication-status file reports an authentication blocker and no remote mutation; this audit does not independently establish current remote state. Historical reconstruction notes explicitly describe unverified former results, not freshly executed tests.

AUDIT_COUNTS.json contains concise machine-readable scope, counts, exact hashes for four final reviews, and the aggregate supplement inventory digest. No secret values or raw scan logs are included.
