"""A partial ngspice waveform must never be accepted as a completed run."""
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from pcb.tools.signal_integrity import spice


class SpiceRunnerTest(unittest.TestCase):
    def test_timeout_removes_only_its_own_container(self):
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(spice, "OUT", Path(temp)), patch.object(spice, "DECKS", Path(temp)), \
                 patch.object(spice.subprocess, "run", side_effect=[
                     subprocess.TimeoutExpired("docker", 240),
                     subprocess.CompletedProcess([], 0, "", ""),
                 ]) as run:
                with self.assertRaisesRegex(RuntimeError, "timed out"):
                    spice.run_deck("slow_case")
            started = run.call_args_list[0].args[0]
            name = started[started.index("--name") + 1]
            self.assertEqual(run.call_args_list[1].args[0], ["docker", "rm", "-f", name])

    def test_roundoff_length_is_a_junction_not_a_singular_ladder(self):
        deck = spice.Deck("stub split remainder")
        deck.ladder("a", "b", 2e-15, 0.2, {})
        self.assertEqual(deck.lines[1:], ["Rj1 a b 1m"])

    def test_real_short_trace_retains_inductance_and_capacitance(self):
        deck = spice.Deck("real short trace")
        with patch.object(spice, "line_params", return_value={
            "R_ohm_per_mm": 0.002, "L_nH_per_mm": 0.4, "C_pF_per_mm": 0.1,
        }):
            deck.ladder("a", "b", 1e-5, 0.2, {})
        self.assertTrue(any(line.startswith("Lt") for line in deck.lines))
        self.assertTrue(any(line.startswith("Ct") for line in deck.lines))

    def test_exit_zero_with_aborted_analysis_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            def aborted(*args, **kwargs):
                (out / "case.txt").write_text("time v(din)\n0 0\n1e-9 1e200\n")
                return subprocess.CompletedProcess(args[0], 0, "run simulation(s) aborted\n", "")
            with patch.object(spice, "OUT", out), patch.object(spice, "DECKS", out), \
                 patch.object(spice.subprocess, "run", side_effect=aborted):
                with self.assertRaises(spice.SimulationAborted):
                    spice.run_deck("case")

    def test_nonfinite_output_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            def nonfinite(*args, **kwargs):
                (out / "case.txt").write_text("time v(din)\n0 0\n1e-9 nan\n")
                return subprocess.CompletedProcess(args[0], 0, "", "")
            with patch.object(spice, "OUT", out), patch.object(spice, "DECKS", out), \
                 patch.object(spice.subprocess, "run", side_effect=nonfinite):
                with self.assertRaisesRegex(RuntimeError, "nonfinite"):
                    spice.run_deck("case")


if __name__ == "__main__":
    unittest.main()
