import unittest
from tools.inspect_ssl_wire import fields, varint


class WireValidationTests(unittest.TestCase):
    def test_uint64_boundary(self):
        self.assertEqual(varint(b"\xff" * 9 + b"\x01", 0), (2**64 - 1, 10))
        for data in (b"\x80", b"\xff" * 9 + b"\x02"):
            with self.subTest(data=data), self.assertRaises(ValueError):
                varint(data, 0)

    def test_mixed_wire_types_and_offsets(self):
        data = b"\x08\x96\x01\x12\x02hi\x1d1234\x21abcdefgh"
        parsed = fields(data)
        self.assertEqual([(n, w, v) for n, w, v, _, _ in parsed],
                         [(1, 0, 150), (2, 2, b"hi"), (3, 5, b"1234"), (4, 1, b"abcdefgh")])
        self.assertEqual(parsed[0][3], 0)
        self.assertEqual(parsed[-1][4], len(data))

    def test_invalid_tags_and_truncated_values(self):
        for data in (b"\x00", b"\x0b", b"\x12\x05hi", b"\x1d123", b"\x21abc"):
            with self.subTest(data=data), self.assertRaises(ValueError):
                fields(data)
