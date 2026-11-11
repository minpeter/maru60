#!/usr/bin/env python3
"""Rename a placed footprint and save a normalised copy into a project library.

usage: save_board_footprint_to_lib.py BOARD.kicad_pcb LIB.pretty LIBNICK [--all-same] REF=NewName [REF=NewName ...]

Used for the footprints that the order-candidate tools extend on the board
(extra land sites, changed pads) so that the board, the library and the
schematic footprint field stay in step (run with KiCad 9 pcbnew).
"""
import sys

import pcbnew


def main():
    board_path, lib, nick = sys.argv[1:4]
    b = pcbnew.LoadBoard(board_path)
    every = "--all-same" in sys.argv       # also rename every other footprint that has the same library id
    by_ref = {f.GetReference(): f for f in b.GetFootprints()}
    for spec in [a for a in sys.argv[4:] if not a.startswith("--")]:
        ref, name = spec.split("=")
        fp = by_ref[ref]
        old_id = fp.GetFPID().GetUniStringLibId()
        if every:
            for other in by_ref.values():
                if other.GetFPID().GetUniStringLibId() == old_id:
                    other.SetFPID(pcbnew.LIB_ID(nick, name))
        fp.SetFPID(pcbnew.LIB_ID(nick, name))
        c = pcbnew.Cast_to_FOOTPRINT(fp.Duplicate()) if hasattr(pcbnew, "Cast_to_FOOTPRINT") else fp.Duplicate()
        if c.IsFlipped():
            c.Flip(c.GetPosition(), pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
        c.SetOrientationDegrees(0)
        c.SetPosition(pcbnew.VECTOR2I(0, 0))
        for p in c.Pads():
            p.SetNetCode(0)
        c.SetReference("REF**")
        pcbnew.FootprintSave(lib, c)
        print(ref, "->", f"{nick}:{name}")
    pcbnew.SaveBoard(board_path, b)


if __name__ == "__main__":
    main()
