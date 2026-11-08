# Brownout, short removal and USB restart contract

**Architecture proposal, not implemented or qualified.** The native revision changes BOM/footprints and C142 value only; it intentionally does not pretend a new reset circuit exists. Accepted firmware/PCB remain unchanged. This is the explicit remaining implementation gap, not a bench-only caveat.

## Why a startup sleep cannot fix this

MAX38902A with the earlier 68 nF has nominal ~4.488 ms startup and approximately **2.244 s short recovery**. This implementation candidate uses 10 nF, giving ~0.660 ms / **330 ms** instead. The factor and slew formula are not all-corner limits. Both recovery ramps are long enough that processor execution, USB and external signals cannot be assumed valid throughout a partial/slow rail recovery. Increasing a firmware sleep does nothing before firmware can execute correctly.

The [RP2350 datasheet](https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf), §7.6.3, distinguishes its ~0.87–1.26 V VREG_AVDD supply-monitor activation from safe 3.3 V operation. A partial dip can fail to reinitialize POR. §7.5/7.6 states that **RUN LOW holds the chip in reset regardless of DVDD, POR or BOD state**. That provides the right external reset mechanism. It does not mean an unqualified supervisor will catch every arbitrarily short dip.

Current reviewed V6 U12 is **TLV810EA29DBZR**, driving `GPIO_ISOLATE`, **not RUN**. It is not a 3.3 V valid-rail/reset guarantee for RP2350. The new LDO's EN is tied to +4V_REG, so firmware cannot reset its BYP ramp or use an LDO MODE pin. No such GPIO was allocated or invented.

## Required hardware path before adoption

1. **Monitor +3V3 at the regulated star with a qualified external supervisor, and drive MCU RUN directly.** Do not rely on a firmware ADC/poll or on POR dropping below ~1.1 V. Proposed design window: guaranteed falling trip between **3.17 and 3.22 V**, guaranteed rising qualification no higher than **3.25 V**, so a static 3.267 V low-corner output can release reset. These are engineering targets, not new user requirements. Detector accuracy, divider drift/input leakage, hysteresis and routing error must fit together.
2. **Hold reset for a qualified interval after the rail actually becomes valid.** A proposed ≥10 ms hardware release interval gives a deliberate USB detach/restart opportunity, but is not a claim that the LDO always settles in 10 ms. Any recurrent threshold crossing restarts qualification; no release while the rail is still ramping, oscillating or in thermal/current-limit cycling. Include supervisor supply behavior and RESET validity near zero volts.
3. **Establish a finite falling-edge/pulse envelope.** Specify maximum assertion latency and minimum detected fault pulse width, then prove the allowed rail trajectory and local stored energy keep all relevant logic/interface rails in their valid range until reset/isolation acts. At a hard short, a 2 µF minimum local capacitor cannot be assumed to buy arbitrary supervisor latency. Undetected fast dips remain a gap unless a bounded detector/latch/hold-up solution or device transient specification covers them. Do not claim safety for every imaginable waveform.
4. **Hardware-gate external enables while reset/rail-invalid.** Require LED power enable LOW independent of stale MCU GP22 state; require GPIO bus isolation asserted independent of MCU execution. Preserve the manual RUN reset path and prevent contention/backfeed among reset outputs. If implementing an AND/inverter or multi-output supervisor, analyze its unpowered behavior and budget its current. **Do not silently drive the six module GPIO signals LOW in suspend**: isolation/safe state and module retention are separate proposed contracts requiring feature review.
5. **Restore only through cold/preconfiguration admission.** RESET/RUN must clear USB-device state and keep the pullup disconnected until a valid boot/configuration path is ready. The RP2350 SIE_CTRL PULLUP_EN and direct PHY pullup/override bits reset to zero; external-reset semantics support the intended disconnect, but actual HAL/bootloader state transitions still require integration tests. Do not retain the host's old configured-current permission across a power-fault restart.

These are concrete circuit connections/state requirements, not implemented pins hidden behind a test plan. They require an additional isolated reset revision before board adoption, with exact supervisor/gate BOM, netlist/ERC and a new USB-current ledger. This pass does not modify the otherwise reviewed netlist to invent that unqualified circuit.

### Bounded supervisor source check

The [TPS3890 datasheet](https://www.ti.com/lit/ds/symlink/tps3890.pdf) supplies ±1% threshold accuracy and bounded hysteresis, but its SENSE-fall propagation delays are **typical-only** (18 µs at 3.3 V in the stated test). A fixed TPS389033 nominal 3.17 V negative threshold can be as low as 3.1383 V, leaving only 3.3 mV above the 3.135 V RP2350 VREG_AVDD recommended minimum before dynamic/routing errors. It is not accepted here as a robust falling-rail solution. An adjustable version can place the nominal threshold better, but still requires a precision ratio/error budget and a guaranteed dynamic envelope.

The [TPS3808 Rev N](https://www.ti.com/lit/ds/symlink/tps3808.pdf) adjustable version has ±2% threshold error and up-to-3% hysteresis; it does not simply fit the narrow 3.135–3.267 V window. The [TPS3899](https://www.ti.com/lit/ds/symlink/tps3899.pdf) headline 0.5% is typical and its hysteresis is materially larger; no nominal-marketing substitution is made. This finite check ends here. **Missing guarantee:** a selected supervisor/reset path meeting the combined static and dynamic window, including supply collapse and short pulses. Obtain applicable vendor limits or select/qualify an appropriate detector/latch architecture in the next reset revision. No source-backed whole-reset guarantee is available from these three public candidates alone.

## Required restart behavior

| Event | Required response, independent of normal-startup timing |
|---|---|
| Cold attach / rapid unplug-replug | Hardware reset while rail-invalid; USB detached; LED enable disabled; module interfaces in reviewed isolation state. Bound raw/buck/LDO/core charge under preconfiguration allocation. |
| Output short and removal | Reset/isolation asserted during fault; do not release on elapsed 0.66 ms/4.49 ms. Wait for actual valid-rail qualification across ~330 ms/~2.24 s nominal recovery or longer. Permanent faults stay reset/off. |
| Partial dip without POR reinitialization | External RUN reset still forces a fresh boot. If pulse is shorter than the qualified detection envelope, safety is **not established**, rather than assuming POR helped. |
| Repeated brownout / thermal cycling | Requalify from the beginning; do not repeatedly reconnect USB or chatter LED power. Fault admission/latching must prevent uncontrolled retry loops. |
| Valid rail after reset | Boot at unconfigured current allocation; rebuild USB device state and wait for new host configuration before normal LED/module admission. A firmware setting does not inherit previous permission. |
| LED restart after reset/resume | Treat retained LED charge/data as unknown. Use the previously required discharge/known-state and rail-ready/black-transfer sequence, not a 2 ms wait followed by assumed-black pixels. |

The USB2.0 base specification §7.1.7.3 defines full-/low-speed detach detection with the pullup removed; its timing table lists 2–2.5 µs detect time. The proposed ≥10 ms valid-rail reset interval is deliberately longer but does not replace host re-enumeration. The [official USB2.0 package](https://www.usb.org/document-library/usb-20-specification) is archived at `../sources/usb20-base.pdf` with prior source provenance. Actual reconnect/reset/bootloader paths still need testing, including host asleep and reconnect during an existing suspend event.

## Firmware and current ownership

The earlier default-OFF divider study and later [deeper-suspend source study](../../maru60-deeper-suspend-feasibility-20261102/FEASIBILITY.md) do not implement this reset architecture or prove ≤2.5 mA suspend. At the existing conditional 80% efficiency screen, 0.829096 mA remains before USB pullup/MCU/flash/module loads. Subtracting 240 µA pullup and 50 µA flash standby leaves 539.096 µA; all six 39 kΩ GPIO HIGH subtract another ~517.950 µA, leaving ~21.147 µA. **No GPIO-state/function reduction is authorized by that arithmetic.** Added supervisor/gate/divider current must be added, not hidden in rounding.

The 10 nF choice changes startup charge timing, not the steady no-load-IQ term. No low-power MODE pin has appeared. Final firmware must explicitly separate attach, bootloader, preconfiguration, configured run, suspend, remote wake, bus reset and power-fault reboot. Module signal/power retention and user-visible recovery behavior remain a proposal for review, not an implemented or silently reduced feature set.

**Status:** mechanism and exact gaps documented; no hardware reset revision, flashing, measurement or production approval performed. Normal USB 4.4–5.5 V remains the working envelope; long 21 V abuse is separate.
