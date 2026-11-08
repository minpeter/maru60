# Exact recovery review

**Pass for exact board recovery only.** Independent full-file SHA-256 and raw-object comparison confirm the historical U10, voltage-label, C128, width-repair and selected typography boards were recovered exactly. No native validation was rerun by this review.

## Verified

- Earlier 53-file input manifest and the recovered SI/C128 study manifests match their files.
- U10 has precisely the archived 1 removed and 10 added tracks.
- The voltage-label board differs from original U10 by exactly two ASCII Value characters, 5 to 4.
- C128 changes only its footprint and adds two tracks and one via. Every old zone block, including saved fill bytes, remains exact.
- Width correction adds only the named fixed-UUID +3V3 segment.
- Typography changes exactly 15 Reference sizes and four Reference anchors. All other objects remain exact.
- All recovered archive files remain unchanged throughout this audit.

## Recovery scope

The complete board SHA matches are conclusive for these board bytes. They do not recreate the missing historical QA suites, terminal evidence, complete later 54-file project map or Git objects. The source-bound study receipts are historical evidence, not fresh tests or qualification. Further work can use the exact selected board after separately restoring and binding its surrounding project.

See review.json for all full expected hashes, exact delta UUIDs, script pins and limitations. audit.py is a standalone read-only reproducer of this review. It writes only this review directory.
