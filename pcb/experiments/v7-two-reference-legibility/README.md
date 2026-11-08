# Two-reference legibility correction

Experimental working selection only. Open `candidate/pcb/maru60.kicad_pro`. PCB SHA256: 4765dfd82f70cfcfc00c06b4d9abfb614c7d657ec086fcf57c28d49bc3236136. The preceding abdb electrical snapshot is preserved in its own unit.

Only U18 and L2 Reference fields change: visible mirrored B.Silkscreen, 0.8 × 0.8 mm text and 0.12 mm stroke, horizontal. U18 anchor is (176.65, 84.25) mm and L2 is (174.95, 77.90) mm. Both have unambiguous adjacent ownership in actual native plots. No footprint placement, circuit value, copper, pad, drill, saved plane, rule or other reference changes.

Fresh DRC 61→55: exactly six label warnings removed, none added. All 12 raw expansion-open records remain identical; other hard errors and explicit schematic parity are 0. Prior ERC 0 is inherited from byte-identical schematics and circuit data, not a newly claimed ERC execution. Inventory remains 9,750 tracks / 919 vias / 383 footprints / 13,184.45545001526 mm.

Independent actual-label review, exact byte carry, actual pixels and separate combined cold refill pass. Reverting only the two fields recovers abdb byte-for-byte; all 57 project companions remain exact. Therefore the completed serial-leg material/support/reference checks inherit as identical electrical inputs; no duplicate graph or signal simulation is claimed.

## Courtyard interpretation and rejected first trial

The initial unselected 21083 candidate passed the cached native courtyard reading but fails the exact raw closed nominal boundary:U18 gap 0.149525 mm is below the unchanged0.150mm target by 0.000475 mm. Its cached value was 0.154525 mm. It remains rejected with source, trial and evidence intact. The successor shifts both references 0.10 mm farther away. Actual nominal/drawn-stroke gaps are U18: 0.249525 / 0.224525 mm and L2: 0.276145 / 0.251145 mm. Both exceed the new candidate's explicit 0.20 mm target. All other native mask/silk/Fab/edge tests pass.

The cached filled area, exact closed nominal courtyard and drawn graphic stroke envelope are distinct. The four earlier adopted labels C100/R140/R160/R134 still pass their original nominal-boundary target; C124/R121 also pass. Optional stroke-envelope shortfalls are not mislabeled as retroactive failures of the earlier nominal criterion. Existing U8/R125 reference intersections with courtyard proxies remain unchanged and are not newly claimed clear. This is a scoped artwork correction, not whole-board assembly or actual 3D visibility qualification.

All prior power, startup/reset/brownout, pulse, input-fault, environmental, physical SI/ESD/EMC, assembly and hardware limits remain. LED qualification stays OFF. Read the preceding C124 adoption-risk brief. No fabrication, flashing, push or stability benefit is implied.

`frozen-carry` preserves the completed actual combined run. `independent-label-review` binds actual 99c2 to the corrected full geometry tests; `independent-carry-review` proves the exact carry and independent refill. The rejected 21083 records and independent review are separately preserved. Frozen original phase labels remain UNSELECTED; this adoption record is the later limited experimental decision. Absolute historical run paths are provenance, not a relocated one-command replay promise.
