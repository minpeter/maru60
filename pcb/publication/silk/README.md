# preserve Maru60 PCB silkscreen artwork variants

## Status

Preserves both original single and paired silkscreen artwork/footprint variants. artwork-proof-only.kicad_pcb is an artwork test board, not a functional keyboard PCB. Identical proof-board bytes are retained in both original packet layouts; the actual artwork/footprint sources differ. No placement or routing of the A/B/V7 designs is changed. Historical proof images are not mechanical or manufacturing validation.

## Publication boundary

Published on 2026-11-03 at the owner's request to preserve the PCB work in GitHub pull requests. All design packets remain separate. This is a draft archive for review, not release, accepted-main adoption, fabrication approval, an order or a powered-board qualification. Main and housing PR #1 are unchanged.

Original packet documents mentioning "private" or "no public push" describe their historical freeze. They are retained verbatim; this publication is the subsequent authorized archive operation. Original manifests bind the original packet contents, not newly added publication reports.

Native PCB/schematic/project and library bytes are preserved. Fresh native DRC/ERC/parity reports (when listed) were generated from separate copies using KiCad 9.0.2; CAD bytes remained unchanged. No cold refill or physical/source witness algorithms were rerun for publication, so inherited advanced verification claims remain historical. Some archived scripts contain original absolute paths and depend on earlier unbundled tooling; inspect/update paths in a new copy before running them.

No fabrication output is generated. Remaining opens, warnings, component, assembly, mechanical, SI/PI/EMC, thermal, USB and power-state release gates must be resolved independently. PCB hardware license selection remains unresolved as documented in existing PR #2; third-party license/provenance files are retained.

## Recovery scope

Only available frozen packets were recovered. The earlier accepted-main PCB (recorded as SHA256 80681cd...f831) and every intermediate iteration were not recovered from these packets. Their historical mention is not proof that their original CAD is included. Timelapse source backup contains rendered SVG/video frames, not CAD versions, and is not mislabeled as PCB source.
