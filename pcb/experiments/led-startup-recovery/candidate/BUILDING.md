# Future full builds, not executed

Use the new candidate overlay, not the immutable baseline. A complete disposable QMK checkout at `431ed9ade0684e98a66eabc949563c3be8f446e8`, exact recursive submodules, and an authorized ARM toolchain plus QMK CLI/Python requirements are needed. They are absent locally. Do not fetch or install them implicitly.

For an already prepared clean checkout, review exact Git/submodule identities and both patch tools' dry runs before applying `firmware/qmk/apply_via_schema_patch.py` and `apply_report_sync_patch.py`. Copy only `candidate/firmware/qmk/keyboards/maru60/rp2350` to the checkout's `keyboards/maru60/rp2350`; reject an existing target rather than merging stale files. Verify every copied source hash against `SOURCE-STATUS.json`.

Compile WKL `maru60/rp2350:via` and HHKB `maru60/rp2350:via_hhkb` sequentially with no qualification or settling override, default prototype IDs, and suspend experiment disabled. Retain full compiler logs, inspect actual full key/underglow translation-unit flags/preprocessing for qualification zero, and hash linked ELF/UF2 outputs. Historical ARM logs from the recovered archive do not validate this new code.

Host stub/extracted-function compilation is not this acceptance step. Even a successful full ARM build would not prove real IRQ/task behavior, USB, DMA/PIO waveforms, rail/current/timing, or hardware qualification. No flashing or enabled-release instructions are supplied.
