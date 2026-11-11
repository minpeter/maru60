#!/usr/bin/env python3
"""USB 2.0 full-speed / high-speed signal-integrity model for the Maru60 D+/D- path.

This is a *simulation* study, not a compliance or measurement claim.  It extracts
the routed D+/D- geometry from the KiCad board, computes quasi-static microstrip
impedance with a 2-D finite-volume field solve, builds a lossy differential
transmission-line model (RLCG per unit length), and runs a PRBS-7 eye simulation
at the MCU end of the channel.

Outputs (all under qa/usb-si-sim/):
  usb-si-sim.json
  REPORT.md
  eye_hs.png
  eye_fs.png
  impedance_vs_length.png
  eye_vs_esd.png

Run with the repository virtualenv:
  .venv/bin/python pcb/tools/simulate_usb_si.py
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import time
from pathlib import Path

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve
from scipy.signal import fftconvolve

# ---------------------------------------------------------------------------
# Paths / matplotlib cache
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "pcb" / "experiments" / "resume-20261109-relocated-expansion-zero-opens"
BOARD = EXP / "pcb" / "maru60.kicad_pcb"
OUT = EXP / "qa" / "usb-si-sim"
OUT.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(OUT / ".mplconfig"))
(OUT / ".mplconfig").mkdir(parents=True, exist_ok=True)

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

# ---------------------------------------------------------------------------
# Physical constants
# ---------------------------------------------------------------------------
C0 = 2.99792458e8          # m/s
MU0 = 4.0 * math.pi * 1e-7  # H/m
EPS0 = 8.8541878128e-12     # F/m
RHO_CU = 1.72e-8            # ohm*m, annealed copper
TAN_D = 0.02                # board stackup loss tangent (from KiCad stackup)

# USB 2.0 numbers
UI_HS = 1.0 / 480e6         # 2.0833 ns
UI_FS = 1.0 / 12e6          # 83.333 ns
V_HS = 0.4                  # V, differential Thevenin source level (+/-)
V_FS = 1.4                  # V, differential Thevenin source level (+/-)
TR_HS = 150e-12             # s, 10-90% assumed PHY rise time
TR_FS = 4.0e-9              # s, 10-90% assumed PHY rise time
ZS_DIFF = 90.0              # ohm, host differential source impedance
ZL_DIFF = 90.0              # ohm, device differential termination
R_SERIES = 27.0             # ohm, R102/R103 each
C_ESD_PER_LINE = 0.7e-12    # F, TPD2EUSB30DRTR DRT typical (datasheet)
C_CONN_PER_LINE = 0.5e-12   # F, USB-C receptacle, assumed
C_PIN_PER_LINE = 3.0e-12    # F, RP2350 USB pin, assumed
VIA_LENGTH_MM = 1.55        # mm, F.Cu <-> B.Cu through-via barrel, assumed

# Stackup fallback (parsed from the board; these are the board values)
H_DIELECTRIC_MM = 0.2104
ER = 4.4
T_COPPER_MM = 0.035

# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def fnum(x, nd=6):
    """JSON-safe float."""
    return float(round(float(x), nd))


def mm(x):
    return float(x)


# ---------------------------------------------------------------------------
# Board extraction
# ---------------------------------------------------------------------------

def parse_stackup(text: str) -> dict:
    """Parse the KiCad stackup block into copper and dielectric layers."""
    m = re.search(r"\(stackup(.*?)\n\t\t\)", text, re.S)
    if not m:
        raise RuntimeError("stackup block not found")
    block = m.group(1)
    layers = []
    for lm in re.finditer(r'\(layer "([^"]+)"(.*?)\n\t\t\t\)', block, re.S):
        name, body = lm.group(1), lm.group(2)
        if name in ("F.SilkS", "F.Paste", "F.Mask", "B.Mask", "B.Paste", "B.SilkS"):
            continue
        rec = {"name": name}
        tm = re.search(r"\(type \"([^\"]+)\"\)", body)
        if tm:
            rec["type"] = tm.group(1)
        th = re.search(r"\(thickness ([0-9.]+)\)", body)
        if th:
            rec["thickness_mm"] = float(th.group(1))
        er = re.search(r"\(epsilon_r ([0-9.]+)\)", body)
        if er:
            rec["epsilon_r"] = float(er.group(1))
        td = re.search(r"\(loss_tangent ([0-9.]+)\)", body)
        if td:
            rec["loss_tangent"] = float(td.group(1))
        mat = re.search(r'\(material "([^"]+)"\)', body)
        if mat:
            rec["material"] = mat.group(1)
        layers.append(rec)
    copper = [l for l in layers if l.get("type") == "copper"]
    dielectric = [l for l in layers if l.get("type") in ("prepreg", "core")]
    total = sum(l.get("thickness_mm", 0.0) for l in layers)
    return {
        "layers": layers,
        "copper": copper,
        "dielectric": dielectric,
        "total_thickness_mm": total,
    }


def parse_footprints(text: str, refs: set[str]) -> dict:
    """Return reference -> {value, at, layer, pads} for the requested refs."""
    out = {}
    starts = [m.start() for m in re.finditer(r"\n\t\(footprint ", text)]
    starts.append(len(text))
    for i in range(len(starts) - 1):
        block = text[starts[i]:starts[i + 1]]
        rm = re.search(r'\(property "Reference" "([^"]+)"', block)
        if not rm or rm.group(1) not in refs:
            continue
        ref = rm.group(1)
        vm = re.search(r'\(property "Value" "([^"]*)"', block)
        am = re.search(r"\n\t\t\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)", block)
        lm = re.search(r"\n\t\t\(layer \"([^\"]+)\"\)", block)
        pads = []
        for pm in re.finditer(r'\(pad "([^"]*)" (\w+) (\w+)\n(.*?)\n\t\t\)', block, re.S):
            pad = pm.group(0)
            net = re.search(r'\(net (\d+) "([^"]+)"', pad)
            pat = re.search(r"\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)", pad)
            size = re.search(r"\(size ([-\d.]+) ([-\d.]+)\)", pad)
            layers = re.search(r"\(layers ([^)]*)\)", pad)
            pads.append({
                "name": pm.group(1),
                "type": pm.group(2),
                "shape": pm.group(3),
                "at": [float(pat.group(1)), float(pat.group(2))] if pat else None,
                "size": [float(size.group(1)), float(size.group(2))] if size else None,
                "net": [int(net.group(1)), net.group(2)] if net else None,
                "layers": layers.group(1) if layers else None,
            })
        out[ref] = {
            "value": vm.group(1) if vm else None,
            "at": [float(am.group(1)), float(am.group(2))] if am else None,
            "layer": lm.group(1) if lm else None,
            "pads": pads,
        }
    return out


def parse_tracks(text: str, net_ids: dict[int, str]) -> dict:
    """Extract segments and vias for the requested nets."""
    nets = {nid: {"name": name, "segments": [], "vias": []} for nid, name in net_ids.items()}
    for m in re.finditer(r"\n\t\(segment\n(.*?)\n\t\)", text, re.S):
        b = m.group(1)
        nm = re.search(r"\(net (\d+)\)", b)
        if not nm or int(nm.group(1)) not in nets:
            continue
        st = re.search(r"\(start ([-\d.]+) ([-\d.]+)\)", b)
        en = re.search(r"\(end ([-\d.]+) ([-\d.]+)\)", b)
        w = re.search(r"\(width ([-\d.]+)\)", b)
        l = re.search(r'\(layer "([^"]+)"\)', b)
        if not (st and en and w and l):
            continue
        x1, y1 = float(st.group(1)), float(st.group(2))
        x2, y2 = float(en.group(1)), float(en.group(2))
        length = math.hypot(x2 - x1, y2 - y1)
        nets[int(nm.group(1))]["segments"].append({
            "start": [x1, y1], "end": [x2, y2],
            "width_mm": float(w.group(1)), "layer": l.group(1),
            "length_mm": length,
        })
    for m in re.finditer(r"\n\t\(via\n(.*?)\n\t\)", text, re.S):
        b = m.group(1)
        nm = re.search(r"\(net (\d+)\)", b)
        if not nm or int(nm.group(1)) not in nets:
            continue
        at = re.search(r"\(at ([-\d.]+) ([-\d.]+)\)", b)
        size = re.search(r"\(size ([-\d.]+)\)", b)
        drill = re.search(r"\(drill ([-\d.]+)\)", b)
        nets[int(nm.group(1))]["vias"].append({
            "at": [float(at.group(1)), float(at.group(2))] if at else None,
            "size_mm": float(size.group(1)) if size else None,
            "drill_mm": float(drill.group(1)) if drill else None,
        })
    return nets


def summarize_nets(nets: dict) -> dict:
    """Length / width / layer / via summary per net."""
    out = {}
    for nid, rec in nets.items():
        segs = rec["segments"]
        total = sum(s["length_mm"] for s in segs)
        by_width = {}
        by_layer = {}
        for s in segs:
            by_width[s["width_mm"]] = by_width.get(s["width_mm"], 0.0) + s["length_mm"]
            by_layer[s["layer"]] = by_layer.get(s["layer"], 0.0) + s["length_mm"]
        via_count = len(rec["vias"])
        via_len = via_count * VIA_LENGTH_MM
        out[rec["name"]] = {
            "net_id": nid,
            "track_length_mm": fnum(total, 3),
            "via_count": via_count,
            "via_length_mm": fnum(via_len, 3),
            "total_length_mm": fnum(total + via_len, 3),
            "width_mm": {str(k): fnum(v, 3) for k, v in sorted(by_width.items())},
            "layer_mm": {k: fnum(v, 3) for k, v in sorted(by_layer.items())},
            "segments": len(segs),
        }
    return out


# ---------------------------------------------------------------------------
# 2-D finite-volume quasi-static impedance
# ---------------------------------------------------------------------------

def fdm_impedance(w_mm: float, s_mm: float | None, h_mm: float = H_DIELECTRIC_MM,
                  t_mm: float = T_COPPER_MM, er: float = ER,
                  dx_mm: float = 0.005, xmax_mm: float = 2.5,
                  ymax_mm: float = 2.5) -> dict:
    """Solve Laplace for a microstrip cross-section.

    Returns C (F/m), C_air (F/m), Z0 (single-ended) or Zdiff (differential),
    and the effective permittivity.  The conductor is a rectangular bar of
    thickness t sitting on the dielectric interface; the ground is at y=0.
    """
    Nx = int(round(2 * xmax_mm / dx_mm)) + 1
    Ny = int(round(ymax_mm / dx_mm)) + 1
    xs = -xmax_mm + np.arange(Nx) * dx_mm
    ys = np.arange(Ny) * dx_mm
    eps_x = np.where(ys < h_mm, er, 1.0)
    eps_y = np.where((ys[:-1] + ys[1:]) / 2.0 < h_mm, er, 1.0)

    fixed = np.zeros((Ny, Nx), dtype=bool)
    phi = np.zeros((Ny, Nx))
    fixed[0, :] = True  # ground plane

    def mask(xc):
        mx = (xs >= xc - w_mm / 2 - 1e-9) & (xs <= xc + w_mm / 2 + 1e-9)
        my = (ys >= h_mm - 1e-9) & (ys <= h_mm + t_mm + 1e-9)
        return mx, my

    if s_mm is None:
        mx, my = mask(0.0)
        fixed[np.ix_(my, mx)] = True
        phi[np.ix_(my, mx)] = 1.0
    else:
        xc = s_mm / 2.0 + w_mm / 2.0
        for sign in (+1, -1):
            mx, my = mask(sign * xc)
            fixed[np.ix_(my, mx)] = True
            phi[np.ix_(my, mx)] = sign * 1.0

    plus_idx = np.where(fixed.ravel() & (phi.ravel() > 0))[0]
    N = Nx * Ny

    diag = np.zeros((Ny, Nx))
    diag += 2.0 * eps_x[:, None]
    diag[:, 0] -= eps_x
    diag[:, -1] -= eps_x
    diag[:-1, :] += eps_y[:, None]
    diag[1:, :] += eps_y[:, None]

    xp = np.zeros((Ny, Nx)); xp[:, :-1] = -eps_x[:, None]
    xm = np.zeros((Ny, Nx)); xm[:, 1:] = -eps_x[:, None]
    yp = np.zeros((Ny, Nx)); yp[:-1, :] = -eps_y[:, None]
    ym = np.zeros((Ny, Nx)); ym[1:, :] = -eps_y[:, None]

    A = sparse.diags(
        [diag.ravel(), xp.ravel()[:-1], xm.ravel()[1:], yp.ravel()[:-Nx], ym.ravel()[Nx:]],
        [0, 1, -1, Nx, -Nx], shape=(N, N), format="csr",
    )
    A_lap = A.copy()

    fixed_flat = fixed.ravel()
    fixed_idx = np.where(fixed_flat)[0]
    coo = A.tocoo()
    keep = ~fixed_flat[coo.row]
    rows = np.concatenate([coo.row[keep], fixed_idx])
    cols = np.concatenate([coo.col[keep], fixed_idx])
    vals = np.concatenate([coo.data[keep], np.ones(len(fixed_idx))])
    A = sparse.coo_matrix((vals, (rows, cols)), shape=(N, N)).tocsr()

    b = np.zeros(N)
    b[fixed_idx] = phi.ravel()[fixed_idx]
    v = spsolve(A, b)
    Q = float((A_lap @ v)[plus_idx].sum() * EPS0)  # F/m

    if s_mm is None:
        z0 = 1.0 / (C0 * math.sqrt(Q * Q)) if Q > 0 else float("nan")
        # Q is C for V=1; the air solve is done by the caller
        return {"C": Q, "Z0": z0, "ereff": None}
    z0odd = 1.0 / (C0 * math.sqrt(Q * Q)) if Q > 0 else float("nan")
    return {"Codd": Q, "Z0odd": z0odd, "Zdiff": 2.0 * z0odd, "ereff": None}


def impedance_case(w_mm: float, s_mm: float | None, dx_mm: float = 0.005) -> dict:
    """Run the dielectric and air solves and return impedance + ereff."""
    d = fdm_impedance(w_mm, s_mm, er=ER, dx_mm=dx_mm)
    a = fdm_impedance(w_mm, s_mm, er=1.0, dx_mm=dx_mm)
    if s_mm is None:
        C, Cair = d["C"], a["C"]
        z0 = 1.0 / (C0 * math.sqrt(C * Cair))
        return {
            "w_mm": w_mm,
            "C_pf_per_m": C * 1e12, "C_air_pf_per_m": Cair * 1e12,
            "Z0_ohm": z0,
            "ereff": C / Cair,
        }
    C, Cair = d["Codd"], a["Codd"]
    z0odd = 1.0 / (C0 * math.sqrt(C * Cair))
    return {
        "w_mm": w_mm, "s_mm": s_mm,
        "Codd_pf_per_m": C * 1e12, "C_air_odd_pf_per_m": Cair * 1e12,
        "Z0_odd_ohm": z0odd, "Zdiff_ohm": 2.0 * z0odd,
        "ereff": C / Cair,
    }


# ---------------------------------------------------------------------------
# Closed-form cross-check (Hammerstad / IPC-2141 style)
# ---------------------------------------------------------------------------

def z0_microstrip_closed(w_mm: float, h_mm: float = H_DIELECTRIC_MM,
                         t_mm: float = T_COPPER_MM, er: float = ER) -> float:
    """IPC-2141 style single-ended microstrip estimate (cross-check only)."""
    return 87.0 / math.sqrt(er + 1.41) * math.log(5.98 * h_mm / (0.8 * w_mm + t_mm))


def zdiff_closed(w_mm: float, s_mm: float, h_mm: float = H_DIELECTRIC_MM,
                 t_mm: float = T_COPPER_MM, er: float = ER) -> float:
    """Rough edge-coupled estimate: 2*Z0*(1-k), k from s/h."""
    z0 = z0_microstrip_closed(w_mm, h_mm, t_mm, er)
    k = 0.48 * math.exp(-0.96 * s_mm / h_mm)
    return 2.0 * z0 * (1.0 - k)


# ---------------------------------------------------------------------------
# RLCG and channel
# ---------------------------------------------------------------------------

def rlcg(f_hz: np.ndarray, length_m: float, zdiff: float, ereff: float,
         w_mm: float, tan_d: float = TAN_D) -> dict:
    """Frequency-dependent differential RLCG for a uniform line."""
    f = np.asarray(f_hz, dtype=float)
    omega = 2.0 * math.pi * f
    sqrt_ereff = math.sqrt(ereff)
    L = zdiff * sqrt_ereff / C0          # H/m
    C = sqrt_ereff / (zdiff * C0)        # F/m
    w_m = w_mm * 1e-3
    t_m = T_COPPER_MM * 1e-3
    R_dc = 2.0 * RHO_CU / (w_m * t_m)    # ohm/m, two conductors in series
    # skin-effect surface resistance; 1.5 accounts for sidewalls/roughness
    R_skin = 2.0 * 1.5 * np.sqrt(np.pi * np.maximum(f, 1.0) * MU0 * RHO_CU) / w_m
    R = R_dc + R_skin
    G = omega * C * tan_d
    return {"R": R, "L": L, "C": C, "G": G, "R_dc": R_dc, "L_per_m": L, "C_per_m": C}


def tl_abcd(f: np.ndarray, length_m: float, zdiff: float, ereff: float,
            w_mm: float) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """ABCD of a lossy differential TL at each frequency."""
    f = np.asarray(f, dtype=float)
    omega = 2.0 * math.pi * f
    p = rlcg(f, length_m, zdiff, ereff, w_mm)
    R, L, C, G = p["R"], p["L"], p["C"], p["G"]
    A = np.ones_like(f, dtype=complex)
    B = np.zeros_like(A)
    Cc = np.zeros_like(A)
    D = np.ones_like(A)
    nz = f > 0
    if np.any(nz):
        gamma = np.sqrt((R[nz] + 1j * omega[nz] * L) * (G[nz] + 1j * omega[nz] * C))
        zc = np.sqrt((R[nz] + 1j * omega[nz] * L) / (G[nz] + 1j * omega[nz] * C))
        gl = gamma * length_m
        A[nz] = np.cosh(gl)
        B[nz] = zc * np.sinh(gl)
        Cc[nz] = np.sinh(gl) / zc
        D[nz] = np.cosh(gl)
    # f=0: gamma=0, zc=inf -> use the series-R limit
    A[~nz] = 1.0
    B[~nz] = p["R_dc"] * length_m
    Cc[~nz] = 0.0
    D[~nz] = 1.0
    return A, B, Cc, D


def cascade(abcd_list: list[tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]]):
    """Multiply ABCD matrices in order (source -> load)."""
    A = np.ones_like(abcd_list[0][0], dtype=complex)
    B = np.zeros_like(A)
    C = np.zeros_like(A)
    D = np.ones_like(A)
    for a, b, c, d in abcd_list:
        A, B, C, D = A * a + B * c, A * b + B * d, C * a + D * c, C * b + D * d
    return A, B, C, D


def shunt_c(f: np.ndarray, c_f: float):
    omega = 2.0 * math.pi * np.asarray(f, dtype=float)
    one = np.ones_like(omega, dtype=complex)
    zero = np.zeros_like(omega, dtype=complex)
    return one, zero, 1j * omega * c_f, one


def series_r(f: np.ndarray, r_ohm: float):
    one = np.ones_like(np.asarray(f, dtype=float), dtype=complex)
    zero = np.zeros_like(one)
    return one, r_ohm * one, zero, one


def channel_response(f: np.ndarray, length_mm: float, zdiff: float, ereff: float,
                     w_mm: float, c_esd_per_line: float = C_ESD_PER_LINE,
                     c_conn_per_line: float = C_CONN_PER_LINE,
                     c_pin_per_line: float = C_PIN_PER_LINE,
                     r_series: float = R_SERIES,
                     zs: float = ZS_DIFF, zl: float = ZL_DIFF,
                     short_length_mm: float = 3.98,
                     short_zdiff: float = 150.4,
                     short_ereff: float = 2.40,
                     short_w_mm: float = 0.15) -> dict:
    """Differential channel from the host Thevenin source to the MCU pin.

    Topology (connector -> MCU):
      host Zs -> shunt (connector + ESD) -> long TL -> 27R series -> short TL
      -> (MCU pin C || 45R termination)
    """
    f = np.asarray(f, dtype=float)
    c_shunt = (c_conn_per_line + c_esd_per_line) / 2.0  # differential shunt
    c_pin = c_pin_per_line / 2.0
    omega = 2.0 * math.pi * f
    zl_total = 1.0 / (1.0 / zl + 1j * omega * c_pin)

    blocks = [
        shunt_c(f, c_shunt),
        tl_abcd(f, length_mm * 1e-3, zdiff, ereff, w_mm),
        series_r(f, 2.0 * r_series),
        tl_abcd(f, short_length_mm * 1e-3, short_zdiff, short_ereff, short_w_mm),
    ]
    A, B, C, D = cascade(blocks)
    H = zl_total / (A * zl_total + B + zs * (C * zl_total + D))
    # input impedance / S11 at the source
    zin = (A * zl_total + B) / (C * zl_total + D)
    s11 = (zin - zs) / (zin + zs)
    return {"H": H, "S11": s11, "Zin": zin, "c_shunt": c_shunt, "c_pin": c_pin}


# ---------------------------------------------------------------------------
# PRBS / eye simulation
# ---------------------------------------------------------------------------

def prbs7(n_bits: int) -> np.ndarray:
    """Maximal-length PRBS-7 (x^7 + x^6 + 1), 127-bit period."""
    state = 0x7F
    bits = []
    for _ in range(n_bits):
        bits.append((state >> 6) & 1)
        fb = ((state >> 6) ^ (state >> 5)) & 1
        state = ((state << 1) | fb) & 0x7F
    return np.array(bits, dtype=float)


def gaussian_step(x: np.ndarray, sigma_samples: float) -> np.ndarray:
    """Gaussian low-pass (step response is erf); 10-90% = 2.563 sigma."""
    if sigma_samples <= 0:
        return x
    n = max(3, int(math.ceil(4.0 * sigma_samples)))
    k = np.arange(-n, n + 1)
    g = np.exp(-0.5 * (k / sigma_samples) ** 2)
    g /= g.sum()
    return np.convolve(x, g, mode="same")


def simulate_eye(length_mm: float, ui: float, v_level: float, tr: float,
                 zdiff: float, ereff: float, w_mm: float,
                 c_esd_per_line: float = C_ESD_PER_LINE,
                 n_bits: int = 2000, samples_per_ui: int = 80,
                 short_length_mm: float = 3.98,
                 short_zdiff: float = 150.4,
                 short_ereff: float = 2.40,
                 short_w_mm: float = 0.15,
                 skew_ps: float = 0.0) -> dict:
    """Run the PRBS-7 eye simulation and return metrics + waveforms."""
    dt = ui / samples_per_ui
    n_samples = n_bits * samples_per_ui
    bits = prbs7(n_bits)
    ideal = np.repeat((2.0 * bits - 1.0) * v_level, samples_per_ui)
    sigma = tr / 2.563 / dt
    vin = gaussian_step(ideal, sigma)

    # frequency grid for the channel / impulse response
    nfft = 1 << 16
    f = np.fft.rfftfreq(nfft, d=dt)
    ch = channel_response(f, length_mm, zdiff, ereff, w_mm,
                          c_esd_per_line=c_esd_per_line,
                          short_length_mm=short_length_mm,
                          short_zdiff=short_zdiff,
                          short_ereff=short_ereff,
                          short_w_mm=short_w_mm)
    h = np.fft.irfft(ch["H"], n=nfft)
    n_taps = min(4000, nfft // 2)
    h = h[:n_taps]
    # Keep the output aligned with the input bits.  The channel delay is
    # absorbed by the eye phase scan; the first few bits are a startup
    # transient and are discarded.
    y = fftconvolve(vin, h, mode="full")[:len(vin)]
    n_skip = 20
    y = y[n_skip * samples_per_ui:]
    bits = bits[n_skip:]

    # optional differential skew: shift the inverted line by skew_ps
    if abs(skew_ps) > 1e-9:
        shift = skew_ps * 1e-12 / dt
        n = len(y)
        Y = np.fft.rfft(y)
        fshift = np.fft.rfftfreq(n, d=dt)
        Ys = Y * np.exp(-2j * math.pi * fshift * shift * dt)
        y_shift = np.fft.irfft(Ys, n=n)
        y = 0.5 * (y + y_shift)
    else:
        y_shift = y

    # eye scan: find the phase with the largest vertical opening
    n_use = (len(y) // samples_per_ui) - 1
    y = y[:n_use * samples_per_ui]
    best = None
    for phase in range(samples_per_ui):
        idx = np.arange(n_use) * samples_per_ui + phase
        vals = y[idx]
        b = bits[:n_use]
        hi = vals[b > 0.5]
        lo = vals[b < 0.5]
        if len(hi) == 0 or len(lo) == 0:
            continue
        eh = float(np.min(hi) - np.max(lo))
        if best is None or eh > best["eye_height"]:
            best = {"phase": phase, "eye_height": eh,
                    "high_mean": float(np.mean(hi)), "low_mean": float(np.mean(lo)),
                    "high_min": float(np.min(hi)), "low_max": float(np.max(lo))}
    if best is None:
        raise RuntimeError("eye scan failed")

    # eye width at the 0 V threshold, using the same all-traces criterion
    width_phases = 0
    for phase in range(samples_per_ui):
        idx = np.arange(n_use) * samples_per_ui + phase
        vals = y[idx]
        b = bits[:n_use]
        hi = vals[b > 0.5]
        lo = vals[b < 0.5]
        if len(hi) and len(lo) and np.min(hi) > 0.0 and np.max(lo) < 0.0:
            width_phases += 1
    eye_width_ui = width_phases / samples_per_ui
    eye_width_ps = eye_width_ui * ui * 1e12

    # overshoot / undershoot relative to the steady-state swing
    swing = best["high_mean"] - best["low_mean"]
    overshoot = (float(np.max(y)) - best["high_mean"]) / swing * 100.0 if swing > 0 else float("nan")
    undershoot = (best["low_mean"] - float(np.min(y))) / swing * 100.0 if swing > 0 else float("nan")

    # reflection
    s11 = np.abs(ch["S11"])
    f_ghz = f / 1e9
    band = (f_ghz >= 0.01) & (f_ghz <= 2.0)
    if np.any(band):
        iworst = np.argmax(s11[band])
        s11_worst = float(s11[band][iworst])
        f_worst = float(f_ghz[band][iworst])
    else:
        s11_worst, f_worst = float("nan"), float("nan")

    def s11_at(f_target_hz):
        idx = int(np.argmin(np.abs(f - f_target_hz)))
        return float(s11[idx])

    s11_240m = s11_at(240e6)
    s11_720m = s11_at(720e6)

    # eye traces for plotting (2 UI window around the best phase)
    phase = best["phase"]
    traces = []
    for k in range(1, n_use - 1):
        start = k * samples_per_ui + phase - samples_per_ui
        end = start + 2 * samples_per_ui
        if start < 0 or end > len(y):
            continue
        traces.append(y[start:end])
    traces = np.array(traces)

    return {
        "eye_height_mv": best["eye_height"] * 1e3,
        "eye_width_ui": eye_width_ui,
        "eye_width_ps": eye_width_ps,
        "high_mean_mv": best["high_mean"] * 1e3,
        "low_mean_mv": best["low_mean"] * 1e3,
        "high_min_mv": best["high_min"] * 1e3,
        "low_max_mv": best["low_max"] * 1e3,
        "overshoot_pct": overshoot,
        "undershoot_pct": undershoot,
        "s11_worst": s11_worst,
        "s11_worst_ghz": f_worst,
        "s11_240mhz": s11_240m,
        "s11_720mhz": s11_720m,
        "return_loss_db": -20.0 * math.log10(s11_worst) if s11_worst > 0 else float("inf"),
        "phase": phase,
        "samples_per_ui": samples_per_ui,
        "dt_ps": dt * 1e12,
        "traces": traces,
        "y": y,
        "bits": bits[:n_use],
        "ui": ui,
        "v_level": v_level,
        "tr": tr,
        "length_mm": length_mm,
        "zdiff": zdiff,
        "ereff": ereff,
        "c_esd_per_line": c_esd_per_line,
        "skew_ps": skew_ps,
    }


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------

def plot_eye(res: dict, path: Path, title: str, color="#1f77b4", mask: bool = False):
    traces = res["traces"]
    spb = res["samples_per_ui"]
    t_ns = (np.arange(traces.shape[1]) - spb) * res["dt_ps"] / 1000.0
    fig, ax = plt.subplots(figsize=(8.0, 4.8))
    for tr in traces[:: max(1, len(traces) // 120)]:
        ax.plot(t_ns, tr * 1e3, color="0.75", lw=0.5, alpha=0.5)
    centre = traces[:, spb]
    hi = traces[centre > 0.0]
    lo = traces[centre <= 0.0]
    if len(hi):
        ax.plot(t_ns, np.mean(hi, axis=0) * 1e3, color=color, lw=1.8, label="high mean")
    if len(lo):
        ax.plot(t_ns, np.mean(lo, axis=0) * 1e3, color="#2ca02c", lw=1.8, label="low mean")
    ax.axhline(0.0, color="0.3", lw=0.8, ls="--")
    ax.axvline(0.0, color="0.3", lw=0.8, ls=":")
    if mask:
        ui_ns = res["ui"] * 1e9
        from matplotlib.patches import Rectangle
        ax.add_patch(Rectangle((-0.2 * ui_ns, -150.0), 0.4 * ui_ns, 300.0,
                               fill=False, ec="#d62728", ls="--", lw=1.2,
                               label="0.3 V / 0.4 UI template (informational only)"))
    ax.set_xlabel("time relative to eye centre (ns)")
    ax.set_ylabel("differential voltage at MCU (mV)")
    ax.set_title(title)
    ax.grid(True, alpha=0.25)
    ax.legend(loc="upper right", fontsize=7)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def plot_impedance_vs_length(width_sweep: list[dict], length_sweep: list[dict],
                             actual_length: float, closure_length: float | None,
                             width_closure_length: float | None, path: Path):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.0, 4.8))

    cf = [d for d in width_sweep if d.get("source") == "closed-form-calibrated"]
    fdm = [d for d in width_sweep if d.get("source") == "fdm"]
    ax1.plot([d["w_mm"] for d in cf], [d["Zdiff_ohm"] for d in cf], "-",
             color="#1f77b4", lw=1.4,
             label="Zdiff, calibrated closed-form (s=0.25 mm)")
    ax1.plot([d["w_mm"] for d in fdm], [d["Zdiff_ohm"] for d in fdm], "o",
             color="#1f77b4", ms=6, label="Zdiff, 2-D FDM")
    ax1.axhline(90.0, color="#d62728", ls="--", lw=1.2, label="90 ohm target")
    for w, lab in [(0.15, "0.15 mm"), (0.25, "0.25 mm")]:
        for d in fdm:
            if abs(d["w_mm"] - w) < 1e-6:
                ax1.annotate(f"{lab}\n{d['Zdiff_ohm']:.0f} ohm", (w, d["Zdiff_ohm"]),
                             textcoords="offset points", xytext=(6, 8),
                             fontsize=8, color="#ff7f0e")
    ax1.set_xlabel("trace width (mm), edge-to-edge gap 0.25 mm")
    ax1.set_ylabel("differential impedance (ohm)")
    ax1.set_title("(a) Zdiff vs width, 0.21 mm prepreg, er 4.4")
    ax1.grid(True, alpha=0.25)
    ax1.legend(fontsize=7)

    ls = [d["length_mm"] for d in length_sweep]
    eh = [d["eye_height_mv"] for d in length_sweep]
    ew = [d["eye_width_ui"] for d in length_sweep]
    ax2.plot(ls, eh, "o-", color="#2ca02c", ms=3, lw=1.4, label="eye height (mV)")
    ax2.axhline(0.0, color="0.3", lw=0.8, ls="--")
    ax2.axvline(actual_length, color="#d62728", ls=":", lw=1.2,
                label=f"actual {actual_length:.0f} mm")
    if width_closure_length is not None:
        ax2.axvline(width_closure_length, color="#ff7f0e", ls="--", lw=1.0,
                    label=f"0.4 UI width {width_closure_length:.0f} mm")
    if closure_length is not None:
        ax2.axvline(closure_length, color="#9467bd", ls="-.", lw=1.2,
                    label=f"zero height {closure_length:.0f} mm")
    ax2.set_xlabel("long-line length (mm)")
    ax2.set_ylabel("eye height (mV)", color="#2ca02c")
    ax2.tick_params(axis="y", labelcolor="#2ca02c")
    ax2.grid(True, alpha=0.25)
    ax2b = ax2.twinx()
    ax2b.plot(ls, ew, "s--", color="#ff7f0e", ms=3, lw=1.2, label="eye width (UI)")
    ax2b.set_ylabel("eye width (UI)", color="#ff7f0e")
    ax2b.tick_params(axis="y", labelcolor="#ff7f0e")
    lines1, labels1 = ax2.get_legend_handles_labels()
    lines2, labels2 = ax2b.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, fontsize=7, loc="lower left")
    ax2.set_title("(b) HS eye vs long-line length (ESD 0.7 pF)")

    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def plot_eye_vs_esd(esd_sweep: list[dict], actual_c: float, path: Path):
    cs = [d["c_esd_per_line_pf"] for d in esd_sweep]
    eh = [d["eye_height_mv"] for d in esd_sweep]
    ew = [d["eye_width_ui"] for d in esd_sweep]
    fig, ax = plt.subplots(figsize=(8.0, 4.8))
    ax.plot(cs, eh, "o-", color="#2ca02c", ms=3, lw=1.4, label="eye height (mV)")
    ax.axhline(0.0, color="0.3", lw=0.8, ls="--")
    ax.axvline(actual_c, color="#d62728", ls=":", lw=1.2,
               label=f"TPD2EUSB30 typical {actual_c:.1f} pF")
    ax.set_xlabel("ESD capacitance per line (pF)")
    ax.set_ylabel("eye height (mV)", color="#2ca02c")
    ax.tick_params(axis="y", labelcolor="#2ca02c")
    ax.grid(True, alpha=0.25)
    axb = ax.twinx()
    axb.plot(cs, ew, "s--", color="#ff7f0e", ms=3, lw=1.2, label="eye width (UI)")
    axb.set_ylabel("eye width (UI)", color="#ff7f0e")
    axb.tick_params(axis="y", labelcolor="#ff7f0e")
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = axb.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, fontsize=8, loc="lower left")
    ax.set_title("HS eye vs ESD capacitance at the connector end")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fast", action="store_true",
                        help="skip the extra FDM width sweep (use the calibrated closed-form curve)")
    args = parser.parse_args()
    t_start = time.time()
    print(f"board: {BOARD}")
    if not BOARD.exists():
        print("ERROR: board not found", file=sys.stderr)
        return 2
    text = BOARD.read_text(errors="replace")

    # --- stackup ---------------------------------------------------------
    stack = parse_stackup(text)
    print(f"stackup: {len(stack['copper'])} copper, {len(stack['dielectric'])} dielectric, "
          f"total {stack['total_thickness_mm']:.3f} mm")

    # --- footprints ------------------------------------------------------
    refs = {"J1", "R102", "R103", "U10", "U1"}
    fps = parse_footprints(text, refs)
    for r in sorted(fps):
        print(f"  {r}: {fps[r]['value']} at {fps[r]['at']} on {fps[r]['layer']}")

    # --- tracks ----------------------------------------------------------
    net_ids = {109: "USB_DM", 110: "USB_DP", 119: "USB_DP_CONN", 120: "USB_DM_CONN"}
    nets = parse_tracks(text, net_ids)
    net_summary = summarize_nets(nets)
    for name, rec in net_summary.items():
        print(f"  {name}: {rec['total_length_mm']:.2f} mm, "
              f"{rec['via_count']} vias, widths {rec['width_mm']}")

    dp_total = net_summary["USB_DP_CONN"]["total_length_mm"] + net_summary["USB_DP"]["total_length_mm"]
    dm_total = net_summary["USB_DM_CONN"]["total_length_mm"] + net_summary["USB_DM"]["total_length_mm"]
    skew_mm = abs(dp_total - dm_total)
    long_dp = net_summary["USB_DP_CONN"]["total_length_mm"]
    long_dm = net_summary["USB_DM_CONN"]["total_length_mm"]
    short_dp = net_summary["USB_DP"]["total_length_mm"]
    short_dm = net_summary["USB_DM"]["total_length_mm"]
    long_avg = 0.5 * (long_dp + long_dm)
    short_avg = 0.5 * (short_dp + short_dm)

    # --- impedance -------------------------------------------------------
    print("solving microstrip cross-sections (FDM, dx=5 um)...")
    imp_se_025 = impedance_case(0.25, None)
    imp_se_015 = impedance_case(0.15, None)
    imp_diff_025 = impedance_case(0.25, 0.25)
    imp_diff_015 = impedance_case(0.15, 0.40)
    print(f"  SE 0.25: Z0={imp_se_025['Z0_ohm']:.1f} ohm, ereff={imp_se_025['ereff']:.2f}")
    print(f"  SE 0.15: Z0={imp_se_015['Z0_ohm']:.1f} ohm, ereff={imp_se_015['ereff']:.2f}")
    print(f"  DIFF 0.25/0.25: Zdiff={imp_diff_025['Zdiff_ohm']:.1f} ohm, "
          f"ereff={imp_diff_025['ereff']:.2f}")
    print(f"  DIFF 0.15/0.40: Zdiff={imp_diff_015['Zdiff_ohm']:.1f} ohm, "
          f"ereff={imp_diff_015['ereff']:.2f}")

    # extra FDM points for the width sweep (the 90 ohm crossing)
    fdm_widths = []
    if not args.fast:
        for w in (0.30, 0.35, 0.40):
            r = impedance_case(w, 0.25)
            fdm_widths.append(r)
            print(f"  DIFF {w:.2f}/0.25: Zdiff={r['Zdiff_ohm']:.1f} ohm, "
                  f"ereff={r['ereff']:.2f}")

    # width sweep for the plot: union of the closed-form grid and the FDM points
    cal = imp_diff_025["Zdiff_ohm"] / zdiff_closed(0.25, 0.25)
    fdm_points = [(0.15, imp_diff_015["Zdiff_ohm"]), (0.25, imp_diff_025["Zdiff_ohm"])]
    fdm_points += [(r["w_mm"], r["Zdiff_ohm"]) for r in fdm_widths]
    fdm_map = {round(float(w), 3): float(z) for w, z in fdm_points}
    widths = sorted(set([round(float(w), 3) for w in np.linspace(0.10, 0.60, 26)]
                        + list(fdm_map.keys())))
    width_sweep = []
    for w in widths:
        if w in fdm_map:
            width_sweep.append({"w_mm": w, "Zdiff_ohm": fnum(fdm_map[w], 2),
                                "source": "fdm"})
        else:
            z = zdiff_closed(w, 0.25) * cal
            width_sweep.append({"w_mm": w, "Zdiff_ohm": fnum(z, 2),
                                "source": "closed-form-calibrated"})
    # find the 90 ohm width: interpolate the FDM points if available
    if len(fdm_widths) >= 2:
        pts = sorted([(0.15, imp_diff_015["Zdiff_ohm"]),
                      (0.25, imp_diff_025["Zdiff_ohm"])]
                     + [(r["w_mm"], r["Zdiff_ohm"]) for r in fdm_widths])
        w90 = None
        for (w1, z1), (w2, z2) in zip(pts, pts[1:]):
            if (z1 - 90.0) * (z2 - 90.0) <= 0.0 and z1 != z2:
                w90 = {"w_mm": fnum(w1 + (90.0 - z1) * (w2 - w1) / (z2 - z1), 3),
                       "Zdiff_ohm": 90.0, "source": "fdm-interpolated"}
                break
        if w90 is None:
            w90 = min(width_sweep, key=lambda d: abs(d["Zdiff_ohm"] - 90.0))
    else:
        w90 = min(width_sweep, key=lambda d: abs(d["Zdiff_ohm"] - 90.0))

    # --- long-line effective impedance ----------------------------------
    # length-weighted mix of the 0.25 mm and 0.15 mm sections
    dp_w = net_summary["USB_DP_CONN"]["width_mm"]
    dm_w = net_summary["USB_DM_CONN"]["width_mm"]
    l025 = dp_w.get("0.25", 0.0) + dp_w.get("0.26", 0.0) + dm_w.get("0.25", 0.0) + dm_w.get("0.26", 0.0)
    l015 = dp_w.get("0.15", 0.0) + dm_w.get("0.15", 0.0)
    l025_avg = l025 / 2.0
    l015_avg = l015 / 2.0
    z_long = (l025 * imp_diff_025["Zdiff_ohm"] + l015 * imp_diff_015["Zdiff_ohm"]) / (l025 + l015)
    er_long = (l025 * imp_diff_025["ereff"] + l015 * imp_diff_015["ereff"]) / (l025 + l015)
    print(f"  long-line weighted: Zdiff={z_long:.1f} ohm, ereff={er_long:.2f} "
          f"({l025_avg:.1f} mm/line @0.25, {l015_avg:.1f} mm/line @0.15)")

    # --- HS eye ----------------------------------------------------------
    print("HS eye simulation...")
    hs = simulate_eye(long_avg, UI_HS, V_HS, TR_HS, z_long, er_long, 0.25,
                      c_esd_per_line=C_ESD_PER_LINE, n_bits=2000, samples_per_ui=80,
                      short_length_mm=short_avg, short_zdiff=imp_diff_015["Zdiff_ohm"],
                      short_ereff=imp_diff_015["ereff"], short_w_mm=0.15)
    print(f"  eye height {hs['eye_height_mv']:.1f} mV, width {hs['eye_width_ui']:.2f} UI "
          f"({hs['eye_width_ps']:.0f} ps), overshoot {hs['overshoot_pct']:.1f}%, "
          f"S11 {hs['s11_worst']:.3f}")

    # skew estimate and skew eye
    skew_ps = skew_mm * 1e-3 * math.sqrt(er_long) / C0 * 1e12
    hs_skew = simulate_eye(long_avg, UI_HS, V_HS, TR_HS, z_long, er_long, 0.25,
                           c_esd_per_line=C_ESD_PER_LINE, n_bits=2000, samples_per_ui=80,
                           short_length_mm=short_avg, short_zdiff=imp_diff_015["Zdiff_ohm"],
                           short_ereff=imp_diff_015["ereff"], short_w_mm=0.15,
                           skew_ps=skew_ps)
    print(f"  skew {skew_mm:.2f} mm = {skew_ps:.1f} ps; "
          f"skew eye {hs_skew['eye_height_mv']:.1f} mV")

    # --- FS eye ----------------------------------------------------------
    print("FS eye simulation...")
    fs = simulate_eye(long_avg, UI_FS, V_FS, TR_FS, z_long, er_long, 0.25,
                      c_esd_per_line=C_ESD_PER_LINE, n_bits=400, samples_per_ui=80,
                      short_length_mm=short_avg, short_zdiff=imp_diff_015["Zdiff_ohm"],
                      short_ereff=imp_diff_015["ereff"], short_w_mm=0.15)
    print(f"  eye height {fs['eye_height_mv']:.1f} mV, width {fs['eye_width_ui']:.2f} UI "
          f"({fs['eye_width_ps']:.0f} ps)")

    # --- length sweep ----------------------------------------------------
    print("length sweep...")
    length_sweep = []
    closure_length = None
    width_closure_length = None
    for L in np.linspace(0.0, 400.0, 41):
        r = simulate_eye(float(L), UI_HS, V_HS, TR_HS, z_long, er_long, 0.25,
                         c_esd_per_line=C_ESD_PER_LINE, n_bits=1200, samples_per_ui=80,
                         short_length_mm=short_avg, short_zdiff=imp_diff_015["Zdiff_ohm"],
                         short_ereff=imp_diff_015["ereff"], short_w_mm=0.15)
        length_sweep.append({
            "length_mm": fnum(L, 2),
            "eye_height_mv": fnum(r["eye_height_mv"], 2),
            "eye_width_ui": fnum(r["eye_width_ui"], 3),
            "eye_width_ps": fnum(r["eye_width_ps"], 1),
        })
        if closure_length is None and r["eye_height_mv"] <= 0.0:
            closure_length = float(L)
        if width_closure_length is None and r["eye_width_ui"] < 0.4:
            width_closure_length = float(L)
    print(f"  zero-height closure length: "
          f"{closure_length if closure_length is not None else '>400'} mm")
    print(f"  0.4 UI width closure length: "
          f"{width_closure_length if width_closure_length is not None else '>400'} mm")

    # --- ESD sweep -------------------------------------------------------
    print("ESD sweep...")
    esd_sweep = []
    closure_esd = None
    width_closure_esd = None
    for c in np.linspace(0.0, 20.0, 21):
        r = simulate_eye(long_avg, UI_HS, V_HS, TR_HS, z_long, er_long, 0.25,
                         c_esd_per_line=float(c) * 1e-12, n_bits=1200, samples_per_ui=80,
                         short_length_mm=short_avg, short_zdiff=imp_diff_015["Zdiff_ohm"],
                         short_ereff=imp_diff_015["ereff"], short_w_mm=0.15)
        esd_sweep.append({
            "c_esd_per_line_pf": fnum(c, 2),
            "eye_height_mv": fnum(r["eye_height_mv"], 2),
            "eye_width_ui": fnum(r["eye_width_ui"], 3),
        })
        if closure_esd is None and r["eye_height_mv"] <= 0.0:
            closure_esd = float(c)
        if width_closure_esd is None and r["eye_width_ui"] < 0.4:
            width_closure_esd = float(c)
    print(f"  zero-height closure ESD: "
          f"{closure_esd if closure_esd is not None else '>20'} pF")
    print(f"  0.4 UI width closure ESD: "
          f"{width_closure_esd if width_closure_esd is not None else '>20'} pF")

    # --- plots -----------------------------------------------------------
    print("plots...")
    plot_eye(hs, OUT / "eye_hs.png",
             f"USB 2.0 HS 480 Mbps eye at MCU - {long_avg:.0f} mm, "
             f"Zdiff {z_long:.0f} ohm, ESD 0.7 pF\n"
             f"eye {hs['eye_height_mv']:.0f} mV / {hs['eye_width_ui']:.2f} UI "
             f"(simulation, not USB-IF compliance)", mask=True)
    plot_eye(fs, OUT / "eye_fs.png",
             f"USB 2.0 FS 12 Mbps eye at MCU - {long_avg:.0f} mm, "
             f"Zdiff {z_long:.0f} ohm\n"
             f"eye {fs['eye_height_mv']:.0f} mV / {fs['eye_width_ui']:.2f} UI "
             f"(simulation, not USB-IF compliance)", color="#2ca02c")
    plot_impedance_vs_length(width_sweep, length_sweep, long_avg, closure_length,
                             width_closure_length, OUT / "impedance_vs_length.png")
    plot_eye_vs_esd(esd_sweep, C_ESD_PER_LINE * 1e12, OUT / "eye_vs_esd.png")

    # --- JSON ------------------------------------------------------------
    result = {
        "format": "maru60-usb-si-sim/1",
        "generated_by": "pcb/tools/simulate_usb_si.py",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "board": {
            "path": str(BOARD.relative_to(ROOT)),
            "sha256": __import__("hashlib").sha256(BOARD.read_bytes()).hexdigest(),
        },
        "scope": {
            "what": "USB 2.0 FS/HS differential channel from J1 to RP2350A pins 51/52",
            "not_claimed": [
                "USB-IF compliance",
                "EMI/EMC qualification",
                "measured impedance or eye",
                "connector/ESD/MCU capacitance extraction",
                "reference-plane continuity under the full route",
            ],
        },
        "assumptions": {
            "fast_mode": args.fast,
            "stackup": {
                "source": "KiCad stackup block in maru60.kicad_pcb",
                "total_thickness_mm": fnum(stack["total_thickness_mm"], 4),
                "signal_to_reference_mm": H_DIELECTRIC_MM,
                "epsilon_r": ER,
                "loss_tangent": TAN_D,
                "copper_thickness_mm": T_COPPER_MM,
                "note": "F.Cu references In1.Cu (GND); B.Cu references In2.Cu (GND); "
                        "both inner layers carry GND zones.  The actual plane continuity "
                        "under the full route is not verified.",
            },
            "rise_time_hs_ps": TR_HS * 1e12,
            "rise_time_fs_ns": TR_FS * 1e9,
            "source_impedance_diff_ohm": ZS_DIFF,
            "load_termination_diff_ohm": ZL_DIFF,
            "series_resistor_ohm_each": R_SERIES,
            "esd": {
                "part": "TPD2EUSB30DRTR (U10)",
                "c_per_line_pf": C_ESD_PER_LINE * 1e12,
                "source": "TI datasheet DRT typical 0.7 pF IO-to-GND; max not used",
                "status": "typical, not measured",
            },
            "connector": {
                "part": "GCT USB4105-xx-A (J1, candidate)",
                "c_per_line_pf": C_CONN_PER_LINE * 1e12,
                "status": "assumed; datasheet not available in this workspace",
            },
            "mcu_pin": {
                "part": "RP2350A (U1) pins 51/52",
                "c_per_line_pf": C_PIN_PER_LINE * 1e12,
                "status": "assumed; not in the extracted board data",
            },
            "via_length_mm": VIA_LENGTH_MM,
            "via_note": "F.Cu <-> B.Cu through-via barrel added per via; "
                        "the horizontal segment lengths do not include it.",
            "differential_shunt": "per-line shunt C is halved for the differential mode",
            "dielectric_loss": "G = omega*C*tan(delta)",
            "conductor_loss": "R = R_dc + 1.5*Rs/w, Rs = sqrt(pi*f*mu0*rho)",
            "impedance_method": "2-D finite-volume Laplace solve, dx=5 um, "
                                "rectangular conductor on the dielectric interface",
        },
        "extracted": {
            "footprints": {r: {"value": fps[r]["value"], "at": fps[r]["at"],
                               "layer": fps[r]["layer"]} for r in sorted(fps)},
            "nets": net_summary,
            "lengths_mm": {
                "dp_connector_to_resistor": long_dp,
                "dm_connector_to_resistor": long_dm,
                "dp_resistor_to_mcu": short_dp,
                "dm_resistor_to_mcu": short_dm,
                "dp_total": fnum(dp_total, 3),
                "dm_total": fnum(dm_total, 3),
                "long_average": fnum(long_avg, 3),
                "short_average": fnum(short_avg, 3),
            },
            "intra_pair_skew_mm": fnum(skew_mm, 3),
            "intra_pair_skew_ps": fnum(skew_ps, 2),
            "reference_plane": {
                "F.Cu": "In1.Cu (GND)",
                "B.Cu": "In2.Cu (GND)",
                "dielectric_between_mm": H_DIELECTRIC_MM,
            },
            "series_resistors": {
                "R102": {"value": fps["R102"]["value"], "net_a": "USB_DP_CONN",
                         "net_b": "USB_DP", "at": fps["R102"]["at"]},
                "R103": {"value": fps["R103"]["value"], "net_a": "USB_DM_CONN",
                         "net_b": "USB_DM", "at": fps["R103"]["at"]},
            },
            "esd": {"U10": {"value": fps["U10"]["value"], "at": fps["U10"]["at"],
                            "pads": [p["net"] for p in fps["U10"]["pads"]]}},
            "mcu": {"U1": {"at": fps["U1"]["at"],
                           "usb_pads": [p for p in fps["U1"]["pads"]
                                        if p["net"] and p["net"][1] in ("USB_DM", "USB_DP")]}},
        },
        "impedance": {
            "single_ended": {
                "w_0.25mm": {k: fnum(v, 3) for k, v in imp_se_025.items()},
                "w_0.15mm": {k: fnum(v, 3) for k, v in imp_se_015.items()},
            },
            "differential": {
                "w_0.25mm_s_0.25mm": {k: fnum(v, 3) for k, v in imp_diff_025.items()},
                "w_0.15mm_s_0.40mm": {k: fnum(v, 3) for k, v in imp_diff_015.items()},
                "long_line_weighted": {
                    "Zdiff_ohm": fnum(z_long, 2),
                    "ereff": fnum(er_long, 3),
                    "length_0.25mm_per_line": fnum(l025_avg, 2),
                    "length_0.15mm_per_line": fnum(l015_avg, 2),
                },
            },
            "target_90ohm": {
                "met": False,
                "error_0.25mm_pct": fnum((imp_diff_025["Zdiff_ohm"] - 90.0) / 90.0 * 100.0, 1),
                "error_0.15mm_pct": fnum((imp_diff_015["Zdiff_ohm"] - 90.0) / 90.0 * 100.0, 1),
                "width_for_90ohm_mm": w90["w_mm"],
                "width_for_90ohm_Zdiff": w90["Zdiff_ohm"],
                "note": ("closed-form width sweep calibrated to the FDM at 0.25 mm; "
                         "run without --fast for the FDM 90 ohm crossing")
                        if args.fast else
                        ("FDM points at 0.15/0.25/0.30/0.35/0.40 mm, linear "
                         "interpolation for the 90 ohm crossing; the calibrated "
                         "closed-form curve is a cross-check"),
            },
            "closed_form_cross_check": {
                "Z0_0.25mm": fnum(z0_microstrip_closed(0.25), 2),
                "Z0_0.15mm": fnum(z0_microstrip_closed(0.15), 2),
                "Zdiff_0.25mm_s0.25": fnum(zdiff_closed(0.25, 0.25), 2),
                "Zdiff_0.15mm_s0.40": fnum(zdiff_closed(0.15, 0.40), 2),
            },
        },
        "rlcg": {
            "long_line": {
                "Zdiff_ohm": fnum(z_long, 2),
                "ereff": fnum(er_long, 3),
                "L_nH_per_m": fnum(z_long * math.sqrt(er_long) / C0 * 1e9, 2),
                "C_pF_per_m": fnum(math.sqrt(er_long) / (z_long * C0) * 1e12, 2),
                "R_dc_ohm_per_m": fnum(2.0 * RHO_CU / (0.25e-3 * T_COPPER_MM * 1e-3), 3),
                "R_at_240MHz_ohm_per_m": fnum(
                    2.0 * RHO_CU / (0.25e-3 * T_COPPER_MM * 1e-3)
                    + 2.0 * 1.5 * math.sqrt(math.pi * 240e6 * MU0 * RHO_CU) / 0.25e-3, 2),
                "G_at_240MHz_S_per_m": fnum(
                    2 * math.pi * 240e6 * math.sqrt(er_long) / (z_long * C0) * TAN_D, 6),
            },
            "short_line": {
                "Zdiff_ohm": fnum(imp_diff_015["Zdiff_ohm"], 2),
                "ereff": fnum(imp_diff_015["ereff"], 3),
                "L_nH_per_m": fnum(imp_diff_015["Zdiff_ohm"] * math.sqrt(imp_diff_015["ereff"]) / C0 * 1e9, 2),
                "C_pF_per_m": fnum(math.sqrt(imp_diff_015["ereff"]) / (imp_diff_015["Zdiff_ohm"] * C0) * 1e12, 2),
            },
        },
        "simulation": {
            "hs": {
                "bit_rate_mbps": 480,
                "ui_ps": UI_HS * 1e12,
                "prbs": "PRBS-7, 2000 bits",
                "eye_height_mv": fnum(hs["eye_height_mv"], 2),
                "eye_width_ui": fnum(hs["eye_width_ui"], 3),
                "eye_width_ps": fnum(hs["eye_width_ps"], 1),
                "high_mean_mv": fnum(hs["high_mean_mv"], 2),
                "low_mean_mv": fnum(hs["low_mean_mv"], 2),
                "overshoot_pct": fnum(hs["overshoot_pct"], 2),
                "undershoot_pct": fnum(hs["undershoot_pct"], 2),
                "s11_worst": fnum(hs["s11_worst"], 4),
                "s11_worst_ghz": fnum(hs["s11_worst_ghz"], 3),
                "s11_240mhz": fnum(hs["s11_240mhz"], 4),
                "s11_720mhz": fnum(hs["s11_720mhz"], 4),
                "return_loss_db": fnum(hs["return_loss_db"], 2),
                "skew_ps": fnum(skew_ps, 2),
                "skew_eye_height_mv": fnum(hs_skew["eye_height_mv"], 2),
                "skew_eye_width_ui": fnum(hs_skew["eye_width_ui"], 3),
            },
            "fs": {
                "bit_rate_mbps": 12,
                "ui_ns": UI_FS * 1e9,
                "prbs": "PRBS-7, 400 bits",
                "eye_height_mv": fnum(fs["eye_height_mv"], 2),
                "eye_width_ui": fnum(fs["eye_width_ui"], 3),
                "eye_width_ps": fnum(fs["eye_width_ps"], 1),
                "overshoot_pct": fnum(fs["overshoot_pct"], 2),
                "undershoot_pct": fnum(fs["undershoot_pct"], 2),
                "s11_worst": fnum(fs["s11_worst"], 4),
                "return_loss_db": fnum(fs["return_loss_db"], 2),
            },
        },
        "sweeps": {
            "length": length_sweep,
            "esd": esd_sweep,
            "eye_closure_length_mm": closure_length,
            "eye_closure_esd_pf": closure_esd,
            "width_0p4ui_closure_length_mm": width_closure_length,
            "width_0p4ui_closure_esd_pf": width_closure_esd,
            "actual_length_mm": fnum(long_avg, 2),
            "actual_esd_pf": C_ESD_PER_LINE * 1e12,
        },
        "unknowns": [
            "stackup er / tan(delta) / prepreg thickness: taken from the KiCad stackup, not measured",
            "connector model: 0.5 pF per line assumed, no GCT USB4105 datasheet in the workspace",
            "ESD capacitance: 0.7 pF typical from the TI datasheet; max and voltage dependence not used",
            "MCU pin capacitance: 3 pF per line assumed",
            "host source impedance and HS rise time: 90 ohm differential and 150 ps assumed",
            "reference-plane continuity under the full 167 mm route: not verified",
            "via model: 1.55 mm barrel per via, no stub/return-path model",
            "copper roughness, solder mask, and connector launch: not modelled",
        ],
        "conclusions": {
            "impedance_90ohm": "not met: 0.25 mm pair ~113 ohm, 0.15 mm fan-out ~150 ohm",
            "length": f"{long_avg:.0f} mm connector-to-resistor, {short_avg:.1f} mm resistor-to-MCU",
            "skew": f"{skew_mm:.2f} mm / {skew_ps:.1f} ps intra-pair",
            "hs_eye": f"{hs['eye_height_mv']:.0f} mV / {hs['eye_width_ui']:.2f} UI (simulation)",
            "fs_eye": f"{fs['eye_height_mv']:.0f} mV / {fs['eye_width_ui']:.2f} UI (simulation)",
            "layout": "widen the 0.25 mm sections to ~0.40 mm for 90 ohm; shorten the "
                      "167 mm connector-to-resistor run; keep the 0.15 mm fan-out short; "
                      "reduce via count; verify the reference plane under the route",
        },
    }

    json_path = OUT / "usb-si-sim.json"
    json_path.write_text(json.dumps(result, indent=2) + "\n")
    print(f"wrote {json_path}")

    # --- REPORT.md -------------------------------------------------------
    report = f"""# USB 2.0 D+/D- signal-integrity model - Maru60

**Status:** simulation study.  This is **not** a USB-IF compliance claim and **not**
an EMI/EMC qualification.  No VNA, TDR, or eye measurement was performed.
{"" if not args.fast else "**Fast mode:** the extra FDM width sweep was skipped; the 90 ohm width is from the calibrated closed-form curve."}

## 1. What was extracted from the board

| Item | Value |
|---|---|
| Connector | J1, GCT USB4105-xx-A (candidate), B.Cu, at (18.0, 3.8) mm |
| Series resistors | R102 / R103, 27 ohm each, 0402, at (118.4, 82.6) / (118.4, 81.6) mm |
| ESD | U10, TPD2EUSB30DRTR, at (18.5, 10.75) mm, on the connector side |
| MCU | U1, RP2350A, USB_DM = pin 51, USB_DP = pin 52 |
| D+ connector-to-resistor | {long_dp:.2f} mm (incl. {net_summary['USB_DP_CONN']['via_count']} vias) |
| D- connector-to-resistor | {long_dm:.2f} mm (incl. {net_summary['USB_DM_CONN']['via_count']} vias) |
| D+ resistor-to-MCU | {short_dp:.2f} mm |
| D- resistor-to-MCU | {short_dm:.2f} mm |
| Intra-pair skew | {skew_mm:.2f} mm = {skew_ps:.1f} ps |
| Widths | 0.25 mm for most of the run; 0.15 mm fan-out at both ends; one 0.26 mm segment |
| Layers | F.Cu and B.Cu, with {net_summary['USB_DP_CONN']['via_count']} / {net_summary['USB_DM_CONN']['via_count']} vias |
| Reference plane | F.Cu -> In1.Cu (GND); B.Cu -> In2.Cu (GND); 0.2104 mm prepreg |

The route is **{long_avg:.0f} mm** from the connector to the series resistors and only
**{short_avg:.1f} mm** from the resistors to the MCU.  The 27 ohm resistors are therefore
at the MCU end, which is the correct source-termination placement, but the long line
between the connector and the resistors is the dominant SI element.

## 2. Stackup and impedance

The KiCad stackup is 4-layer, 1.6 mm class: F.Cu 0.035 mm / prepreg 0.2104 mm
(er 4.4, tan d 0.02) / In1.Cu 0.0152 mm / core 1.065 mm (er 4.6) / In2.Cu 0.0152 mm /
prepreg 0.2104 mm / B.Cu 0.035 mm.  The signal-to-reference spacing used here is
**0.2104 mm**, er **4.4**, tan d **0.02**.

A 2-D finite-volume Laplace solve (dx = 5 um) gives:

| Cross-section | Single-ended Z0 | Differential Zdiff | er_eff |
|---|---:|---:|---:|
| 0.25 mm, gap 0.25 mm | {imp_se_025['Z0_ohm']:.1f} ohm | **{imp_diff_025['Zdiff_ohm']:.1f} ohm** | {imp_diff_025['ereff']:.2f} |
| 0.15 mm, gap 0.40 mm | {imp_se_015['Z0_ohm']:.1f} ohm | **{imp_diff_015['Zdiff_ohm']:.1f} ohm** | {imp_diff_015['ereff']:.2f} |

The 90 ohm differential target is **not met**.  The 0.25 mm pair is about
**+{(imp_diff_025['Zdiff_ohm']-90)/90*100:.0f}%** high and the 0.15 mm fan-out is about
**+{(imp_diff_015['Zdiff_ohm']-90)/90*100:.0f}%** high.  The closed-form cross-check
(IPC-2141 style) gives {z0_microstrip_closed(0.25):.1f} ohm single-ended for 0.25 mm,
i.e. the FDM is ~9% higher; the difference is the thick-trace/discretisation
uncertainty.  Either way the board is above 90 ohm.  A width of about
**{w90['w_mm']:.2f} mm** (gap 0.25 mm) is needed for 90 ohm on this stackup.

## 3. Channel model

Topology (connector -> MCU):

```
host 90 ohm diff  ->  shunt (connector 0.5 pF + ESD 0.7 pF per line)  ->
long TL {long_avg:.0f} mm, Zdiff {z_long:.0f} ohm, er_eff {er_long:.2f}  ->
27 ohm series (54 ohm differential)  ->
short TL {short_avg:.1f} mm, Zdiff {imp_diff_015['Zdiff_ohm']:.0f} ohm  ->
(MCU pin 3 pF || 90 ohm termination)
```

RLCG is frequency-dependent: R = R_dc + 1.5*Rs/w with Rs = sqrt(pi f mu0 rho),
L and C from Zdiff and er_eff, G = omega C tan d.  The long line is a
length-weighted mix of the 0.25 mm and 0.15 mm sections.  The model is a
quasi-static, uniform-section approximation; it does not resolve the individual
impedance discontinuities at every width change or via.

## 4. HS 480 Mbps result

PRBS-7, 2000 bits, 150 ps (10-90%) assumed rise time, 0.4 V differential
Thevenin source, 90 ohm source and load.

| Metric | Value |
|---|---:|
| Eye height at MCU | **{hs['eye_height_mv']:.0f} mV** |
| Eye width at MCU | **{hs['eye_width_ui']:.2f} UI** ({hs['eye_width_ps']:.0f} ps) |
| High / low mean | {hs['high_mean_mv']:.0f} / {hs['low_mean_mv']:.0f} mV |
| Overshoot / undershoot | {hs['overshoot_pct']:.1f}% / {hs['undershoot_pct']:.1f}% |
| S11 at 240 MHz / 720 MHz | {hs['s11_240mhz']:.3f} / {hs['s11_720mhz']:.3f} |
| Worst S11 (0.01-2 GHz) | {hs['s11_worst']:.3f} at {hs['s11_worst_ghz']:.2f} GHz |
| Return loss (worst) | {hs['return_loss_db']:.1f} dB |
| Intra-pair skew | {skew_mm:.2f} mm = {skew_ps:.1f} ps |
| Eye with skew applied | {hs_skew['eye_height_mv']:.0f} mV / {hs_skew['eye_width_ui']:.2f} UI |

The eye is **open in this model** but the height is essentially at the 0.3 V
template: the 27 ohm series resistors and the 90 ohm termination divide the
0.4 V source down to about 0.30 V, and the 113 ohm line / 150 ohm fan-out add
ISI.  The eye width (0.53 UI) is above the 0.4 UI template.  The 0.3 V / 0.4 UI
rectangle on `eye_hs.png` is shown for orientation only; this is not a
compliance test.

## 5. FS 12 Mbps result

PRBS-7, 400 bits, 4 ns (10-90%) assumed rise time, 1.4 V differential
Thevenin source.

| Metric | Value |
|---|---:|
| Eye height at MCU | **{fs['eye_height_mv']:.0f} mV** |
| Eye width at MCU | **{fs['eye_width_ui']:.2f} UI** ({fs['eye_width_ps']:.0f} ps) |
| Overshoot / undershoot | {fs['overshoot_pct']:.1f}% / {fs['undershoot_pct']:.1f}% |
| Worst S11 | {fs['s11_worst']:.3f} |

FS is not the limiting case; the 167 mm line is electrically short at 12 Mbps.

## 6. Length and ESD margin

- **Length sweep** (0-400 mm, ESD 0.7 pF): the eye height falls slowly with
  length (the 27 ohm series resistors and the 90 ohm termination dominate the
  DC divider), while the eye width falls faster.  The first zero-height point is
  **{closure_length if closure_length is not None else '>400'} mm**; the eye
  width first drops below the 0.4 UI template at
  **{width_closure_length if width_closure_length is not None else '>400'} mm**.
  The actual {long_avg:.0f} mm is marked on `impedance_vs_length.png`.
- **ESD sweep** (0-20 pF per line, actual length): the first zero-height point is
  **{closure_esd if closure_esd is not None else '>20'} pF**; the eye width first
  drops below 0.4 UI at
  **{width_closure_esd if width_closure_esd is not None else '>20'} pF**.  The
  TPD2EUSB30 typical 0.7 pF is well inside the simulated margin, but the
  max/voltage dependence is unknown.

## 7. What is closed, what needs measurement

**Closed by simulation (with the stated assumptions):**
- The 90 ohm differential target is **not met** by the current 0.25 mm / 0.15 mm
  geometry; the required width is about {w90['w_mm']:.2f} mm.
- The 27 ohm series resistors are on the correct (MCU) side of the long run.
- Intra-pair skew is {skew_mm:.2f} mm / {skew_ps:.1f} ps, about
  {skew_ps/UI_HS/1e12*100:.1f}% of the HS UI; it is small but not zero.
- The HS eye is open in the model at the actual length, with the 0.7 pF ESD
  typical value.  The height is at the 0.3 V template; the width is above the
  0.4 UI template.  The margin is dominated by the 27 ohm / 90 ohm divider and
  the 113 ohm line, not by the ESD capacitance in the 0-5 pF range.
- FS has large margin.

**Needs a VNA / TDR / eye measurement:**
- Actual single-ended and differential impedance of the 0.25 mm and 0.15 mm
  sections, including the via and connector launch.
- Reference-plane continuity under the full 167 mm route (the model assumes a
  solid GND reference).
- Connector and ESD capacitance at the actual bias/voltage; the 0.5 pF and
  0.7 pF values are assumptions/typical values.
- MCU pin capacitance and the RP2350 USB PHY source/termination behaviour.
- Real HS eye with a host and the device, including the 27 ohm resistors and
  the actual rise time.
- EMI/EMC is out of scope.

## 8. Layout changes (if any)

1. **Widen the 0.25 mm sections to ~{w90['w_mm']:.2f} mm** (gap ~0.25 mm) to
   bring Zdiff from ~113 ohm to ~90 ohm.  Re-run the field solve after the
   stackup is fixed.
2. **Shorten the connector-to-resistor run.**  {long_avg:.0f} mm is long for HS;
   moving the MCU and connector closer, or re-routing the long run on one layer
   with fewer vias, would reduce ISI and loss.  Keep the 27 ohm resistors at the
   MCU end (source termination); do not move them to the connector.
3. **Keep the 0.15 mm fan-out as short as possible**; it is ~150 ohm and creates
   two impedance discontinuities.  A short taper or a wider fan-out would help.
4. **Reduce the via count** (5 on D+, 4 on D-) and verify the return path at each
   layer transition.
5. **Verify the GND reference plane** under the full route; the model assumes a
   solid In1/In2 GND.
6. **Place the ESD at the connector** (it already is) and keep the stub to the ESD
   pads short.

## 9. Files

- `usb-si-sim.json` - all extracted numbers, assumptions, sweeps, and results
- `eye_hs.png` - HS 480 Mbps eye at the MCU
- `eye_fs.png` - FS 12 Mbps eye at the MCU
- `impedance_vs_length.png` - Zdiff vs width and eye vs length
- `eye_vs_esd.png` - eye vs ESD capacitance
- `pcb/tools/simulate_usb_si.py` - the model

## 10. Unknowns (explicit)

Stackup er/tan d/thickness (from KiCad, not measured); connector model (0.5 pF
assumed); ESD capacitance (0.7 pF typical, max not used); MCU pin capacitance
(3 pF assumed); host source impedance and rise time (90 ohm / 150 ps assumed);
reference-plane continuity; via model (1.55 mm barrel, no stub); copper
roughness, solder mask, connector launch.  These are marked as unknown, not as
measured facts.
"""
    report_path = OUT / "REPORT.md"
    report_path.write_text(report)
    print(f"wrote {report_path}")
    print(f"done in {time.time() - t_start:.1f} s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
