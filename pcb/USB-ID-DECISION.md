# USB VID/PID — decision document

**Status: open. This document records options and a recommendation; it does not
allocate or select a USB ID. The final choice is the owner's.**

Prepared 2026-11-11 for owner review. This is not legal advice. USB-IF fees,
pid.codes policy, and VIA behavior change over time; verify the current terms
before acting.

## 1. Why this matters

A USB device is identified by a 16-bit Vendor ID (VID) and a 16-bit Product ID
(PID). The pair is what the host operating system, QMK, and the VIA app use to
recognize the keyboard. Shipping a non-unique or unallocated pair causes:

- collisions with other devices (wrong driver, wrong VIA definition, confusing
  device names);
- VIA loading a definition for a different keyboard;
- support and warranty confusion;
- non-compliance with USB-IF/pid.codes terms if the ID is not allocated to this
  product;
- a release that cannot be traced back to a specific product identity.

A VID/PID allocation is an identifier, not a safety, quality, or USB compliance
certification. Selling a USB device still requires the applicable regulatory and
USB compliance work.

## 2. Current state in this repository

| Location | Current value | Meaning |
| --- | --- | --- |
| `pcb/firmware/qmk/keyboards/maru60/rp2350/keyboard.json` | `usb.vid = 0xFEED`, `usb.pid = 0x6060`, `device_version = 0.0.1` | QMK prototype default; bench only |
| `pcb/firmware/qmk/keyboards/maru60/rp2350/config.h` | Default `FEED:6060`; optional `MARU60_PRIVATE_TEST_IDS` selects `0x1209:0x0001` (WKL) or `0x1209:0x0002` (HHKB) | Shared private test IDs; explicitly "NOT unique; MUST NOT be used on redistributed/sold/manufactured devices" |
| `pcb/firmware/via/generate.py` | Hardcodes `0x1209` and `0x0001`/`0x0002`; names the definitions "PRIVATE TEST - shared ID; not for manufacture" | Generated VIA definitions use the shared test IDs |
| `pcb/firmware/via/maru60-wkl-64.json` | `vendorId = 0x1209`, `productId = 0x0001` | WKL VIA definition, shared test ID |
| `pcb/firmware/via/maru60-hhkb-64.json` | `vendorId = 0x1209`, `productId = 0x0002` | HHKB VIA definition, shared test ID |
| `pcb/firmware/README.md` | States that default prototype IDs and optional shared private-test IDs are not production allocations | Correct warning; no release ID exists yet |

The current `0x1209:0x0001` and `0x1209:0x0002` pairs are **shared private test
IDs**. They are not unique to Maru60, are not production allocations, and must
not appear in any redistributed, sold, or manufactured device. The same applies
to `FEED:6060`: it is a QMK bench convention, not a product identity.

## 3. Options

### Option A — pid.codes PID under VID `0x1209` (open-source hardware)

`0x1209` is the Open Source Hardware VID administered by
[pid.codes](https://pid.codes/). A project requests a PID through the pid.codes
registry (historically a GitHub pull request), publishes its open-source
hardware design, and receives a PID assigned to that project.

- **Cost:** no fee for the PID.
- **Lead time:** review/assignment varies; typically days to weeks, depending on
  registry activity and whether the project documentation is complete.
- **Pros:** free; recognized open-hardware identity; unique PID; works with QMK
  and VIA; no USB-IF membership; appropriate for a small open keyboard.
- **Cons:** requires an open-source hardware project and a public source link;
  `0x1209` is a shared VID, so the OS may show a generic manufacturer; the
  project must follow pid.codes terms; not suitable if the design will be
  closed-source; PID is tied to the project, not freely transferable.
- **Prerequisite:** the PCB license decision must be resolved first. pid.codes
  expects an open-source hardware design; an unlicensed PCB or a closed license
  is not eligible. See [LICENSE-DECISION.md](LICENSE-DECISION.md).

### Option B — own VID from USB-IF

A company can join USB-IF, obtain its own Vendor ID, and assign Product IDs
itself.

- **Cost:** USB-IF membership dues are in the thousands of US dollars per year
  (historically around US$6,000/year for the relevant membership level; verify
  the current fee schedule). Budget for compliance/testing separately.
- **Lead time:** application, membership approval, and VID assignment typically
  take days to weeks; testing/certification adds more.
- **Pros:** unique VID owned by the project; full control of PIDs; can be used
  with a closed-source design; professional identity; no dependency on
  pid.codes policy.
- **Cons:** recurring cost and administration; overkill for a small open-source
  keyboard; membership must be maintained; a VID does not by itself make the
  product USB-compliant.
- **When to choose:** the owner intends commercial sale with a closed design, or
  needs a vendor identity independent of an open-hardware registry.

### Option C — prototype-only `FEED:6060`

`0xFEED` is a QMK convention, not a USB-IF-assigned VID; `0x6060` is a QMK test
PID. The pair is useful for bring-up and bench testing.

- **Cost/lead time:** zero.
- **Pros:** familiar to QMK; no registry work; fine for a board that never leaves
  the bench.
- **Cons:** not unique; not a product identity; may collide with other QMK
  devices; not appropriate for distribution, sale, or manufacture; VIA
  definitions may conflict.
- **Verdict:** keep for bench/prototype builds only. Do not ship.

### Option D — shared private test `0x1209:0x0001` / `0x1209:0x0002`

These are pid.codes test PIDs used by multiple projects for development.

- **Cost/lead time:** zero.
- **Pros:** lets VIA recognize a development build without waiting for an
  allocation.
- **Cons:** not unique; explicitly not for redistribution, sale, or manufacture;
  another project using the same pair can make VIA load the wrong definition;
  OS descriptor caches and support logs become ambiguous; shipping them can
  violate pid.codes terms.
- **Verdict:** development only. Remove from release builds and release
  documentation.

## 4. Comparison

| Option | Unique? | Cost | Lead time | Open-source requirement | Suitable for sale? | Best use |
| --- | --- | --- | --- | --- | --- | --- |
| pid.codes `0x1209` PID | Yes, per allocation | Free | Days–weeks | Yes | Yes, if design stays open and terms are met | Recommended for Maru60 |
| Own USB-IF VID | Yes | Membership + compliance | Weeks | No | Yes | Commercial/closed design |
| `FEED:6060` | No | Free | None | No | **No** | Bench/prototype |
| `0x1209:0001/0002` shared test | No | Free | None | Registry test use | **No** | Temporary development |

## 5. Recommendation

**Recommended path: request a pid.codes PID under VID `0x1209` for Maru60, and
keep `FEED:6060` for bench-only builds. Do not ship `0x1209:0001` or
`0x1209:0002`.**

Details:

1. **Resolve the PCB license first.** pid.codes requires an open-source hardware
   project. If the owner chooses CERN-OHL-S-2.0 (the recommendation in
   [LICENSE-DECISION.md](LICENSE-DECISION.md)), the project is eligible. If the
   owner chooses a closed or NC-only license, pid.codes is not the right path;
   use an own USB-IF VID instead.
2. **Request one PID per VIA-visible product variant, or one PID for the family
   with a combined VIA definition.** The current WKL and HHKB definitions are
   separate JSON files keyed by PID. If they keep separate definitions, request
   two PIDs (WKL and HHKB) with a short justification; if pid.codes prefers one
   PID per project, merge the definitions into one VIA JSON with both layouts
   and use one PID. Do not ship two variants under the same PID with different
   VIA definitions.
3. **Keep `FEED:6060` as an explicit bench build option**, not the default
   release identity. A release build must fail or warn if it still contains
   `FEED:6060` or the shared test IDs.
4. **Record the allocation.** Put the pid.codes URL, allocation date, and the
   exact VID/PID in the firmware README and the release checklist.
5. **If commercial sale with a closed design is the goal**, skip pid.codes and
   obtain an own USB-IF VID. Do not use a resold/rented VID without checking its
   terms; VID licenses are generally non-transferable.

This is a recommendation, not an allocation. The owner must choose the path and
complete the registry/USB-IF process.

## 6. Exact files to change after the owner decides

### Firmware identity

- `pcb/firmware/qmk/keyboards/maru60/rp2350/config.h`
  - Remove the `MARU60_PRIVATE_TEST_IDS` block that selects
    `0x1209:0x0001/0x0002`.
  - Add the allocated `VENDOR_ID` / `PRODUCT_ID` values, or a
    `MARU60_ALLOCATED_IDS` block with the allocation URL in a comment.
  - Keep a clearly named `MARU60_PROTOTYPE_IDS` opt-in for `FEED:6060` bench
    builds; make the release default the allocated IDs.
  - Add a compile-time guard that rejects `0x1209:0x0001`, `0x1209:0x0002`, and
    `FEED:6060` in a release build.
- `pcb/firmware/qmk/keyboards/maru60/rp2350/keyboard.json`
  - Set `usb.vid` / `usb.pid` to the allocated values (or keep the prototype
    values only if `config.h` is the single release override; do not maintain
    two conflicting release sources).
  - Bump `usb.device_version` for the first allocated release (for example
    `1.0.0`), and keep prototype builds at `0.0.x`.
  - If the VIA definitions are merged to one PID, update the layout metadata and
    the VIA generator together; do not leave a stale second definition.
- `pcb/firmware/via/generate.py`
  - Remove the hardcoded `0x1209` / `0x0001` / `0x0002` values.
  - Read the IDs from one source of truth (recommended:
    `pcb/firmware/usb_ids.json`, or `keyboard.json` if it is authoritative).
  - Replace the "PRIVATE TEST - shared ID; not for manufacture" names with the
    allocated product names.
- `pcb/firmware/via/maru60-wkl-64.json`
  - Regenerate with the allocated `vendorId` / `productId` and product name.
- `pcb/firmware/via/maru60-hhkb-64.json`
  - Regenerate with the allocated `vendorId` / `productId` and product name.

### Documentation

- `pcb/firmware/README.md` — replace the "not production allocations" warning
  with the allocated ID, the pid.codes/USB-IF path, the bench-only `FEED:6060`
  rule, and the release gate.
- `pcb/README.md` — add a short "USB identity" note near the license/provenance
  section: allocated VID/PID, bench IDs, and a link to this decision.
- `pcb/requirements.md` — add a "USB VID/PID" row with the allocated value and
  status; keep the existing VIA row separate.
- `pcb/CURRENT.md` — state that the current prototype uses bench/test IDs and is
  not a production USB identity.
- `docs/pcb-validation.md` — add a release-gate item: inspect the USB
  descriptor, confirm the allocated VID/PID, confirm no `FEED:6060` or
  `0x1209:0001/0002` in the release UF2, and confirm VIA loads the matching
  definition.
- `pcb/firmware/via/*.json` — the generated files are the VIA-visible identity;
  keep them in sync with the firmware and document that they are generated.

### Recommended new single source of truth

- `pcb/firmware/usb_ids.json` — one record per variant:
  `{ "variant": "wkl", "vid": "0x1209", "pid": "0x....", "allocation": "https://pid.codes/1209/..../", "status": "allocated" }`.
- `tools/check_usb_ids.py` — a read-only check that compares `config.h`,
  `keyboard.json`, `via/generate.py`, and the generated VIA JSONs against
  `usb_ids.json`, and fails on `FEED:6060` or `0x1209:0001/0002` in a release
  configuration. This prevents the current drift where multiple files hardcode
  the same test IDs.

### Do not change

- `pcb/engineering/third_party/MX_V2/**` — no USB identity content.
- QMK upstream files — keep their GPL-2.0-or-later notices; the USB ID is a
  Maru60 overlay value, not an upstream change.
- `pcb/firmware/qmk/patches/**` — unless the release guard needs a patch; if so,
  add a new hash-guarded patch rather than editing an existing one silently.

## 7. Release checklist

- [ ] PCB license resolved and pid.codes eligibility confirmed (or own VID
      obtained).
- [ ] PID allocation recorded with URL and date.
- [ ] `config.h`, `keyboard.json`, `via/generate.py`, and both VIA JSONs agree.
- [ ] Release build rejects `FEED:6060` and `0x1209:0001/0002`.
- [ ] USB descriptor read back on hardware: VID/PID, product string, serial
      behavior, and device version match the release record.
- [ ] VIA app loads the correct WKL or HHKB definition; remapping and
      persistence are tested (still an open qualification item).
- [ ] Release notes state the allocation and do not call the device
      "PRIVATE TEST".
- [ ] No shared test ID appears in a manufactured, sold, or redistributed
      binary.

## 8. Owner decision checklist

- [ ] Choose pid.codes `0x1209` (recommended for open hardware) or own USB-IF
      VID (commercial/closed design).
- [ ] Decide one PID for the family or one PID per WKL/HHKB variant, based on
      whether the VIA definitions stay separate.
- [ ] Confirm the PCB license is compatible with the chosen path.
- [ ] Approve the bench-only `FEED:6060` policy and the release guard.
- [ ] Then update the files above and record the allocation.

**The final choice is the owner's. This document does not allocate a USB ID.**
