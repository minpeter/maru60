"""2-D electrostatic field solve for the outer-layer traces of the JLC04161H-7628 stack.

Finite-volume Laplace solve on a graded tensor grid (scipy sparse direct solve).
Cross-section, y up from the reference plane:

    y = 0                 inner GND plane (In1 under F.Cu, In2 over B.Cu)
    0 .. H                7628 prepreg, er = ER_PREPREG
    H .. H+T              outer copper, T = 35 um, width w
    solder mask           conformal, MASK um thick, er = ER_MASK, over laminate and copper
    above                 air, closed by a grounded box far away

For N conductors it returns the Maxwell capacitance matrix C (F/m), the same
with every dielectric replaced by air (C0), and from them
    L = mu0*eps0 * inv(C0)        (H/m, quasi-TEM, lossless)
Single line: Z0 = sqrt(L/C), er_eff = C/C0, delay = sqrt(L*C).
Pair: odd/even mode values from the 2x2 matrices.

The model is a computation, not a measurement. Its error against closed-form
microstrip results is printed by `python fieldsolve.py --selftest`.
"""
from __future__ import annotations

import json
import math
import sys

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

EPS0 = 8.8541878128e-12
MU0 = 4e-7 * math.pi
C_LIGHT = 299792458.0

H = 0.2104       # mm prepreg (board file stackup)
T = 0.035        # mm outer copper
ER_PREPREG = 4.4  # 7628 prepreg, value given in the analysis context
ER_MASK = 3.8    # assumption: JLCPCB quotes 3.8 for its solder mask
MASK = 0.020     # mm, assumption (mask over copper; 15-30 um typical)


def _graded(lo, hi, fine_regions, fine, coarse, growth=1.25):
    """1-D grid: `fine` spacing inside fine_regions (list of (a, b)), growing to `coarse` elsewhere."""
    pts = {lo, hi}
    for a, b in fine_regions:
        n = max(1, int(round((b - a) / fine)))
        for i in range(n + 1):
            pts.add(round(a + (b - a) * i / n, 9))
    pts = sorted(pts)
    out = [pts[0]]
    for a, b in zip(pts, pts[1:]):
        gap = b - a
        if gap <= fine * 1.5:
            out.append(b)
            continue
        # fill the gap with steps that grow away from both ends
        left, right, step = [a], [b], fine
        while right[-1] - left[-1] > 2.2 * step:
            left.append(left[-1] + step)
            right.append(right[-1] - step)
            step = min(step * growth, coarse)
        if right[-1] - left[-1] > 1.2 * step:
            left.append(0.5 * (left[-1] + right[-1]))
        out.extend(left[1:])
        out.extend(sorted(right))
    return np.array(sorted(set(round(v, 9) for v in out)))


def solve(conductors, *, h=H, t=T, er=ER_PREPREG, er_mask=ER_MASK, mask=MASK,
          fine=0.004, box_x=5.0, box_y=5.0):
    """conductors: list of (x_center_mm, width_mm). Returns dict with C, C0, L (per metre)."""
    xs_regions, edges = [], []
    for xc, w in conductors:
        edges += [xc - w / 2, xc + w / 2]
    xmin, xmax = min(edges) - box_x, max(edges) + box_x
    for e in edges:
        xs_regions.append((e - 0.06, e + 0.06))
    for xc, w in conductors:
        xs_regions.append((xc - w / 2, xc + w / 2))
    # merge
    xs_regions.sort()
    merged = [list(xs_regions[0])]
    for a, b in xs_regions[1:]:
        if a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    x = _graded(xmin, xmax, merged, fine, 0.25)
    ybreaks = sorted({0.0, h, h + t, h + mask, h + t + mask, h + t + mask + 0.06})
    y = _graded(0.0, h + t + box_y, [(a, b) for a, b in zip(ybreaks, ybreaks[1:]) if b - a > 1e-9], fine, 0.25)
    nx, ny = len(x), len(y)
    xc_cell = 0.5 * (x[:-1] + x[1:])
    yc_cell = 0.5 * (y[:-1] + y[1:])

    def eps_cells(with_dielectric):
        e = np.ones((nx - 1, ny - 1))
        if not with_dielectric:
            return e
        X, Y = np.meshgrid(xc_cell, yc_cell, indexing="ij")
        e[Y < h] = er
        if mask > 0:
            e[(Y >= h) & (Y < h + mask)] = er_mask                      # mask on laminate
            for xc, w in conductors:                                     # mask over and beside copper
                m = (np.abs(X - xc) < w / 2 + mask) & (Y >= h) & (Y < h + t + mask)
                e[m] = er_mask
        return e

    # conductor node mask
    cid = -np.ones((nx, ny), dtype=int)
    for k, (xc, w) in enumerate(conductors):
        ix = np.where((x >= xc - w / 2 - 1e-9) & (x <= xc + w / 2 + 1e-9))[0]
        iy = np.where((y >= h - 1e-7) & (y <= h + t + 1e-7))[0]
        cid[np.ix_(ix, iy)] = k
    fixed = np.zeros((nx, ny), dtype=bool)
    fixed[0, :] = fixed[-1, :] = fixed[:, 0] = fixed[:, -1] = True
    fixed |= cid >= 0

    dx, dy = np.diff(x), np.diff(y)
    idx = np.arange(nx * ny).reshape(nx, ny)

    def assemble(e):
        # edge conductances (finite volume): x-directed edge between (i,j)-(i+1,j)
        ep = np.pad(e, 1, mode="edge")  # (nx+1, ny+1), cell (i,j) at [i+1, j+1]
        dyp = np.pad(dy, 1, mode="constant")
        dxp = np.pad(dx, 1, mode="constant")
        # x edges: i in 0..nx-2, j in 0..ny-1 ; cells below (j-1) and above (j)
        gx = (ep[1:-1, 0:-1] * dyp[None, 0:-1] / 2 + ep[1:-1, 1:] * dyp[None, 1:] / 2) / dx[:, None]
        gy = (ep[0:-1, 1:-1] * dxp[0:-1, None] / 2 + ep[1:, 1:-1] * dxp[1:, None] / 2) / dy[None, :]
        rows, cols, vals = [], [], []
        a, b = idx[:-1, :].ravel(), idx[1:, :].ravel()
        g = gx.ravel()
        rows += [a, b, a, b]; cols += [b, a, a, b]; vals += [-g, -g, g, g]
        a, b = idx[:, :-1].ravel(), idx[:, 1:].ravel()
        g = gy.ravel()
        rows += [a, b, a, b]; cols += [b, a, a, b]; vals += [-g, -g, g, g]
        return sp.csr_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(nx * ny, nx * ny))

    def cap_matrix(with_dielectric):
        A = assemble(eps_cells(with_dielectric))
        free = ~fixed.ravel()
        Aff = A[free][:, free].tocsc()
        lu = spla.splu(Aff)
        n = len(conductors)
        C = np.zeros((n, n))
        for k in range(n):
            phi = np.zeros(nx * ny)
            phi[(cid == k).ravel()] = 1.0
            rhs = -(A[free][:, ~free] @ phi[~free])
            phi[free] = lu.solve(rhs)
            q = A @ phi
            for m in range(n):
                C[m, k] = q[(cid == m).ravel()].sum() * EPS0
        return 0.5 * (C + C.T)

    C = cap_matrix(True)
    C0 = cap_matrix(False)
    L = MU0 * EPS0 * np.linalg.inv(C0)
    return {"C": C, "C0": C0, "L": L, "grid": (nx, ny)}


def single(w, **kw):
    r = solve([(0.0, w)], **kw)
    C, C0, L = r["C"][0, 0], r["C0"][0, 0], r["L"][0, 0]
    return {"w_mm": w, "C_pF_per_mm": C * 1e9, "L_nH_per_mm": L * 1e6, "Z0_ohm": math.sqrt(L / C),
            "er_eff": C / C0, "delay_ps_per_mm": math.sqrt(L * C) * 1e9}


def pair(w, gap, **kw):
    """Symmetric edge-coupled pair. C matrix entries are Maxwell form (C12 negative)."""
    s = w + gap
    r = solve([(-s / 2, w), (s / 2, w)], **kw)
    C, C0, L = r["C"], r["C0"], r["L"]
    c_odd, c_even = C[0, 0] - C[0, 1], C[0, 0] + C[0, 1]
    c0_odd, c0_even = C0[0, 0] - C0[0, 1], C0[0, 0] + C0[0, 1]
    l_odd, l_even = L[0, 0] - L[0, 1], L[0, 0] + L[0, 1]
    z_odd, z_even = math.sqrt(l_odd / c_odd), math.sqrt(l_even / c_even)
    return {
        "w_mm": w, "gap_mm": gap,
        "Z_odd": z_odd, "Z_even": z_even, "Z_diff": 2 * z_odd, "Z_common": z_even / 2,
        "er_eff_odd": c_odd / c0_odd, "er_eff_even": c_even / c0_even,
        "delay_odd_ps_per_mm": math.sqrt(l_odd * c_odd) * 1e9,
        "delay_even_ps_per_mm": math.sqrt(l_even * c_even) * 1e9,
        "C11_pF_per_mm": C[0, 0] * 1e9, "Cm_pF_per_mm": -C[0, 1] * 1e9,
        "L11_nH_per_mm": L[0, 0] * 1e6, "Lm_nH_per_mm": L[0, 1] * 1e6,
        "kC": -C[0, 1] / C[0, 0], "kL": L[0, 1] / L[0, 0],
    }


def coupled(w_victim, w_aggr, gap, **kw):
    """Two different lines side by side: per-length self and mutual C and L."""
    x2 = w_victim / 2 + gap + w_aggr / 2
    r = solve([(0.0, w_victim), (x2, w_aggr)], **kw)
    C, L = r["C"], r["L"]
    return {"w_victim": w_victim, "w_aggr": w_aggr, "gap_mm": gap,
            "C11_pF_per_mm": C[0, 0] * 1e9, "C22_pF_per_mm": C[1, 1] * 1e9, "Cm_pF_per_mm": -C[0, 1] * 1e9,
            "L11_nH_per_mm": L[0, 0] * 1e6, "L22_nH_per_mm": L[1, 1] * 1e6, "Lm_nH_per_mm": L[0, 1] * 1e6,
            "kC": -C[0, 1] / math.sqrt(C[0, 0] * C[1, 1]), "kL": L[0, 1] / math.sqrt(L[0, 0] * L[1, 1])}


def hammerstad(w, h, er, t=0.0):
    """Hammerstad-Jensen microstrip (no mask) for the self test."""
    u = w / h
    if t > 0:
        du = (t / h) / math.pi * math.log(1 + 4 * math.e / ((t / h) * (1 / math.tanh(math.sqrt(6.517 * u))) ** 2))
        dur = 0.5 * (1 + 1 / math.cosh(math.sqrt(er - 1))) * du
        u1, ur = u + du, u + dur
    else:
        u1 = ur = u

    def z01(u):
        f = 6 + (2 * math.pi - 6) * math.exp(-((30.666 / u) ** 0.7528))
        return 376.73 / (2 * math.pi) * math.log(f / u + math.sqrt(1 + (2 / u) ** 2))

    def ee(u, er):
        a = 1 + math.log((u ** 4 + (u / 52) ** 2) / (u ** 4 + 0.432)) / 49 + math.log(1 + (u / 18.1) ** 3) / 18.7
        b = 0.564 * ((er - 0.9) / (er + 3)) ** 0.053
        return (er + 1) / 2 + (er - 1) / 2 * (1 + 10 / u) ** (-a * b)

    e = ee(ur, er) * (z01(u1) / z01(ur)) ** 2
    return z01(ur) / math.sqrt(ee(ur, er)), e


def selftest():
    out = []
    for w in (0.15, 0.2, 0.25, 0.4):
        fs = single(w, mask=0.0)
        z, e = hammerstad(w, H, ER_PREPREG, T)
        out.append({"w": w, "Z0_solver": round(fs["Z0_ohm"], 2), "Z0_hammerstad": round(z, 2),
                    "er_eff_solver": round(fs["er_eff"], 3), "er_eff_hammerstad": round(e, 3),
                    "Z0_error_pct": round(100 * (fs["Z0_ohm"] / z - 1), 2)})
    # grid convergence at 0.25 mm
    conv = [{"fine_mm": f, "Z0": round(single(0.25, mask=0.0, fine=f)["Z0_ohm"], 3)} for f in (0.008, 0.004, 0.0025)]
    return {"vs_hammerstad_no_mask": out, "grid_convergence_w0p25": conv}


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        print(json.dumps(selftest(), indent=1))
    else:
        for w in (0.15, 0.2, 0.25):
            print(json.dumps(single(w)))
        print(json.dumps(pair(0.25, 0.2)))
