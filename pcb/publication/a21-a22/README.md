# preserve Maru60 A21/A22 four-layer PCB checkpoints

## Status

A21: 21 opens, 0 hard DRC, 58 warnings, parity 0, ERC 0. A22 predecessor: 22 opens, 0 hard DRC, 59 warnings, parity 0, ERC 0. The exact A22 PCB/project is retained at a21/coordinator-evidence/source.kicad_pcb and source.kicad_pro; use its matching root schematic/libraries in a separate working copy. A21 closes the actual remote ENABLE function and includes A22 FAULT history. This checkpoint remains isolated and has not been adopted as accepted-main.

## Publication boundary

Published on 2026-11-03 at the owner's request to preserve the PCB work in GitHub pull requests. All design packets remain separate. This is a draft archive for review, not release, accepted-main adoption, fabrication approval, an order or a powered-board qualification. Main and housing PR #1 are unchanged.

Original packet documents mentioning "private" or "no public push" describe their historical freeze. They are retained verbatim; this publication is the subsequent authorized archive operation. Original manifests bind the original packet contents, not newly added publication reports.

Native PCB/schematic/project and library bytes are preserved. Fresh native DRC/ERC/parity reports (when listed) were generated from separate copies using KiCad 9.0.2; CAD bytes remained unchanged. No cold refill or physical/source witness algorithms were rerun for publication, so inherited advanced verification claims remain historical. Some archived scripts contain original absolute paths and depend on earlier unbundled tooling; inspect/update paths in a new copy before running them.

No fabrication output is generated. Remaining opens, warnings, component, assembly, mechanical, SI/PI/EMC, thermal, USB and power-state release gates must be resolved independently. PCB hardware license selection remains unresolved as documented in existing PR #2; third-party license/provenance files are retained.

## Recovery scope

Only available frozen packets were recovered. The earlier accepted-main PCB (recorded as SHA256 80681cd...f831) and every intermediate iteration were not recovered from these packets. Their historical mention is not proof that their original CAD is included. Timelapse source backup contains rendered SVG/video frames, not CAD versions, and is not mislabeled as PCB source.
