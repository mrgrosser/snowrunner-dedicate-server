import importlib.util
from pathlib import Path
import struct
import unittest
import zlib

spec = importlib.util.spec_from_file_location('inspect_saves', Path(__file__).parents[1] / 'tools/inspect_saves.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class MapValidationTests(unittest.TestCase):
    def test_valid_payload(self):
        data = b'truck\0' * 100
        self.assertEqual(module.decode_map(struct.pack('<I', len(data)) + zlib.compress(data) + b'\x4b\x17\x34\x01'), data)

    def test_wrong_length(self):
        with self.assertRaises(ValueError):
            module.decode_map(struct.pack('<I', 2) + zlib.compress(b'abc') + b'\0' * 4)

    def test_truncated_stream(self):
        with self.assertRaises(ValueError):
            module.decode_map(struct.pack('<I', 3) + zlib.compress(b'abc')[:-2])

    def test_trailing_data(self):
        with self.assertRaises(ValueError):
            module.decode_map(struct.pack('<I', 3) + zlib.compress(b'abc') + b'x')

    def test_size_limit(self):
        with self.assertRaises(ValueError):
            module.decode_map(struct.pack('<I', 100) + zlib.compress(b'abc'), limit=10)


if __name__ == '__main__':
    unittest.main()
