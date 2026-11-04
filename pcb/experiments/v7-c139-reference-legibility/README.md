# C139 reference legibility correction

Experimental working selection only. Open `candidate/pcb/maru60.kicad_pro`. PCB SHA-256: 2b5787cc27e7fea92dff2ad483185fccfab1d2d27bf07662395de26f7ab14d69. Prior 4765 is preserved unchanged.

Only C139's Reference field changes: its anchor moves from (179.97, 85.0) to (181.4, 81.8) mm and text grows from 0.75 to 0.80 mm. The 90-degree orientation, 0.10 mm stroke, visible mirrored B.Silkscreen and content remain. It is directly above its own component column in the inspected native view. No component pose, value, pad, conductor, drill, saved fill, rule, other field or companion file changes.

Fresh native DRC has 55 to 51 warnings: exactly four C139 records disappear and none appear. All 12 raw expansion-open records are identical; other hard DRC and explicit schematic parity are zero. ERC 0 and all material/reference/firmware evidence inherit only from identical electrical inputs, not a fresh electrical execution or simulation. Inventory remains 9,750 tracks, 919 vias, 383 footprints and 13,184.45545001526 mm summed track length.

Independent raw reversal recovers 4765 byte for byte; all 57 companions are exact. Separate normal cold refill is byte-identical. Actual raw closed nominal courtyard gap is 0.279524 mm and drawn-stroke envelope gap is 0.254524 mm, both exceeding 0.20 mm. The 0.284524 mm cached courtyard reading is distinct and is not substituted. Mask, other silk, source Fab and edge checks pass. These are 2D source proxies and inspected text ownership, not process or 3D assembly approval.

R159 and C136 remain unchanged. The bounded local screen found their nearby free pockets misleadingly associated with other components. No claim of exhaustive continuous infeasibility is made, and labels were not hidden or moved far away merely to clear warnings.

All prior power, startup/reset/brownout, pulse, fault-input, environmental, physical SI/ESD/EMC, assembly and hardware limits remain. LED qualification stays OFF. There is no electrical improvement claim, fabrication, flashing or push. The complete 95-entry warning history has 44 resolved and 51 remaining. Frozen trial records retain their earlier UNSELECTED phase; this record is the later bounded experimental adoption.
