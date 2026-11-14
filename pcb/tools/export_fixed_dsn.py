#!/usr/bin/env python3
"""Export an incremental routing job while keeping existing copper fixed.

Run with KiCad 9. The source CAD is read only. Internal Edge.Cuts contours are
part of the native export and must be retained by downstream DSN processing.
"""
import argparse
import hashlib
from pathlib import Path
import pcbnew as p

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("board", type=Path)
ap.add_argument("output", type=Path)
a = ap.parse_args()
before = hashlib.sha256(a.board.read_bytes()).hexdigest()
b = p.LoadBoard(str(a.board))
outline = p.SHAPE_POLY_SET()
assert b.GetBoardPolygonOutlines(outline)
for t in b.GetTracks():
    t.SetLocked(True)
assert p.ExportSpecctraDSN(b, str(a.output))
assert hashlib.sha256(a.board.read_bytes()).hexdigest() == before
print("Exported fixed existing copper;", sum(outline.HoleCount(i) for i in range(outline.OutlineCount())), "internal contours")
