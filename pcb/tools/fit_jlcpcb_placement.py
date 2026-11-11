#!/usr/bin/env python3
"""Derive JLCPCB placement rotations and positions from JLCPCB's own footprints.

usage: fit_jlcpcb_placement.py BOARD.json PARTS.json OUT.json [--cache DIR]

KiCad and the JLCPCB parts library do not agree on what "rotation 0" means for a
package, so a placement file with KiCad angles puts some parts down turned.
Instead of a table of guessed corrections, this tool fetches the footprint that
JLCPCB itself uses for each LCSC part (the EasyEDA component API), and for every
placed part finds the rotation phi and position O for which that footprint's
pads land on the board's pads:

    top side:     board_pad = O + Rot(phi) * lib_pad
    bottom side:  board_pad = O + MirrorX * Rot(phi) * lib_pad

Rot is counter-clockwise as seen from the component side, which is how JLCPCB
defines the Rotation column (bottom parts as seen from the bottom, X mirrored).
The result per reference is written to OUT.json with the fit residual; a large
residual means the two footprints differ and the part must be checked by hand.
Needs network access.  export_order_package.py reads OUT.json and never fetches.
"""
from __future__ import annotations

import json
import math
import re
import sys
import time
import urllib.request
from pathlib import Path

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
HOSTS = ["easyeda.com", "lceda.cn"]      # the same component database
API = "https://{}/api/products/{}/components?version=6.4.19.5"
UNIT = 0.254      # EasyEDA canvas unit (10 mil) in mm


def fetch(lcsc: str, cache: Path) -> dict | None:
    f = cache / f"{lcsc}.json"
    if not f.exists():
        for host in HOSTS * 2:
            req = urllib.request.Request(API.format(host, lcsc), headers={"User-Agent": UA, "Accept": "application/json"})
            try:
                raw = urllib.request.urlopen(req, timeout=20).read()
                if json.loads(raw).get("success"):
                    f.write_bytes(raw)
                    time.sleep(1.5)       # both hosts throttle bursts
                    break
            except Exception:
                time.sleep(3)
        else:
            return None
    try:
        d = json.loads(f.read_text())
    except Exception:
        return None
    return d.get("result") if d.get("success") else None


def lib_pads(result: dict):
    ds = result["packageDetail"]["dataStr"]
    ox, oy = float(ds["head"]["x"]), float(ds["head"]["y"])
    pads = []
    for s in ds["shape"]:
        if not s.startswith("PAD~"):
            continue
        f = s.split("~")
        num = f[8]
        if not num:
            continue          # mechanical / unnumbered pad
        pads.append((num, (float(f[2]) - ox) * UNIT, (float(f[3]) - oy) * UNIT))
    return pads, result["packageDetail"].get("title", "")


def rot(p, phi):
    c, s = math.cos(math.radians(phi)), math.sin(math.radians(phi))
    x, y = p
    return (x * c + y * s, -x * s + y * c)        # counter-clockwise on a y-down canvas


def norm(n):
    return re.sub(r"[^0-9A-Za-z]", "", n).upper()


def fit(board, lib, bottom, prefer):
    """board, lib: [(num, x, y)].  Returns (phi, Ox, Oy, rms, matched_by)."""
    bnum = {}
    for n, x, y in board:
        bnum.setdefault(norm(n), []).append((x, y))
    lnum = {}
    for n, x, y in lib:
        lnum.setdefault(norm(n), []).append((x, y))
    common = [k for k in lnum if k in bnum and len(lnum[k]) == 1 and len(bnum[k]) == 1]
    by_number = len(common) >= max(2, 0.6 * len(lnum)) or (len(lnum) <= 2 and len(common) == len(lnum))
    best = None
    for phi in (0, 90, 180, 270):
        def place(p):
            q = rot(p, phi)
            return (-q[0], q[1]) if bottom else q
        if by_number:
            L = [place(lnum[k][0]) for k in common]
            B = [bnum[k][0] for k in common]
            ox = sum(b[0] - l[0] for b, l in zip(B, L)) / len(L)
            oy = sum(b[1] - l[1] for b, l in zip(B, L)) / len(L)
            err = math.sqrt(sum((b[0] - l[0] - ox) ** 2 + (b[1] - l[1] - oy) ** 2 for b, l in zip(B, L)) / len(L))
        else:
            L = [place((x, y)) for _, x, y in lib]
            B = [(x, y) for _, x, y in board]
            ox = sum(b[0] for b in B) / len(B) - sum(l[0] for l in L) / len(L)
            oy = sum(b[1] for b in B) / len(B) - sum(l[1] for l in L) / len(L)
            err = math.sqrt(sum(min((b[0] - l[0] - ox) ** 2 + (b[1] - l[1] - oy) ** 2 for b in B) for l in L) / len(L))
        cand = (round(err, 4), 0 if phi == prefer else 1, phi, ox, oy)
        if best is None or cand < best:
            best = cand
    return best[2], best[3], best[4], best[0], "pad number" if by_number else "geometry"


def main():
    board = json.loads(Path(sys.argv[1]).read_text())
    parts = json.loads(Path(sys.argv[2]).read_text())
    cache = Path(sys.argv[sys.argv.index("--cache") + 1]) if "--cache" in sys.argv else Path("build/jlc-footprints")
    cache.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(Path(__file__).parent))
    from export_order_package import match_rule

    out, by_part = {}, {}
    for fp in board["fps"]:
        rule = match_rule(fp, parts["rules"])
        if rule is None or not rule.get("assemble", True) or not rule.get("lcsc"):
            continue
        bottom = fp["layer"] == "B.Cu"
        layer = "B.Cu" if bottom else "F.Cu"
        pads = [(p["num"], p["x"], p["y"]) for p in fp["pads"] if p["num"] and layer in p["layers"] and p["drill"][0] == 0]
        if not pads:      # through-hole style connector pads
            pads = [(p["num"], p["x"], p["y"]) for p in fp["pads"] if p["num"]]
        # a footprint with a second land site: keep the site at the footprint origin
        near = [p for p in pads if math.hypot(p[1] - fp["x"], p[2] - fp["y"]) < 2.2]
        if fp["ref"].startswith("LED") and len(near) >= 4:
            pads = near
        res = fetch(rule["lcsc"], cache)
        kicad_rot = fp["rot"] % 360
        conv = (180 - kicad_rot) % 360 if bottom else kicad_rot
        if res is None or not res.get("packageDetail"):
            out[fp["ref"]] = {"lcsc": rule["lcsc"], "status": "no JLCPCB footprint available", "rotation": conv, "x": fp["x"], "y": fp["y"], "side": "Bottom" if bottom else "Top"}
            continue
        lib, title = lib_pads(res)
        phi, ox, oy, rms, how = fit(pads, lib, bottom, conv)
        out[fp["ref"]] = {"lcsc": rule["lcsc"], "jlc_footprint": title, "status": "fitted", "matched_by": how, "pads_board": len(pads), "pads_lib": len(lib),
                          "rotation": phi, "x": round(ox, 4), "y": round(oy, 4), "side": "Bottom" if bottom else "Top", "rms_mm": rms,
                          "kicad_rotation": kicad_rot, "kicad_convention_rotation": conv, "correction_deg": (phi - conv) % 360,
                          "origin_shift_mm": round(math.hypot(ox - fp["x"], oy - fp["y"]), 4)}
        key = (rule["lcsc"], rule.get("mpn", ""), title, fp["fpid"].split(":")[-1])
        by_part.setdefault(key, []).append(out[fp["ref"]])
    summary = []
    for (lcsc, mpn, title, fpname), rows in sorted(by_part.items()):
        summary.append({"lcsc": lcsc, "mpn": mpn, "jlc_footprint": title, "kicad_footprint": fpname, "count": len(rows),
                        "corrections_deg": sorted({r["correction_deg"] for r in rows}), "max_rms_mm": max(r["rms_mm"] for r in rows),
                        "max_origin_shift_mm": max(r["origin_shift_mm"] for r in rows), "matched_by": rows[0]["matched_by"],
                        "pads": f'{rows[0]["pads_board"]}/{rows[0]["pads_lib"]}'})
    Path(sys.argv[3]).write_text(json.dumps({"source": "EasyEDA component API (the footprints JLCPCB places from)", "board": sys.argv[1],
                                              "parts": summary, "placements": out}, indent=1) + "\n")
    for s in summary:
        flag = "  <-- CHECK" if s["max_rms_mm"] > 0.15 or len(s["corrections_deg"]) > 1 else ""
        print(f'{s["lcsc"]:>10} {s["mpn"][:22]:22} {s["kicad_footprint"][:38]:38} n={s["count"]:3} corr={s["corrections_deg"]} rms={s["max_rms_mm"]:.3f} shift={s["max_origin_shift_mm"]:.3f} {s["matched_by"]} {s["pads"]}{flag}')
    missing = [r for r, v in out.items() if v["status"] != "fitted"]
    print("no JLCPCB footprint:", missing)


if __name__ == "__main__":
    main()
