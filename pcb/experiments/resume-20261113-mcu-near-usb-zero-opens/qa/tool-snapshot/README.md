# Original validation sources

The manifest now resolves changed shared tools and regression tests to exact
historical sources. Every relocated file retains its original recorded SHA-256.
Signal-integrity tools already archived in `../signal-integrity/source/` are
referenced there. Geometry, copper-material and PDN tools and regression tests
are preserved in this directory.

The PDN source and two tests were reconstructed from the earlier and current
versions and accepted only after their bytes matched the original manifest
hashes. No historical simulation output or expected hash was changed.

These files record provenance, not a standalone environment. Later cutout,
pad-contact, reverse-LED and population improvements remain in the shared tools.
