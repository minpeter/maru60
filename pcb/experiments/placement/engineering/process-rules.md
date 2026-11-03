# Candidate process rules — NOT a fabrication approval

The first native placement declares 0.15 mm minimum copper clearance, 0.15 mm copper-to-drill clearance and 0.25 mm minimum through-hole drill. These are design targets that a selected fabricator must explicitly accept; no supplier or order is selected.

Why not untouched KiCad defaults:
- Official RP2350A R4 footprint adjacent pad edges are 0.17 mm apart; a default 0.20 mm netclass rule flags the component itself.
- Official RP2350A thermal-via drills are 0.25 mm; a default 0.30 mm drill minimum flags the reference footprint itself.
- The standard GCT USB4105 candidate footprint has 0.1944 mm internal copper-to-NPTH clearance; a default 0.25 mm rule flags this component itself.

These are explicit global process assumptions, **not DRC exclusions**. Actual shorts, courtyard collisions, edge violations and unrouted items are still reported. There is no approved impedance stackup, copper weight, thermal-via fill/tenting process or fine-pitch assembly process. Confirm all of them before routing release/fabrication, including the RP2350 exposed-pad solder/thermal-via treatment.
