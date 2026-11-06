# Restored study validation

Selected repository HEAD: be51692d6b7c3069d20602cfb518370028179307.

- All 844 outer-manifest file hashes and byte lengths pass; no missing or additional files.
- All 58 current CAD files and all 22 firmware files match the selected repository byte for byte, with identical file sets.
- Power evidence source hashes independently checked against the selected repository: all 29 match.
- Portable power replay passes. It checks the archived netlist hash, snapshot net memberships and component-pad assertions (36 components / 181 pads). It does not regenerate a native netlist or remeasure hardware.
- Conditional current-limit arithmetic passes; generated CURRENT_LIMITS.json is byte-identical to the archived version. This is a snapshot-and-equation replay, not a dynamic circuit model or USB compliance certification.
- U18 CAD source hashes (board and project) match the selected repository. Native U18 replay was NOT RUN: hardcoded original source paths do not exist and the required vendor PDF is unavailable. System /usr/bin/python3 provides pcbnew 9.0.2; the default python3 does not provide pcbnew. No guards were removed and no dependencies were installed. Archived geometry is manifest-verified evidence, not a fresh native geometry result.
- All tests that can write outputs were run on copies under this validation directory. The complete original study remains hash-unchanged after tests.

This validates archive integrity and portable evidence consistency, not manufacturing readiness. The study remains an analysis supplement: no routing candidate selected; inherited 9 open connection pairs and 38 warnings are not freshly revalidated here. Hardware, dynamic power, thermal, SI/EMI and full firmware qualification remain unperformed. No push, installation, credential use or original-source modification was performed by this validation.

Machine-readable detail: results.json. Reproduction scripts: validate.py, bind_sources.py. Portable execution stdout/stderr: replay.py.log and current_limits.py.log.
