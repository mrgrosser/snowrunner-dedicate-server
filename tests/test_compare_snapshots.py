import hashlib
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zlib

from tools import compare_snapshots as comparison


def map_bytes(payload, trailer=b'abcd'):
    return struct.pack('<I', len(payload)) + zlib.compress(payload) + trailer


class SnapshotComparisonTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.before = self.root / 'before'
        self.after = self.root / 'after'
        self.before.mkdir()
        self.after.mkdir()

    def write(self, folder, name, payload):
        (folder / name).write_bytes(payload)

    def test_decoded_id_move_and_input_bytes_unchanged(self):
        name = '1_sts_level_us_02_01.cfg'
        old = map_bytes(b'xxTRUCK-123\x00AAAA')
        new = map_bytes(b'xxxxTRUCK-123\x00AAAB')
        self.write(self.before, name, old)
        self.write(self.after, name, new)
        result = comparison.compare(self.before, self.after, ['TRUCK-123'])
        row = result['files'][0]
        self.assertEqual(result['summary']['changed'], 1)
        self.assertEqual(row['before']['truck_id_references']['TRUCK-123']['offsets'], [2])
        self.assertEqual(row['after']['truck_id_references']['TRUCK-123']['offsets'], [4])
        self.assertEqual(row['payload_comparison']['length_delta'], 2)
        self.assertEqual((self.before / name).read_bytes(), old)
        self.assertEqual((self.after / name).read_bytes(), new)
        self.assertEqual(row['before']['stored_sha256'], hashlib.sha256(old).hexdigest())

    def test_container_only_change_is_not_payload_change(self):
        self.write(self.before, 'sts_level.cfg', map_bytes(b'same', b'abcd'))
        self.write(self.after, 'sts_level.cfg', map_bytes(b'same', b'wxyz'))
        row = comparison.compare(self.before, self.after)['files'][0]
        self.assertEqual(row['status'], 'changed')
        self.assertEqual(row['payload_comparison']['positional_differing_bytes'], 0)
        self.assertNotEqual(row['before']['trailer_hex'], row['after']['trailer_hex'])

    def test_added_removed_unchanged_and_missing_marker(self):
        self.write(self.before, 'gone.cfg', b'ID')
        self.write(self.after, 'new.cfg', b'ID')
        for folder in [self.before, self.after]:
            self.write(folder, 'CompleteSave.cfg', b'{"a":1}')
            self.write(folder, 'ignored.txt', b'not a save')
        result = comparison.compare(self.before, self.after, ['ID'])
        self.assertEqual(result['summary'], {'added': 1, 'removed': 1, 'changed': 0, 'unchanged': 1})
        self.assertEqual(result['files'][0]['before']['truck_id_references']['ID']['count'], 0)

    def test_corrupt_map_is_reported_not_searched_as_raw(self):
        for folder in [self.before, self.after]:
            self.write(folder, 'sts_level.cfg', b'ID invalid map')
        result = comparison.compare(self.before, self.after, ['ID'])
        self.assertEqual(result['decode_errors'], 2)
        self.assertNotIn('truck_id_references', result['files'][0]['before'])
        self.assertNotIn('payload_comparison', result['files'][0])

    def test_offsets_bounded_but_count_exact_and_overlapping(self):
        refs = comparison.marker_references(b'a' * 105, [('aa', b'aa')])['aa']
        self.assertEqual(refs['count'], 104)
        self.assertEqual(len(refs['offsets']), 100)
        self.assertTrue(refs['offsets_truncated'])

    def test_change_count_and_half_open_ranges_include_tail(self):
        diff = comparison.byte_changes(b'abcde', b'axcdyz')
        self.assertEqual(diff['positional_differing_bytes'], 3)
        self.assertEqual(diff['first_differing_ranges_half_open'], [[1, 2], [4, 6]])
        self.assertEqual(diff['length_delta'], 1)

    def test_invalid_marker_and_missing_or_empty_snapshot_rejected(self):
        for bad in ['', 'nonascii\u2603', 'line\nbreak', 'x' * 257]:
            with self.assertRaises(ValueError):
                comparison.validate_markers([bad])
        with self.assertRaises(ValueError):
            comparison.validate_markers([str(x) for x in range(9)])
        for folder in [self.before, self.root / 'missing']:
            with self.assertRaises(ValueError):
                comparison.snapshot_files(folder)

    def test_symlink_and_size_limit_rejected(self):
        original = self.root / 'original.cfg'
        original.write_bytes(b'abc')
        (self.before / 'linked.cfg').symlink_to(original)
        with self.assertRaises(ValueError):
            comparison.snapshot_files(self.before)
        with patch.object(comparison, 'MAX_STORED_BYTES', 2):
            with self.assertRaises(ValueError):
                comparison.read_stable(original)

    def test_cli_returns_nonzero_for_invalid_map(self):
        for folder in [self.before, self.after]:
            self.write(folder, 'sts_level.cfg', b'broken')
        completed = subprocess.run([sys.executable, str(Path(comparison.__file__)),
                                    str(self.before), str(self.after)], capture_output=True, text=True)
        self.assertEqual(completed.returncode, 1)
        self.assertIn('decode_errors', completed.stdout)


if __name__ == '__main__':
    unittest.main()
