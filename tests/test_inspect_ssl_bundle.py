import struct
import unittest
from tools.inspect_ssl_bundle import inspect


def sample():
    payload = b"sample_marker"
    module = bytes.fromhex("53534c4202000200") + b"\0" * 4 + struct.pack("<I", len(payload)) + payload
    name = b"example.module"
    return (bytes.fromhex("5333444201000200010001") + struct.pack("<I", 1)
            + bytes.fromhex("0200000001") + struct.pack("<I", len(name)) + name
            + b"\x01" + struct.pack("<I", len(module)) + module)


class BundleFramingTests(unittest.TestCase):
    def test_location_and_complete_consumption(self):
        data = sample()
        result = inspect(data, ["sample_marker"])
        self.assertEqual(result["module_count"], 1)
        self.assertEqual(result["modules"][0]["hits"][0]["bundle_offset"], data.index(b"sample_marker"))
        self.assertEqual(result["modules"][0]["hits"][0]["module_offset"], 16)

    def test_truncated_or_extra_bytes_rejected(self):
        for data in (sample()[:10], sample()[:-1], sample() + b"x"):
            with self.subTest(length=len(data)), self.assertRaises(ValueError):
                inspect(data)

    def test_payload_length_mismatch_rejected(self):
        data = bytearray(sample())
        offset = data.index(b"SSLB")
        struct.pack_into("<I", data, offset + 12, 1)
        with self.assertRaisesRegex(ValueError, "payload length"):
            inspect(data)

    def test_unknown_version_and_huge_name_rejected(self):
        data = bytearray(sample()); data[4] = 9
        with self.assertRaises(ValueError): inspect(data)
        data = bytearray(sample()); struct.pack_into("<I", data, 20, 0xffffffff)
        with self.assertRaises(ValueError): inspect(data)
