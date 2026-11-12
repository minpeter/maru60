# Second pass: operation lists

Everything that changed the board between PCB `36700843` and the present one
is in this folder as an operation list. They were planned on the geometry of
`36700843` and applied in the order below; KiCad DRC, ERC and schematic parity
were the judge after each group.

| Order | File | What it does |
| --- | --- | --- |
| 1 | `usb-pair-ops.json` | USB pair laid again. Made by `plan_pair_tracks.py` from `usb-pair-spec.json`, which names the two centre lines found by `plan_pair_route.py` (`usb-pair-route-main.json`, `usb-pair-route-end.json`). |
| 2 | `via-ops.json` | The last six vias inside SMD pads, planned by hand. |
| 3 | `marks-ops.json` | Pin-1 marks of `LED30` and `U11`. |
| 4 | `resistors/R170` `R172` `R173` `R176` `R177` `R178` `R180` `R183` `R171` `R174` `R175` `R185` `R182` `R179` | Series resistors planned by `plan_series_resistor.py`, in this order (each plan was made on the board that already had the earlier ones). `R185` was turned by hand afterwards. |
| 5 | `resistors/R181` `R184`, `led54-alt-site.json`, `led54-dot-ops.json`, `resistors/R186` | Hand-planned resistors and the second site of `LED54` (`apply_led_alt_sites.py`). `R184` goes before the LED site: the site's DOUT pad takes the net of `LED54` pad 3. |
| 6 | `snubber-ops.json` | `R187` and `C144`. |
| 7 | `text-ops.json` | Reference texts. |
| 8 | `resistors/R188` | Hand-planned on the board with lists 1–7 applied (the all-hop screen of the LED simulation showed that `KEY_RGB_CHAIN_30` needed one too). |

After the board operations: `save_board_footprint_to_lib.py` writes the
library copies of `LED30`, `LED54` (`candidates`) and `U11` (`Maru60`), the
footprint fields of `LED54` and `U11` are changed in the schematic, and
`edit_schematic_added_parts.py` adds the symbols listed in
`schematic-parts.json`.

```sh
# geometry of the board the plans start from (commit 8632502)
tools/run_kicad9.sh python3 pcb/tools/dump_board_geometry.py <36700843 board> build/base.json

# 1. the pair: search, then tracks (prints the smallest distances it finds)
.venv/bin/python pcb/tools/plan_pair_route.py build/base.json main.json \
  --from F.Cu:22.82:10.847 --to B.Cu:113.4:71.4 --nets USB_DP_CONN,USB_DM_CONN --avoid 98.8:61.15:0.29
.venv/bin/python pcb/tools/plan_pair_route.py build/base.json end.json \
  --from F.Cu:116.4:73.6 --to B.Cu:119.75:82.1 --nets USB_DP_CONN,USB_DM_CONN --window 100:60:134:92
.venv/bin/python pcb/tools/plan_pair_tracks.py build/base.json usb-pair-spec.json ops.json

# any list
tools/run_kicad9.sh python3 pcb/tools/apply_layout_ops.py <board> <ops.json>

# a series resistor (REF, driving LED, net; optional MAX_MM and MIN_MM)
.venv/bin/python pcb/tools/plan_series_resistor.py <board.json> ops.json R179 LED44 KEY_RGB_CHAIN_56 24 8
```

The new tracks and vias carry fresh KiCad identifiers on every run, so the
board file of a rerun differs in its UUIDs and therefore in its hash; the
copper is the same.
