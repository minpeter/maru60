# PCB hardware license — decision document

**Status: open. This document records options and a recommendation; it does not
select or grant a license. The final choice is the owner's.**

Prepared 2026-11-11 for owner review. This is not legal advice; confirm the
choice with qualified counsel before publishing a license file or selling
hardware.

## 1. Why a decision is needed

The repository currently has two licenses for physical designs, but no license
for the PCB hardware design. Without an explicit PCB license, default copyright
applies: the public can read the files on GitHub, but has no clear permission to
copy, modify, manufacture, or distribute the PCB. That is inconsistent with the
stated intent of open hardware and blocks a clean pid.codes USB ID request (see
[USB-ID-DECISION.md](USB-ID-DECISION.md)).

## 2. Inventory: what is licensed, what is not

| Item | Files / scope | Current status | Redistributed third-party content? |
| --- | --- | --- | --- |
| Maru60 top and bottom case (housing) | `build_topcase_draft.py`, `export_topcase.py`, `render_topcase_draft.py`, `verify_topcase.py`, `models/maru60-hhkb-topcase*`, `images/topcase-*`, `evidence/topcase*`, `build_bottomcase_draft.py`, `verify_bottomcase.py`, `export_bottomcase.py`, `models/maru60-hhkb-bottomcase*`, `evidence/bottomcase*` | **CC BY-NC 4.0** (`LICENSE-topcase`), personal/non-commercial use only; commercial sale requires owner permission | No |
| Standalone wrist rest | Wrist-rest generator, model exports, documentation, renders; everything not listed under the cases | **CC BY 4.0** (`LICENSE`), commercial use permitted with attribution | No |
| PCB hardware design | KiCad projects, schematics, boards, local symbol/footprint libraries, PCB scripts, manufacturing data, PCB documentation | **Unselected** — no PCB license file; root `LICENSE` is not asserted as the PCB license | Yes, see rows below |
| ai03 MX_V2 hot-swap footprints | `pcb/engineering/third_party/MX_V2/MX-Hotswap-1U.kicad_mod`, `MX-Hotswap-7U.kicad_mod` | **MIT** (`pcb/engineering/third_party/MX_V2/LICENSE`, © 2017 ai03); upstream commit `0b379eebbeb66c7fd6e82e400b47958ad695614e` | Yes — retain copyright and permission notice |
| KiCad standard symbol/footprint libraries | External KiCad libraries used by the projects; local project libraries (`Maru60.pretty`, `MaruStudy.pretty`, `Protection_Study.pretty`, `*.kicad_sym`) | KiCad libraries are **CC BY-SA 4.0 with the KiCad library exception**; the exception means use in a design does not force the design under CC BY-SA. Local project libraries are original unless a file says otherwise | Only if library files are copied into the repo; keep notices |
| RP2350A Minimal reference elements | Archived experiment packets: U1 QFN thermal-via footprint, L1 inductor footprint, symbol pin definitions, selected 0402 land pattern, GPIO escape reference | **MIT** (© 2026 Raspberry Pi Ltd), per the archived `PROVENANCE.md` / `LICENSE.txt` | Yes — retain MIT notice |
| marbastlib Gateron comparison footprint | Archived experiment packets only; not selected for production | **CERN-OHL-P v2** (permissive), included unchanged | Yes — retain CERN-OHL-P notice |
| QMK firmware overlay | `pcb/firmware/qmk/**`, `pcb/firmware/via/**` | **GPL-2.0-or-later** (QMK); separate from the hardware license | Yes — QMK upstream notices |
| INKC Rule 60 V3 plate drawing and converted plate files | `third_party/inkc-rule60-v3/rule60-v3.dwg`, `build_plate.py`, `models/rule60-v3-hhkb-gas-plate*`, `evidence/plate-report.json` | **Not covered by either repository license**; redistributed on the creator's statement that the plate drawings are open source | Yes — separate provenance, not a Maru60 license grant |

The PCB design also uses component datasheets and vendor reference designs. Those
are not open-source licenses; record them as references, not as licensed design
content.

## 3. What "unselected" means in practice

- The PCB KiCad sources are copyrightable works. No one may reproduce, modify,
  manufacture, or sell them without permission, except for the limited rights
  GitHub's terms give to view and fork within GitHub.
- The MIT footprint files remain MIT regardless of the PCB license. They can be
  used, modified, and redistributed with their notice; they do not force the rest
  of the PCB to be MIT.
- The KiCad library exception avoids a share-alike obligation for merely using
  standard library symbols/footprints. It does not license modified library files
  that are redistributed; those remain CC BY-SA 4.0.
- The firmware is GPL-2.0-or-later. Distributing a board with firmware requires
  the corresponding firmware source, but the hardware design can carry a
  different license.

## 4. Comparison of candidate licenses

Ratings are for this project: KiCad sources, third-party MIT footprints, a
possible commercial sale, and an owner who says "open hardware."

| License | Type | Commercial sale | Derivatives | Source disclosure | Patent grant | Attribution / notices | Fit for this PCB |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **CERN-OHL-S-2.0** | Strongly reciprocal, hardware-specific | Yes | Must be under CERN-OHL-S-2.0 | Complete Source must be made available to recipients when products are made/distributed; includes CAD, scripts, docs, manufacturing files | Yes, express | Retain notices, mark changes, include license text | **Best fit** for a strongly open hardware project; clear source definition; MIT components can be included with notices |
| **CERN-OHL-W-2.0** | Weakly reciprocal, hardware-specific | Yes | Modifications to the design must be shared under W; a Larger Work may combine the design with proprietary parts | Source for the design; not necessarily the whole product | Yes, express | Retain notices, mark changes | Good if the owner wants commercial/proprietary products around an open core; weaker guarantee that derivatives stay open |
| **TAPR OHL** | Reciprocal, hardware-specific (2007) | Yes | Must be under TAPR OHL | Documentation and design files required | Yes, express | Retain notices; documentation and record-keeping duties | Workable but dated and less common; more process burden; weaker ecosystem familiarity |
| **CC BY-SA 4.0** | Reciprocal copyright license | Yes | Must be under CC BY-SA 4.0 | "Source" is not defined for hardware; share-alike scope is unclear for CAD/manufacturing | **No** — CC licenses do not grant patent rights | Attribution, license link, indicate changes | Not recommended for the PCB; acceptable for documentation/artwork only |
| **MIT** | Permissive | Yes | May be closed/proprietary | None | **No express patent grant** | Retain copyright and permission notice | Simple and compatible, but does not keep hardware open; weak patent position |
| **Apache-2.0** | Permissive, software-oriented | Yes | May be closed/proprietary | Notice/state-changes file; no source disclosure for derivatives | **Yes, express**, with patent-retaliation termination | NOTICE file, mark modified files, trademark rules | Good permissive fallback with a patent grant; not hardware-specific; Apache-2.0 is compatible with GPLv3, not GPLv2-only (QMK is GPL-2.0-or-later, so aggregation is workable) |

Notes:

- CERN-OHL-S/W and TAPR OHL are open-hardware licenses, not OSI-approved
  open-source licenses. "Open hardware" is the accurate label; do not call the
  PCB "OSI open source" unless an OSI-approved license is chosen.
- CERN-OHL-S-2.0 is used by open keyboard PCB projects (for example, Waffling60,
  which was reviewed but not copied). That is evidence of community familiarity,
  not a legal reason by itself.
- MIT and Apache-2.0 are copyright/software licenses applied to CAD files. They
  can work, but they do not define manufacturing-source obligations or hardware
  reciprocity.

## 5. Conflicts and risks to resolve before publishing

### 5.1 Top conflict: CC BY-NC 4.0 housing vs an open PCB license

The housing is CC BY-NC 4.0: non-commercial use only. Every candidate PCB
license above permits commercial use (CERN, TAPR, CC BY-SA, MIT, Apache). That
creates a product-level conflict, not a license-text conflict:

- Selling a bare PCB under an open PCB license is permitted by that license.
- Selling a complete Maru60 (PCB + housing) commercially is **not** permitted by
  the housing license without the owner's separate permission.
- A project-level claim of "open hardware" is inconsistent while a major
  physical design is NC. NC also fails the Open Source Hardware Definition's
  "no discrimination against fields of endeavor" test.

The PCB license cannot cure the housing NC. The owner must choose one of:

1. Keep the housing NC and treat the PCB as a separate open design; commercial
   sale of complete units requires a separate written permission or a commercial
   license from the owner.
2. Relicense the housing to CC BY 4.0 (or a CERN-OHL variant) if commercial
   reuse is intended.
3. Dual-license the housing: NC for the public, commercial terms on request.

Do not describe the whole repository as "open hardware" until this is resolved.

### 5.2 NC restrictions

"NonCommercial" is ambiguous at the edges (selling at cost, kits, commissioned
builds, business use, review units). It also blocks the most common reason a
small keyboard design gets manufactured. If the owner wants a commercial sale,
NC is the wrong default for the housing and should be revisited deliberately,
not worked around.

### 5.3 Attribution requirements

- CC BY 4.0 / CC BY-NC 4.0 / CC BY-SA 4.0: credit the creator, link the license,
  and indicate changes. The current root README and `docs/fabrication.md` do
  this for the housing and wrist rest; a PCB license must add the same for the
  PCB.
- CERN-OHL-S/W: retain copyright and license notices, identify modified files,
  and include the license text with the design.
- MIT: retain the copyright and permission notice in all copies or substantial
  portions. The ai03 MX_V2 `LICENSE` must stay next to the footprints.
- Apache-2.0: include a NOTICE file and state changes.
- Do not remove the INKC plate-drawing provenance or imply it is covered by the
  new PCB license.

### 5.4 Patent grants

- CERN-OHL-S/W, TAPR OHL, and Apache-2.0 include express patent grants. For a
  hardware design that may be sold, this is a meaningful advantage.
- MIT has no express patent grant. CC BY-SA 4.0 explicitly does not grant patent
  rights. Choosing either leaves a patent-risk gap that a contributor or buyer
  may raise.
- A patent grant is not a warranty that the design does not infringe; it is a
  promise not to assert certain patents against users of the licensed design.

### 5.5 Share-alike scope and third-party MIT files

- CERN-OHL-S's "Complete Source" is the clearest fit for KiCad: it covers the
  schematic, board, libraries, scripts, documentation, and manufacturing data.
- CC BY-SA's share-alike is copyright-based and does not define what "source"
  means for a physical product; it is a poor fit for hardware.
- The ai03 MX_V2 files can remain under MIT inside a CERN-OHL-S project. Keep
  their `LICENSE` and identify them as third-party components. Do not relicense
  them or remove their notices.
- The KiCad library exception means standard library use does not make the PCB
  CC BY-SA. If local libraries contain copied KiCad library content, document it
  and keep the CC BY-SA notice on those files.

### 5.6 Firmware and plate drawing

- The QMK overlay is GPL-2.0-or-later. It is a separate work from the hardware;
  distributing a board with firmware requires the corresponding firmware source.
  Do not apply the PCB license to QMK upstream files.
- The INKC plate drawing is not covered by either repository license. It needs
  its own provenance/permission statement; the PCB license must not imply it is
  covered.

## 6. Recommendation

**Recommended: CERN-OHL-S-2.0 for the Maru60 PCB hardware design**, with:

- the ai03 MX_V2 footprints and Raspberry Pi RP2350A Minimal elements retained
  under MIT with their notices;
- the QMK firmware overlay retained under GPL-2.0-or-later;
- the housing left under CC BY-NC 4.0 **only if** the owner accepts that
  complete-unit commercial sale needs separate permission;
- the INKC plate drawing kept outside the PCB license.

Reasons:

1. It is written for hardware and defines the source that must be shared
   (KiCad files, scripts, documentation, manufacturing data).
2. Strong reciprocity matches the stated open-hardware intent and prevents a
   manufacturer from taking the design closed.
3. It permits commercial sale, so it does not block a small run or a future
   product; it only requires that the design source remain open.
4. It includes an express patent grant, unlike MIT or CC BY-SA.
5. MIT-licensed footprints can be included with notices, so the existing
   third-party inventory is compatible.
6. It is familiar to open-hardware keyboard designers and reviewers.

Fallbacks, in order:

- **CERN-OHL-W-2.0** if the owner wants to allow proprietary products or
  closed add-on modules around an open core. This is the better choice if
  commercial partners will not accept strong reciprocity.
- **Apache-2.0** if the owner wants a permissive, OSI-approved license with a
  patent grant and is comfortable with closed derivatives.
- **MIT** only if maximum simplicity/compatibility matters more than keeping
  derivatives open; accept the missing express patent grant.
- **CC BY-SA 4.0** is not recommended for the PCB; use it only for
  documentation/artwork if desired.
- **TAPR OHL** is not recommended for a new KiCad project in 2026; it is older
  and has more process overhead than CERN-OHL.

This recommendation is not a selection. The owner must confirm the commercial
intent, the housing NC position, and the third-party notice plan before a
license file is published.

## 7. Exact files to add or change after the owner decides

### Add

- `pcb/LICENSE-PCB` — full text of the chosen license (recommended:
  CERN-OHL-S-2.0). Use the canonical license text, not a summary. If the owner
  prefers the existing root-license pattern, use root `LICENSE-PCB` instead and
  link to it consistently; do not maintain both.
- `pcb/LICENSE-PCB-NOTICE` (optional but recommended) — short scope statement:
  which files are covered, which are third-party MIT/GPL/CC, and where the
  housing/wrist-rest/plate licenses live.
- `pcb/firmware/USB-IDS.md` or `pcb/firmware/usb_ids.json` — only if the USB ID
  decision is implemented at the same time; see
  [USB-ID-DECISION.md](USB-ID-DECISION.md).

### Change

- `pcb/README.md` — replace the "License and design provenance" section
  (currently says the PCB license is unselected) with the chosen license, scope,
  and third-party notice links.
- `README.md` (root) — update the license paragraph so it names the PCB license
  and does not imply the root `LICENSE` covers the PCB.
- `docs/fabrication.md` — update "License and design history" with the PCB
  license, the housing NC caveat, and the third-party exceptions.
- `pcb/requirements.md` — change the "Open hardware license" row from "Exact
  license and provenance review pending" to the chosen license and date.
- `pcb/CURRENT.md` — add a one-line license status near the top so the current
  baseline is not read as unlicensed.
- `pcb/engineering/THIRD_PARTY_NOTICES.md` — add the PCB license notice, keep
  the ai03 MIT notice, and list the RP2350A Minimal / marbastlib / KiCad
  exceptions that apply to archived packets.
- `pcb/publication/a21-a22/README.md`, `pcb/publication/b70/README.md`,
  `pcb/publication/p3/README.md`, `pcb/publication/placement/README.md`,
  `pcb/publication/power-study/README.md`, `pcb/publication/silk/README.md`,
  `pcb/publication/v7/README.md` — replace the sentence "PCB hardware license
  selection remains unresolved" with a pointer to `pcb/LICENSE-PCB` and the
  scope/notice file.
- `pcb/engineering/third_party/MX_V2/LICENSE` — do not change the MIT text;
  only add a sibling note if the owner wants the scope explicit.

### SPDX headers

Add `SPDX-License-Identifier: CERN-OHL-S-2.0` (or the chosen identifier) to
first-party source files that can carry comments, for example:

- `pcb/engineering/footprint-check.mjs`
- `pcb/feasibility/validate_layout.mjs`
- `pcb/tools/export_material_graph.py`
- `tools/check_pcb_current.py`
- `tools/check_pcb_native.py`
- `tools/check_pcb_portable.py`
- `pcb/firmware/via/generate.py` — decide whether this generator is PCB design
  (CERN-OHL-S) or firmware tooling (GPL-2.0-or-later); do not guess. If it
  generates VIA definitions from QMK metadata, GPL-2.0-or-later is the safer
  default, with a note that the generated JSON is not the hardware license.

KiCad files have no comment syntax. Record the license in the title-block
Comment field and/or a repository `REUSE.toml` covering the CAD globs. At
minimum, cover the selected projects:

- `pcb/experiments/resume-20261109-relocated-expansion-zero-opens/pcb/maru60.kicad_pro`
- `pcb/experiments/resume-20261109-relocated-expansion-zero-opens/pcb/maru60.kicad_sch`
- `pcb/experiments/resume-20261109-relocated-expansion-zero-opens/pcb/maru60.kicad_pcb`
- `pcb/experiments/resume-20261105-ext-gpio26/pcb/maru60.kicad_pro`
- `pcb/experiments/resume-20261105-ext-gpio26/pcb/maru60.kicad_sch`
- `pcb/experiments/resume-20261105-ext-gpio26/pcb/maru60.kicad_pcb`

Do **not** add the PCB license header to QMK upstream files, the ai03 MIT
footprints, the KiCad standard libraries, or the INKC plate drawing.

## 8. Owner decision checklist

- [ ] Choose the license: CERN-OHL-S-2.0 (recommended), CERN-OHL-W-2.0,
      Apache-2.0, MIT, TAPR OHL, or another.
- [ ] Decide the housing position: keep CC BY-NC 4.0, relicense, or offer
      commercial permission.
- [ ] Confirm whether complete units will be sold commercially.
- [ ] Confirm the third-party notice plan (ai03 MIT, RP2350A MIT, marbastlib
      CERN-OHL-P, KiCad CC BY-SA + exception, INKC plate).
- [ ] Have counsel review the chosen license and the NC/open interaction.
- [ ] Then add `pcb/LICENSE-PCB`, update the files above, and only then request a
      pid.codes PID (which requires an open-source hardware project).

**The final choice is the owner's. This document does not make it.**
