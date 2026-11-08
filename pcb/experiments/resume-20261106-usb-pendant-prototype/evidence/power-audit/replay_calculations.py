#!/usr/bin/env python3
"""Portable arithmetic-only replay. Run: python3 replay_calculations.py.

Reads sibling calculations.json; writes sibling calculation-replay-result.json.
No CAD, vendor files, third-party modules or original audit.py are loaded.
This checks recorded arithmetic, NOT authenticity/applicability of source values,
CAD connectivity, effective component parameters, or active-loop stability.
"""
from fractions import Fraction
from itertools import product
from pathlib import Path
import hashlib
import json
import math

F = Fraction
ROOT = Path(__file__).resolve().parent
INPUT = ROOT / 'calculations.json'
# Source values: TI TPS6293x SLUSEA4D Rev D, pp.6-7 (VREF, ISS),
# pp.21-23 (SS/timing), pp.29-32 (divider/LC equations); board nominal labels.
# These are recorded audit inputs, not independently requalified by this script.
REFERENCE = {'25C': ('0.792', '0.808'), '0_to_85C': ('0.788', '0.812'),
             'minus40_to_150C': ('0.784', '0.816')}
TOP_OHMS, BOTTOM_OHMS = F(40000), F(10000)
INITIAL_TOLERANCE = F('0.001')
# Deliberate symmetric magnitude assumption. Datasheet has positive MAX only.
LEAK_MAGNITUDE_A = F('0.00000015')
CSS_F, CSS_TOLERANCE = F('100e-9'), F('0.10')
ISS_MIN_A, ISS_TYP_A, ISS_MAX_A = F('4.5e-6'), F('5.5e-6'), F('6.5e-6')
VREF_TYP_V = F('0.8')
VIN_V, VOUT_V, L_H, F_HZ = F(5), F(4), F('4.7e-6'), F(500000)
IC_RATING_A, COUT_NOMINAL_F = F(2), F('49.7e-6')
TARGET_K, T_OFF_TYP_S, IDEAL_MAX_DUTY = F('0.4'), F('140e-9'), F('0.98')
ASSUMPTIONS = [
    'Regulated DC divider: initial resistor tolerance only; excludes TCR, aging, board leakage, ripple and distribution drop.',
    'Signed +/-0.15uA leakage is a conservative magnitude assumption, not a quoted signed datasheet interval.',
    'SS calculation uses nominal capacitor +/-10% only, reference extremes and charge-current extremes; excludes C derating and actual startup dynamics.',
    'Single ideal CCM point: 5V at buck VIN, 4V output, nominal 4.7uH/500kHz; 2A is IC rating, not verified board load.',
    '49.7uF is a nominal sum, not qualified effective capacitance; capacitive ripple is not an upper bound.',
    'Timing uses typical off-time and ideal duty arithmetic; no measured dropout, active transient or stability result.'
]
actual = json.loads(INPUT.read_text())
checks = []
def check_numeric(path, observed, expected):
    # JSON holds the original float serialization. Both exact float equality and
    # a documented tight numeric tolerance are checked, not rounded reporting text.
    e = float(expected)
    assert isinstance(observed, (int, float)) and not isinstance(observed, bool), path
    assert math.isfinite(observed) and observed == e, (path, observed, e)
    assert math.isclose(observed, e, rel_tol=1e-14, abs_tol=1e-15), path
    checks.append(path + ': numeric')
def check_fraction(path, observed, expected):
    assert set(observed) == {'exact', 'decimal'}, path
    assert F(observed['exact']) == expected, (path, observed, str(expected))
    assert observed['exact'] == str(expected), path
    checks.append(path + ': exact rational')
    check_numeric(path, observed['decimal'], expected)

assert set(actual) == set(REFERENCE) | {'soft_start', 'nominal_design_screen'}
for name, endpoints in REFERENCE.items():
    section = actual[name]
    # Independent nodal divider equation, Vout = Vref + Rt*(Vref/Rb + Ileak).
    cases = []
    for ref, top_scale, bottom_scale, sign in product(map(F, endpoints),
            [1-INITIAL_TOLERANCE, 1+INITIAL_TOLERANCE],
            [1-INITIAL_TOLERANCE, 1+INITIAL_TOLERANCE], [-1, 1]):
        rt, rb, leak = TOP_OHMS*top_scale, BOTTOM_OHMS*bottom_scale, sign*LEAK_MAGNITUDE_A
        cases.append({'vref': ref, 'rt': rt, 'rb': rb,
                      'assumed_signed_leak_A': leak, 'vout': ref + rt*(ref/rb+leak)})
    assert len(section['corners']) == len(cases) == 16
    for i, (recorded, computed) in enumerate(zip(section['corners'], cases)):
        assert set(recorded) == set(computed)
        for field, value in computed.items():
            check_fraction(f'{name}.corners[{i}].{field}', recorded[field], value)
    check_numeric(name+'.min', section['min'], min(x['vout'] for x in cases))
    check_numeric(name+'.max', section['max'], max(x['vout'] for x in cases))
    no_leak = [x['vref'] + x['rt']*x['vref']/x['rb'] for x in cases]
    check_fraction(name+'.without_leak_min', section['without_leak_min'], min(no_leak))
    check_fraction(name+'.without_leak_max', section['without_leak_max'], max(no_leak))

# Evaluate all 2x2x2 soft-start corners, rather than directly picking extrema.
ss_cases = [c*v/i for c,v,i in product(
    [CSS_F*(1-CSS_TOLERANCE), CSS_F*(1+CSS_TOLERANCE)],
    map(F, REFERENCE['minus40_to_150C']), [ISS_MIN_A, ISS_MAX_A])]
soft = {'nominal_s': CSS_F*VREF_TYP_V/ISS_TYP_A,
        'conditional_min_s': min(ss_cases), 'conditional_max_s': max(ss_cases)}
for key, val in soft.items():
    check_fraction('soft_start.'+key, actual['soft_start'][key], val)

# Ideal ON-state inductor slope times ON duration (independent derivation).
duty = VOUT_V/VIN_V
ripple = (VIN_V-VOUT_V)/L_H * duty/F_HZ
screen = {
    'delta_i_A': ripple,
    'K_at_IC_2A_rating': ripple/IC_RATING_A,
    'peak_at_IC_rating_A': IC_RATING_A + ripple/2,
    'capacitive_ripple_nominal_only_V': ripple/(8*F_HZ*COUT_NOMINAL_F),
    'L_at_K_0p4_at_IC_rating_H': (VIN_V-VOUT_V)*duty/(F_HZ*TARGET_K*IC_RATING_A),
    'minimum_Vin_no_foldback_ideal_V': VOUT_V/(1-F_HZ*T_OFF_TYP_S),
    'minimum_Vin_98percent_ideal_V': VOUT_V/IDEAL_MAX_DUTY
}
for key, val in screen.items():
    check_fraction('nominal_design_screen.'+key, actual['nominal_design_screen'][key], val)
check_numeric('nominal_design_screen.Cout_nominal_only_uF',
              actual['nominal_design_screen']['Cout_nominal_only_uF'], COUT_NOMINAL_F*10**6)
result = {
    'status': 'PASS_ARITHMETIC_ONLY',
    'qualification': 'No CAD/source requalification or active-model/stability approval.',
    'input_file': INPUT.name,
    'input_sha256': hashlib.sha256(INPUT.read_bytes()).hexdigest(),
    'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'feedback_corners_recomputed': 48,
    'soft_start_corners_recomputed': 8,
    'checks_passed': len(checks),
    'assumptions': ASSUMPTIONS,
    'checks': checks
}
(ROOT/'calculation-replay-result.json').write_text(json.dumps(result, indent=2)+'\n')
print(f"PASS_ARITHMETIC_ONLY: {len(checks)} checks, 48 feedback corners, 8 SS corners; no stability qualification.")
