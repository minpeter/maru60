# Maru60

Maru60 is an experimental HHKB housing for Rule 60 V3 internals with an
integrated honeycomb wrist rest. This repository also includes the standalone
Rule 60 V3 wrist rest and an unfinished RP2350A PCB design.

| Start here | Contents |
| --- | --- |
| [Housing](docs/housing.md) | Build and verify matching top/bottom variants; print files, fit and assembly |
| [Standalone wrist rest](docs/wrist-rest.md) | Current tight-fit downloads, reproduction and print guidance |
| [PCB current state](pcb/CURRENT.md) | Strict baseline, development prototype and unresolved qualification |
| [PCB validation](docs/pcb-validation.md) | Reproduce native CAD, portable firmware and power checks |
| [PCB order package](pcb/order/README.md) | Gerbers, JLCPCB BOM and placement file for the order candidate, with ordering steps |
| [PCB fabrication draft](pcb/fabrication/README.md) | Earlier BOM, CPL and Gerbers for the 0/0 prototype; superseded by the order package |
| [Detailed fabrication reference](docs/fabrication.md) | Complete design history, measurements, hardware and plate guidance |

Install [uv](https://docs.astral.sh/uv/), then run from the repository root:

```sh
uv sync --locked
uv run python -m maru60.pipeline --board ph60-rev3
uv run python -m unittest discover -s tests
uv run tools/check_pcb_current.py
```

The housing pipeline builds and verifies both cases in a variant-specific
folder under `build/`. Add `--strike-inserts` for the upper insert trial,
`--catches luban32` for the purchased LUBAN 32 mm catches with inserts (assumed
widths, caliper first) or `--no-battery-bay` for the wired lower case. Published `models/` and `evidence/`
change only with `--publish`; review [housing guidance](docs/housing.md) first.
CAD checks do not establish physical fit or strength. The custom PCB has an
[order candidate](pcb/order/README.md) for a first prototype run; it has **not
been built or qualified on hardware**.

The standalone wrist rest uses [CC BY 4.0](LICENSE); the Maru60 cases use
[CC BY-NC 4.0](LICENSE-topcase). See the [full license and design history](docs/fabrication.md#license-and-design-history)
for third-party exceptions and attribution.

<details>
<summary>Earlier README section links</summary>

<a id="rule-60-v3-honeycomb-wrist-rest--no-extra-hardware"></a>
[Rule 60 V3 Honeycomb Wrist Rest — No Extra Hardware](docs/fabrication.md#rule-60-v3-honeycomb-wrist-rest--no-extra-hardware) · <a id="download-and-print"></a>
[Download and print](docs/fabrication.md#download-and-print) · <a id="fit-and-assembly"></a>
[Fit and assembly](docs/fabrication.md#fit-and-assembly) · <a id="slicing"></a>
[Slicing](docs/fabrication.md#slicing) · <a id="reproduce-and-continue-designing"></a>
[Reproduce and continue designing](docs/fabrication.md#reproduce-and-continue-designing) · <a id="verification-and-limitations"></a>
[Verification and limitations](docs/fabrication.md#verification-and-limitations) · <a id="maru60-hhkb-top-case-with-integrated-wrist-rest-experimental"></a>
[Maru60 HHKB top case with integrated wrist rest (experimental)](docs/fabrication.md#maru60-hhkb-top-case-with-integrated-wrist-rest-experimental) · <a id="printing"></a>
[Printing](docs/fabrication.md#printing) · <a id="interface-spec-and-pcb-boards"></a>
[Interface spec and PCB boards](docs/fabrication.md#interface-spec-and-pcb-boards) · <a id="reproduce"></a>
[Reproduce](docs/fabrication.md#reproduce) · <a id="optional-upper-strike-inserts-canot-od35--l3-trial"></a>
[Optional upper strike inserts (CANOT OD3.5 × L3 trial)](docs/fabrication.md#optional-upper-strike-inserts-canot-od35--l3-trial) · <a id="measurements-and-evidence"></a>
[Measurements and evidence](docs/fabrication.md#measurements-and-evidence) · <a id="verification-and-limitations-1"></a>
[Verification and limitations](docs/fabrication.md#verification-and-limitations-1) · <a id="maru60-hhkb-bottom-case-draft"></a>
[Maru60 HHKB bottom case (draft)](docs/fabrication.md#maru60-hhkb-bottom-case-draft) · <a id="local-m2-insert-mount-study-not-released"></a>
[Local M2 insert-mount study (not released)](docs/fabrication.md#local-m2-insert-mount-study-not-released) · <a id="purchased-32-mm-catches--canot-inserts--separate-local-trial"></a>
[Purchased 32 mm catches / CANOT inserts — separate local trial](docs/fabrication.md#purchased-32-mm-catches--canot-inserts--separate-local-trial) · <a id="photo-refined-sculpted-alternative-c-derived-still-experimental"></a>
[Photo-refined sculpted alternative (C-derived, still experimental)](docs/fabrication.md#photo-refined-sculpted-alternative-c-derived-still-experimental) · <a id="hhkb-gasket-plate-inkc-drawing"></a>
[HHKB gasket plate (INKC drawing)](docs/fabrication.md#hhkb-gasket-plate-inkc-drawing) · <a id="pcb"></a>
[PCB](docs/fabrication.md#pcb) · <a id="off-the-shelf-board-ph60-rev3-multi"></a>
[Off-the-shelf board: PH60 Rev.3 Multi](docs/fabrication.md#off-the-shelf-board-ph60-rev3-multi) · <a id="maru60s-own-pcb-rp2350a-work-in-progress"></a>
[Maru60's own PCB (RP2350A, work in progress)](docs/fabrication.md#maru60s-own-pcb-rp2350a-work-in-progress) · <a id="license-and-design-history"></a>
[License and design history](docs/fabrication.md#license-and-design-history)

</details>
