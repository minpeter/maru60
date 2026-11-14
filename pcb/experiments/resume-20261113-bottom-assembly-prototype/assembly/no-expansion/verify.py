#!/usr/bin/env python3
"""Check exported population and exercise the real pre-init function with GPIO mocks."""
import argparse
import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent.parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    out = parser.parse_args().output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    policy = json.loads((BASE / "design/assembly-policy.json").read_text())
    snapshot = json.loads((BASE / "evidence/cost-review-20261114/parts-snapshot.json").read_text())
    old_refs = {ref for part in snapshot["parts"] for ref in part["refs"]}
    excluded = set(policy["exclude_from_assembly"])
    expected = old_refs - excluded
    bom = list(csv.DictReader((HERE / "bom-review.csv").open()))
    bom_refs = [ref for row in bom for ref in row["Designator"].split(",")]
    assert len(bom_refs) == len(set(bom_refs)) == 319 and set(bom_refs) == expected
    variants = {}
    for name in ("split", "2u"):
        pos = list(csv.DictReader((HERE / f"placements-native-{name}.csv").open()))
        assert len(pos) == 319 and {row["Reference"] for row in pos} == expected
        assert all(row["Layer"] == "B.Cu" for row in pos)
        variants[name] = {row["Reference"]: row for row in pos}
    differences = sorted(ref for ref in expected if variants["split"][ref] != variants["2u"][ref])
    assert differences == ["LED14", "LED15"]
    for name, sha in policy["source_inputs"].items():
        assert hashlib.sha256((BASE / name).read_bytes()).hexdigest() == sha
    actual = (HERE / "firmware/maru60.c").read_text()
    match = re.search(r"void keyboard_pre_init_kb\(void\)\s*\{(.*?)\n\}", actual, re.S)
    assert match
    function = match.group(0)
    # Independent requirement: only six unpopulated GPIOs plus existing RGB
    # control/data outputs may be touched; all must be LOW at the user hook.
    prefix = """#include <assert.h>
#include <stdint.h>
static uint32_t levels = 0xffffffffU, outputs, touched, hook_count;
static const uint32_t unused = (1U<<3)|(1U<<10)|(1U<<24)|(1U<<25)|(1U<<26)|(1U<<27);
static const uint32_t rgb = (1U<<20)|(1U<<21)|(1U<<22);
static void gpio_write_pin_low(unsigned pin) {
    assert(pin < 30); levels &= ~(1U<<pin); touched |= 1U<<pin;
}
static void gpio_set_pin_output(unsigned pin) {
    assert(pin < 30);
    if (unused & (1U<<pin)) assert(!(levels & (1U<<pin)));
    outputs |= 1U<<pin; touched |= 1U<<pin;
}
static void keyboard_pre_init_user(void) {
    assert(touched == (unused|rgb)); assert(outputs == (unused|rgb));
    assert(!(levels & (unused|rgb))); ++hook_count;
}
""" + "\n".join(f"#define GP{i} {i}" for i in range(30)) + "\n"
    suffix = "\nint main(void) { keyboard_pre_init_kb(); assert(hook_count == 1); return 0; }\n"
    controls = {
        "actual": function,
        "missing_gpio26_preload": function.replace("gpio_write_pin_low(GP26);", ""),
        "accidental_row3_gpio29": function.replace("GP26", "GP29"),
    }
    results = []
    for name, body in controls.items():
        source, binary = out / (name + ".c"), out / name
        source.write_text(prefix + body + suffix)
        subprocess.run(["cc", "-std=c11", "-Wall", "-Wextra", "-Werror", str(source), "-o", str(binary)], check=True)
        result = subprocess.run([str(binary)], cwd=out, capture_output=True, text=True)
        (out / (name + ".log")).write_text(result.stdout + result.stderr)
        assert (result.returncode == 0) == (name == "actual"), name
        results.append({"case": name, "exit": result.returncode, "expected_result": True})
    report = {"pass": True, "bom_rows": len(bom), "placements_each": len(expected),
              "same_refs_in_bom_and_both_placements": True, "omitted_refs": sorted(excluded),
              "backspace_only_placement_differences": differences, "cad_hashes_unchanged": True,
              "preinit_host_results": results, "scope": "Host GPIO calls mocked; full ARM builds and physical behavior are separate checks",
              "firmware_sha256": hashlib.sha256((HERE / "firmware/maru60.c").read_bytes()).hexdigest()}
    (out / "result.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
