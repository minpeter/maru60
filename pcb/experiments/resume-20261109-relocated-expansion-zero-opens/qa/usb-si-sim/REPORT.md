# USB 2.0 D+/D- signal-integrity model - Maru60

**Status:** simulation study.  This is **not** a USB-IF compliance claim and **not**
an EMI/EMC qualification.  No VNA, TDR, or eye measurement was performed.


## 1. What was extracted from the board

| Item | Value |
|---|---|
| Connector | J1, GCT USB4105-xx-A (candidate), B.Cu, at (18.0, 3.8) mm |
| Series resistors | R102 / R103, 27 ohm each, 0402, at (118.4, 82.6) / (118.4, 81.6) mm |
| ESD | U10, TPD2EUSB30DRTR, at (18.5, 10.75) mm, on the connector side |
| MCU | U1, RP2350A, USB_DM = pin 51, USB_DP = pin 52 |
| D+ connector-to-resistor | 169.63 mm (incl. 5 vias) |
| D- connector-to-resistor | 164.59 mm (incl. 4 vias) |
| D+ resistor-to-MCU | 4.10 mm |
| D- resistor-to-MCU | 3.85 mm |
| Intra-pair skew | 5.28 mm = 27.5 ps |
| Widths | 0.25 mm for most of the run; 0.15 mm fan-out at both ends; one 0.26 mm segment |
| Layers | F.Cu and B.Cu, with 5 / 4 vias |
| Reference plane | F.Cu -> In1.Cu (GND); B.Cu -> In2.Cu (GND); 0.2104 mm prepreg |

The route is **167 mm** from the connector to the series resistors and only
**4.0 mm** from the resistors to the MCU.  The 27 ohm resistors are therefore
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
| 0.25 mm, gap 0.25 mm | 66.1 ohm | **112.8 ohm** | 2.45 |
| 0.15 mm, gap 0.40 mm | 82.6 ohm | **150.4 ohm** | 2.40 |

The 90 ohm differential target is **not met**.  The 0.25 mm pair is about
**+25%** high and the 0.15 mm fan-out is about
**+67%** high.  The closed-form cross-check
(IPC-2141 style) gives 60.6 ohm single-ended for 0.25 mm,
i.e. the FDM is ~9% higher; the difference is the thick-trace/discretisation
uncertainty.  Either way the board is above 90 ohm.  A width of about
**0.40 mm** (gap 0.25 mm) is needed for 90 ohm on this stackup.

## 3. Channel model

Topology (connector -> MCU):

```
host 90 ohm diff  ->  shunt (connector 0.5 pF + ESD 0.7 pF per line)  ->
long TL 167 mm, Zdiff 118 ohm, er_eff 2.44  ->
27 ohm series (54 ohm differential)  ->
short TL 4.0 mm, Zdiff 150 ohm  ->
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
| Eye height at MCU | **299 mV** |
| Eye width at MCU | **0.53 UI** (1094 ps) |
| High / low mean | 151 / -151 mV |
| Overshoot / undershoot | 1.4% / 1.3% |
| S11 at 240 MHz / 720 MHz | 0.073 / 0.142 |
| Worst S11 (0.01-2 GHz) | 0.456 at 2.00 GHz |
| Return loss (worst) | 6.8 dB |
| Intra-pair skew | 5.28 mm = 27.5 ps |
| Eye with skew applied | 299 mV / 0.51 UI |

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
| Eye height at MCU | **1071 mV** |
| Eye width at MCU | **0.99 UI** (82292 ps) |
| Overshoot / undershoot | 0.0% / 0.0% |
| Worst S11 | 0.241 |

FS is not the limiting case; the 167 mm line is electrically short at 12 Mbps.

## 6. Length and ESD margin

- **Length sweep** (0-400 mm, ESD 0.7 pF): the eye height falls slowly with
  length (the 27 ohm series resistors and the 90 ohm termination dominate the
  DC divider), while the eye width falls faster.  The first zero-height point is
  **380.0 mm**; the eye
  width first drops below the 0.4 UI template at
  **220.0 mm**.
  The actual 167 mm is marked on `impedance_vs_length.png`.
- **ESD sweep** (0-20 pF per line, actual length): the first zero-height point is
  **>20 pF**; the eye width first
  drops below 0.4 UI at
  **15.0 pF**.  The
  TPD2EUSB30 typical 0.7 pF is well inside the simulated margin, but the
  max/voltage dependence is unknown.

## 7. What is closed, what needs measurement

**Closed by simulation (with the stated assumptions):**
- The 90 ohm differential target is **not met** by the current 0.25 mm / 0.15 mm
  geometry; the required width is about 0.40 mm.
- The 27 ohm series resistors are on the correct (MCU) side of the long run.
- Intra-pair skew is 5.28 mm / 27.5 ps, about
  1.3% of the HS UI; it is small but not zero.
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

1. **Widen the 0.25 mm sections to ~0.40 mm** (gap ~0.25 mm) to
   bring Zdiff from ~113 ohm to ~90 ohm.  Re-run the field solve after the
   stackup is fixed.
2. **Shorten the connector-to-resistor run.**  167 mm is long for HS;
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
