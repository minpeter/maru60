# Restored work and evidence boundary

This commit preserves the complete restored Git history through be51692 and the exact saved GPIO25/power research supplement. It does not select a new PCB or authorize manufacture. The selected development CAD remains be51692 / PCB41f82c80 with 9 physical open pairs and 38 native warnings. The strict bbf61e6 baseline is also unchanged. LED power qualification remains disabled.

The adjacent `resume-20261106-gpio25-power-study` folder is the byte-preserved saved supplement, with its original manifest. Its nine GPIO25 transition candidates are rejected, not alternate production designs. See its START_HERE.txt and detailed reports. Historical statements that no external push had occurred describe the time of that report, before this publication request.

## Later work whose files were not recovered

A later interrupted work session had reported four integrated COL14/GPIO25 trials, all rejected because exact remote inner-plane GND-loss witnesses remained. It also reported a source-bound low-voltage host harness with 30 scenarios, 8 expected observability-limit reproductions, and 2 mutation controls, plus a relocation replay. Those executable artifacts were not found in the available workspace or saved supplement during this restoration. These are historical reported results only, not independently replayed results of this checkout. They must not be cited as available test evidence or treated as a hardware qualification. Reconstruct and rerun from source before relying on them.

The reason the earlier workspace is unavailable is unknown. This restoration does not claim that all transient work was recovered. No selected-design change was based on the missing tests.

## Continuing safely

Keep the strict and development selections separate. Do not promote rejected routing merely because native DRC reports fewer opens. A future GPIO25 topology must preserve exact retained return copper/contact conditions. Low-voltage work must distinguish software-observable state changes from an analog rail disturbance invisible to firmware, preserve default LED qualification OFF, and require physical source/load and fault-timing measurements before qualification.

Full archives and original Git history are preserved separately; duplicate transport ZIPs, temporary compiler binaries, caches, and vendor PDFs are not newly added here. No main-branch rewrite, firmware flashing, purchase, or manufacturing action is included.
