# Recovered V7 warning review

Source: exact selected board 7c23d6ea, freshly checked with KiCad 9.0.2. All 92 warning records have unique source-bound identities and explicit dispositions in JSON/CSV: 28 text-height, 31 silk overlap, 26 silk-over-mask, 5 dangling tracks and 2 dangling vias. None is waived or marked electrically qualified.

The seven electrical warnings were freshly re-extracted from the actual board using read-only native immediate track/pad connectivity. This is not a complete all-net geometric graph replay or an SI/PDN proof. The native source bytes are unchanged.

Highest-consequence review items remain the USB_DM branch/connector return, retained C128 supply stub with conditional PDN resonance, and BUCK_FB dead arm. Do not delete active junctions or interpret reduced warning count/capacitance as better stability. The two GND stubs, VBUS via and +4V_REG stub have explicit preservation requirements as well.

Typography and intact-logo candidates are handled in separate experiments, including complete ink/mask geometry and visual association. The original 108-warning packet is missing; this is a new 92-warning register for the exactly recovered selected board, not a recreated historical packet.

The reused C128 PDN and BUCK_FB findings come from recovered source-bound archives whose native input board 8a4ff6a6 matches the recovered chain. Their numerical assumptions and qualification limits remain in those packets; no new physical simulation is asserted here.
