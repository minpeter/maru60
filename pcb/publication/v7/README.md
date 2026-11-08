# preserve Maru60 V7 protection-integration checkpoint

## Status

V7 checkpoint 02: 53 opens, 0 hard DRC, 123 warnings, parity 0. Original archive replay produced 5 ERC library warnings because engineering/Maru60_Options.kicad_sym was omitted. The unchanged shared symbol library from the A21 packet is supplied as a packaging repair (SHA256 f4f200b7b158eb086c33ec7ac46533e1a3d1e1fa29c13c0137208e97c0dad6e0); replay then produced ERC 0. No PCB, schematic, project, footprint or routing bytes were changed. V7 has 382 footprints and adds protection/power parts. Fine-pitch grounds, LDO IN/EN, buck and inter-block routing remain unfinished. Nine GND pads remain source-unreached in the inherited audit. Thermal, power-off injection, reset, USB current and fault qualification remain open.

## Publication boundary

Published on 2026-11-03 at the owner's request to preserve the PCB work in GitHub pull requests. All design packets remain separate. This is a draft archive for review, not release, accepted-main adoption, fabrication approval, an order or a powered-board qualification. Main and housing PR #1 are unchanged.

Original packet documents mentioning "private" or "no public push" describe their historical freeze. They are retained verbatim; this publication is the subsequent authorized archive operation. Original manifests bind the original packet contents, not newly added publication reports.

Native PCB/schematic/project and library bytes are preserved. Fresh native DRC/ERC/parity reports (when listed) were generated from separate copies using KiCad 9.0.2; CAD bytes remained unchanged. No cold refill or physical/source witness algorithms were rerun for publication, so inherited advanced verification claims remain historical. Some archived scripts contain original absolute paths and depend on earlier unbundled tooling; inspect/update paths in a new copy before running them.

No fabrication output is generated. Remaining opens, warnings, component, assembly, mechanical, SI/PI/EMC, thermal, USB and power-state release gates must be resolved independently. PCB hardware license selection remains unresolved as documented in existing PR #2; third-party license/provenance files are retained.

## Recovery scope

Only available frozen packets were recovered. The earlier accepted-main PCB (recorded as SHA256 80681cd...f831) and every intermediate iteration were not recovered from these packets. Their historical mention is not proof that their original CAD is included. Timelapse source backup contains rendered SVG/video frames, not CAD versions, and is not mislabeled as PCB source.
