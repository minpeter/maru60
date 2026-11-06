# Completed frozen nine-pair GPIO25 study

This supersedes the early-stop status in resume-audit/REPORT.md. All nine frozen via pairs were tested. No source edits or candidate selection.

| Case | Native opens/warnings/parity | Exact remote witnesses | Exact unchanged foreign-track reference loss |
|---|---|---|---|
| j0-b0 | 8/38/0 | 10 | COL14 9820d4ee-e433-4a88-934a-98eda993e59e |
| j0-b1 | 8/38/0 | 10 | COL14 9820d4ee-e433-4a88-934a-98eda993e59e |
| j0-b2 | 8/38/0 | 10 | COL14 9820d4ee-e433-4a88-934a-98eda993e59e |
| j1-b0 | 8/38/0 | 10 | COL14 9820d4ee-e433-4a88-934a-98eda993e59e |
| j1-b1 | 8/38/0 | 10 | COL14 9820d4ee-e433-4a88-934a-98eda993e59e |
| j1-b2 | 8/38/0 | 10 | COL14 9820d4ee-e433-4a88-934a-98eda993e59e |
| j2-b0 | 8/38/0 | 10 | COL14 9820d4ee-e433-4a88-934a-98eda993e59e |
| j2-b1 | 8/38/0 | 10 | COL14 9820d4ee-e433-4a88-934a-98eda993e59e |
| j2-b2 | 8/38/0 | 10 | COL14 9820d4ee-e433-4a88-934a-98eda993e59e |

Every native gate compares all 38 warning records exactly to the source, not only their count. All fresh boards were refilled by the unmodified build script. j0-b0 reuses the byte-identical previously completed board and native result; its foreign-reference regression is fresh.

Remote witnesses are exact rational source-interior/candidate-exterior points off both boundaries and outside every source and candidate drill polygon. The 455 µm envelope only locates remote negative evidence, never accepts local loss. Foreign-reference witnesses are additionally strictly inside unchanged foreign-track copper projected to the correct reference plane. They prove genuine positive-area reference regression, not merely native Boolean rounding artifacts. Full-track scanning stops after the first exact counterexample per case and is not claimed complete.

The six sites pass ordinary 150 µm inventory screening but not the conservative 205 µm sufficient screen. That distinction is not the rejection reason: actual native gates pass and exact reference regressions fail.

Preservation: all 85 preexisting files remain byte-identical; interrupted j0-b1 remains untouched and archived. Source hash remains 41f82c80f242eb8ded04d24c02f1ba1f39a900cd971d4bca6976d28353fcfdc5. Old audit is preserved as a historical checkpoint.

Not run after rejection: full antipad locality attribution, complete all-track area/contour acceptance scans, semantic material/contact merge acceptance, cold58, ERC and net-identity acceptance. No SI, simulated stability, manufacturing or production acceptance. No conclusion beyond these nine frozen pairs.
