"""ngspice runner and small netlist helpers shared by the sim_*.py scripts.

Decks are written to pcb/tools/signal_integrity/decks/ (kept in the repository),
raw output to build/si/out/ (git-ignored). ngspice runs in the Docker image
built from the Dockerfile in this folder:

    docker build -t maru60-ngspice:bookworm pcb/tools/signal_integrity
"""
from __future__ import annotations

import json
import math
import os
import subprocess
import uuid
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DECKS = HERE / "decks"
OUT = ROOT / "build" / "si" / "out"
QA = ROOT / "pcb" / "experiments" / "resume-20261111-order-candidate" / "qa" / "signal-integrity"
IMAGE = os.environ.get("MARU60_NGSPICE_IMAGE", "maru60-ngspice:bookworm")


class SimulationAborted(RuntimeError):
    """ngspice can return exit zero and write partial data after an abort."""


RHO_CU = 1.72e-8  # ohm m
T_CU = 35e-6


def lines():
    return json.loads((OUT / "lines.json").read_text())


def geometry():
    return json.loads((OUT / "geometry.json").read_text())


def line_params(w, table=None):
    """Interpolated per-mm C (pF), L (nH), and DC R (ohm) for an outer-layer track of width w (mm)."""
    table = table or lines()
    ws = sorted(float(k) for k in table["single"])
    w_ = min(max(w, ws[0]), ws[-1])
    for a, b in zip(ws, ws[1:]):
        if a <= w_ <= b:
            u = (w_ - a) / (b - a)
            ta, tb = table["single"][f"{a:.2f}"], table["single"][f"{b:.2f}"]
            return {k: (1 - u) * ta[k] + u * tb[k] for k in ("C_pF_per_mm", "L_nH_per_mm", "Z0_ohm", "delay_ps_per_mm")} | {
                "R_ohm_per_mm": RHO_CU / (w * 1e-3 * T_CU) * 1e-3}
    raise ValueError(w)


class Deck:
    def __init__(self, title):
        self.lines = [f"* {title}"]
        self._n = 0

    def add(self, *text):
        self.lines.extend(text)

    def uid(self, prefix="n"):
        self._n += 1
        return f"{prefix}{self._n}"

    def ladder(self, a, b, length_mm, w_mm, table=None, max_section_mm=2.0, tag="t"):
        """Lossy LC ladder between nodes a and b for a single track over the plane."""
        # Splitting a route at a stub can leave a ~1e-15 mm floating-point
        # remainder. An LC ladder for that numerical zero makes ngspice's
        # matrix ill-conditioned. 1e-9 mm is 1000x below KiCad's 1 nm grid.
        if length_mm <= 1e-9:
            self.add(f"R{self.uid('j')} {a} {b} 1m")
            return
        p = line_params(w_mm, table)
        n = max(1, math.ceil(length_mm / max_section_mm))
        d = length_mm / n
        prev = a
        for i in range(n):
            mid = self.uid(tag + "m")
            nxt = b if i == n - 1 else self.uid(tag)
            k = self.uid("")
            self.add(f"R{tag}{k} {prev} {mid} {p['R_ohm_per_mm'] * d:.6g}",
                     f"L{tag}{k} {mid} {nxt} {p['L_nH_per_mm'] * d:.6g}n",
                     f"C{tag}{k} {nxt} 0 {p['C_pF_per_mm'] * d:.6g}p")
            prev = nxt

    def via(self, a, b, table=None):
        t = table or lines()
        k = self.uid("")
        self.add(f"Lv{k} {a} {b} {t['via_L_nH']:.4g}n", f"Cv{k} {b} 0 {t['via_C_pF']:.4g}p")

    def coupled_ladder(self, a1, b1, a2, b2, length_mm, cp, max_section_mm=2.0, tag="c"):
        """Two coupled tracks. cp: dict from fieldsolve.coupled()/pair() with C11, C22, Cm, L11, L22, Lm per mm."""
        n = max(1, math.ceil(length_mm / max_section_mm))
        d = length_mm / n
        c11 = cp["C11_pF_per_mm"] - cp["Cm_pF_per_mm"]            # to ground
        c22 = cp.get("C22_pF_per_mm", cp["C11_pF_per_mm"]) - cp["Cm_pF_per_mm"]
        l11, l22 = cp["L11_nH_per_mm"], cp.get("L22_nH_per_mm", cp["L11_nH_per_mm"])
        kk = cp["Lm_nH_per_mm"] / math.sqrt(l11 * l22)
        p1, p2 = a1, a2
        for i in range(n):
            n1 = b1 if i == n - 1 else self.uid(tag + "a")
            n2 = b2 if i == n - 1 else self.uid(tag + "b")
            k = self.uid("")
            # series copper resistance keeps the ladder damped (and the solver's time step sane)
            m1, m2 = self.uid(tag + "ra"), self.uid(tag + "rb")
            ra = RHO_CU / (cp.get("w_victim", cp.get("w_mm", 0.2)) * 1e-3 * T_CU) * 1e-3 * d
            rb = RHO_CU / (cp.get("w_aggr", cp.get("w_mm", 0.2)) * 1e-3 * T_CU) * 1e-3 * d
            self.add(f"R{tag}a{k} {p1} {m1} {ra:.6g}", f"R{tag}b{k} {p2} {m2} {rb:.6g}")
            p1, p2 = m1, m2
            self.add(f"L{tag}a{k} {p1} {n1} {l11 * d:.6g}n", f"L{tag}b{k} {p2} {n2} {l22 * d:.6g}n",
                     f"K{tag}{k} L{tag}a{k} L{tag}b{k} {kk:.5f}",
                     f"C{tag}a{k} {n1} 0 {c11 * d:.6g}p", f"C{tag}b{k} {n2} 0 {c22 * d:.6g}p",
                     f"C{tag}m{k} {n1} {n2} {cp['Cm_pF_per_mm'] * d:.6g}p")
            p1, p2 = n1, n2

    def run(self, name, vectors, tran=None, control_extra=""):
        """Write decks/<name>.cir, run it, return {vector: array} plus 'time'."""
        DECKS.mkdir(exist_ok=True)
        OUT.mkdir(parents=True, exist_ok=True)
        text = list(self.lines)
        if tran:
            text.append(f".tran {tran}")
        text += [".control", "set wr_singlescale", "set wr_vecnames", "set numdgt=7", "run", control_extra,
                 f"wrdata /out/{name}.txt " + " ".join(vectors), "quit 0", ".endc", ".end", ""]
        (DECKS / f"{name}.cir").write_text("\n".join(t for t in text if t is not None))
        return run_deck(name)


def run_deck(name):
    out = OUT / f"{name}.txt"
    if out.exists():
        out.unlink()
    container = f"maru60-si-{uuid.uuid4().hex}"
    cmd = ["docker", "run", "--rm", "--name", container, "-u", f"{os.getuid()}:{os.getgid()}", "-v", f"{DECKS}:/decks:ro", "-v", f"{OUT}:/out",
           "-w", "/out", IMAGE, "-b", f"/decks/{name}.cir"]
    try:
        r = subprocess.run(cmd + [], capture_output=True, text=True, timeout=float(os.environ.get("MARU60_NGSPICE_TIMEOUT", "240")))
    except subprocess.TimeoutExpired:
        subprocess.run(["docker", "rm", "-f", container], capture_output=True)
        raise RuntimeError(f"ngspice timed out for {name}")
    (OUT / f"{name}.log").write_text(r.stdout + "\n--- stderr ---\n" + r.stderr)
    if "simulation(s) aborted" in (r.stdout + r.stderr).lower():
        raise SimulationAborted(f"ngspice aborted {name}; partial waveforms are invalid")
    if r.returncode != 0:
        raise RuntimeError(f"ngspice exited {r.returncode} for {name}:\n{r.stderr[-2000:]}")
    if not out.exists():
        raise RuntimeError(f"ngspice failed for {name}:\n{r.stdout[-2000:]}\n{r.stderr[-2000:]}")
    with out.open() as f:
        names = f.readline().split()
        data = np.loadtxt(f, ndmin=2)
    if not data.size or not np.isfinite(data).all():
        raise RuntimeError(f"ngspice wrote empty or nonfinite data for {name}")
    return {n: data[:, i] for i, n in enumerate(names)}


# ---- waveform measurements ---------------------------------------------------
def crossings(t, v, level, rising):
    out = []
    s = v - level
    idx = np.where((s[:-1] < 0) & (s[1:] >= 0))[0] if rising else np.where((s[:-1] > 0) & (s[1:] <= 0))[0]
    for i in idx:
        out.append(t[i] + (t[i + 1] - t[i]) * (level - v[i]) / (v[i + 1] - v[i]))
    return out


def edge_time(t, v, lo, hi, rising, after=0.0):
    """10-90 style time between two levels for the first edge after `after`."""
    a = [x for x in crossings(t, v, lo if rising else hi, rising) if x >= after]
    if not a:
        return None
    b = [x for x in crossings(t, v, hi if rising else lo, rising) if x >= a[0]]
    return (b[0] - a[0]) if b else None


def style(ax, title=None, xlabel=None, ylabel=None):
    ax.set_facecolor("#fcfcfb")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#c3c2b7")
    ax.grid(True, color="#e6e5e0", linewidth=0.6)
    ax.tick_params(colors="#52514e", labelsize=8)
    if title:
        ax.set_title(title, fontsize=9.5, color="#0b0b0b", loc="left")
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=8.5, color="#52514e")
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=8.5, color="#52514e")


SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]
INK2 = "#52514e"
