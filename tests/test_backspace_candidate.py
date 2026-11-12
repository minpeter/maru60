"""Candidate evidence and assembly population must stay bound to delivered CAD."""
import csv
import gzip
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT / 'pcb/experiments/resume-20261112-backspace-2u'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name):
    return json.loads((CANDIDATE / name).read_text())


def csv_rows(name):
    with (CANDIDATE/'order'/name).open() as stream:
        return list(csv.DictReader(stream))


class BackspaceCandidateTest(unittest.TestCase):
    def test_archived_files_have_the_recorded_identity(self):
        manifest = read('MANIFEST.json')
        self.assertFalse(manifest['manufacturing_ready'])
        for path, value in manifest['files'].items():
            self.assertEqual(digest(ROOT/path), value, path)

    def test_native_mechanical_dfm_and_led_reports_bind_same_board(self):
        board_hash = digest(CANDIDATE/'pcb/maru60.kicad_pcb')
        for name in ('native-RESULT.json', 'mechanical-fit.json', 'dfm-per-rule.json', 'led-corners.json'):
            report = read('qa/'+name)
            self.assertEqual(report['board_sha256'], board_hash, name)
            if 'pass' in report:
                self.assertTrue(report['pass'], name)
        dfm = read('qa/dfm-per-rule.json')
        self.assertEqual(len(dfm['rules']), 32)
        self.assertTrue(all(r['violations'] == 0 and r['unconnected'] == 0 for r in dfm['rules']))
        led = read('qa/led-corners.json')
        self.assertEqual(len(led['cases']), 54)
        self.assertTrue(all(c['pass'] for c in led['cases']))
        geometry = gzip.decompress((CANDIDATE/'qa/geometry.json.gz').read_bytes())
        self.assertEqual(hashlib.sha256(geometry).hexdigest(), led['geometry_sha256'])
        self.assertEqual(digest(CANDIDATE/'qa/lines.json'), led['lines_sha256'])

    def test_export_hashes_and_readback(self):
        prov = read('order/PROVENANCE.json')
        self.assertEqual(digest(ROOT/prov['board']['path']), prov['board']['sha256'])
        self.assertTrue(all(c['pass'] for c in prov['checks']))
        for path, value in prov['files'].items():
            self.assertEqual(digest(CANDIDATE/'order'/path), value, path)
        self.assertEqual(digest(CANDIDATE/'order/parts.json'), prov['parts_database']['sha256'])
        self.assertTrue(read('qa/gerber-readback.json')['pass'])

    def test_exclusive_led_sites_and_receptacles_are_not_auto_assembled(self):
        full = {r['Reference']: r for r in csv_rows('bom-full.csv')}
        bom_refs = [ref for row in csv_rows('bom-jlcpcb.csv') for ref in row['Designator'].split(',')]
        cpl_refs = [r['Designator'] for r in csv_rows('cpl-jlcpcb.csv')]
        self.assertEqual(len(bom_refs), len(set(bom_refs)))
        self.assertEqual(set(bom_refs), set(cpl_refs))
        self.assertEqual(len(cpl_refs), 334)
        for ref in ('SW14','SW15','LED14','LED15'):
            self.assertNotIn(ref, cpl_refs)
            self.assertEqual(full[ref]['Assembled by JLCPCB'], 'no')
        self.assertTrue({'R189','R190','R191'} <= set(cpl_refs))
        parts = read('order/parts.json')['rules']
        for ref in ('SW14','SW15'):
            rule = next(r for r in parts if ref in r.get('refs', []))
            self.assertEqual(rule['mfr'], 'Mill-Max')
            self.assertIn('pending', rule['mpn'])


if __name__ == '__main__':
    unittest.main()
