# Unselected C139-only buck reference correction

Candidate: `candidate/pcb/maru60.kicad_pcb`
SHA-256: `2b5787cc27e7fea92dff2ad483185fccfab1d2d27bf07662395de26f7ab14d69`
Source: `4765dfd82f70cfcfc00c06b4d9abfb614c7d657ec086fcf57c28d49bc3236136`

Only C139 Reference changed: position from (179.97,85.0) to (181.4,81.8) mm; 90 degrees unchanged; height/width 0.75 to 0.8 mm; 0.1 mm stroke unchanged; visible and mirrored B.Silkscreen unchanged. Its vertical column is centered exactly on its own footprint. Actual text ends immediately above its own courtyard rather than a neighbor. Native rendered back-side image was inspected at images/buck-trial.png: C139 is readable and separated from C141, C138, U18 and its owner's body. Existing R159 and C136 defects remain visible and unchanged.

qa/raw-warning-comparison.json verifies exact raw one-Reference-only delta, all 57 companion hashes unchanged, every electrical object and all 12 filled zones exact. Native KiCad 9.0.2 DRC with explicit schematic parity reports 55 to 51 warnings, four removed and none added, the same 12 unconnected records, no other hard DRC or parity issues. qa/cold-refill.json verifies normal fresh-process cold refill produces byte-identical candidate. All native calls use five private 0700 XDG directories and offscreen Qt.

Actual new ink lower bounds: raw closed nominal courtyard 0.279524 mm; actual raw drawn-stroke courtyard 0.254524 mm; mask 0.534524 mm; other silk 0.441666 mm; filled Fab 0.833846 mm; unreconstructed source Fab 4.330169 mm; edge at least 10 mm. Nominal and stroke both pass 0.20 mm. Geometry results are in qa/three-boundaries.json. Native cached courtyard reports 0.284524 mm and is NOT used as the nominal acceptance value. Closed raw polygons and line/arc chains are reconstructed separately from stroke envelopes; circles are filled disks at raw centerline radius. These are 2D proxies, not 3D assembly proof.

## Remaining concrete crowding blockers

R159 is packed between R160 and C139; direct side placements intersect neighboring component courtyards. Its top-facing pocket is constrained by C141 and the existing C141 reference. A read-only 0.1 mm grid screen, horizontal and vertical 0.8/0.1 mm typography, within 3.5 mm of the owner found only five geometric fits, all around (181.6–181.9,81.7–81.8) mm: over the C139 column, now occupied by C139's unambiguous reference. Moving R159 there would misassociate the label and is rejected.

C136 lies directly below U18 and above/right of C137, beside SW14. The narrow U18/C136 gap cannot accept readable text with required courtyard margin. The same local screen found free positions only starting around (176.8,89.6) mm below/right alongside C137, rather than immediately next to C136. These would risk C137/C136 association and are rejected. No claim of exhaustive continuous mathematical infeasibility: this is a bounded local screen plus inspected ownership constraint, not permission for a broad cosmetic sweep.

Screen candidates were in-memory only; no failed PCB candidate was generated. Exactly one real unselected PCB candidate was written and retained. No selected or prior frozen files changed. Parent owns independent review and any install/commit/backup. Full circuit/model, QMK, manufacturing, hardware and SI qualifications remain unchanged.
