# Recovered portable tests

These portable C tests and generators come from the recovered accepted-main archive. Run them through `candidate/run_host_checks.py`, which supplies this candidate's actual source, redirects all generated output to a fresh external directory, and evaluates only the original matrix model's main fixture. Do not run the historical matrix script directly: its old BS65/output-path assumptions are not current acceptance instructions.

The NEW startup/transport fixture is under `candidate/tests/startup_guard`. It is not a recovered copy of the earlier missing startup/independent suites. Qualification remains zero. Do not follow old instructions to merely flip qualification to one: enabled experiments require explicit synthetic contract macros in disposable host builds, and enabled hardware use requires real qualification evidence.
