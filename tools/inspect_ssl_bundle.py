"""Read-only inspector for the observed SnowRunner S3DB/SSLB bundle layout.

This validates container framing, not bytecode semantics. No extraction or writes.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path


def inspect(data, needles=()):
    if len(data) < 20 or data[:11] != bytes.fromhex("5333444201000200010001"):
        raise ValueError("unsupported S3DB header")
    count = struct.unpack_from("<I", data, 11)[0]
    if not 0 < count <= 100000 or data[15:20] != bytes.fromhex("0200000001"):
        raise ValueError("unsupported directory header/count")
    pos = 20
    names = []
    def u32():
        nonlocal pos
        if pos + 4 > len(data):
            raise ValueError("truncated directory")
        value = struct.unpack_from("<I", data, pos)[0]
        pos += 4
        return value
    for _ in range(count):
        size = u32()
        if not 0 < size <= 4096 or pos + size > len(data):
            raise ValueError("invalid module name length")
        names.append(data[pos:pos + size].decode("utf-8"))
        pos += size
    if data[pos:pos + 1] != b"\x01":
        raise ValueError("unsupported size-table marker")
    pos += 1
    sizes = [u32() for _ in range(count)]
    if pos + sum(sizes) != len(data):
        raise ValueError("module sizes do not consume entire bundle")
    modules = []
    for name, size in zip(names, sizes):
        chunk = data[pos:pos + size]
        if size < 16 or chunk[:8] != bytes.fromhex("53534c4202000200"):
            raise ValueError("unsupported SSLB module header")
        if struct.unpack_from("<I", chunk, 12)[0] != size - 16:
            raise ValueError("SSLB payload length mismatch")
        hits = []
        for needle in needles:
            marker = needle.encode("utf-8")
            if not marker:
                raise ValueError("empty search marker")
            start = 0
            while (offset := chunk.find(marker, start)) >= 0:
                hits.append({"marker": needle, "module_offset": offset, "bundle_offset": pos + offset})
                start = offset + 1
        modules.append({"name": name, "offset": pos, "size": size,
                        "sha256": hashlib.sha256(chunk).hexdigest(), "hits": hits})
        pos += size
    return {"sha256": hashlib.sha256(data).hexdigest(), "size": len(data),
            "module_count": count, "modules": modules,
            "limitations": "Observed framing only; strings do not establish execution or bytecode semantics."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--marker", action="append", default=[])
    parser.add_argument("--hits-only", action="store_true")
    args = parser.parse_args()
    try:
        if args.bundle.stat().st_size > 64 * 1024 * 1024:
            raise ValueError("bundle exceeds 64 MiB limit")
        result = inspect(args.bundle.read_bytes(), args.marker)
        if args.hits_only:
            result["modules"] = [m for m in result["modules"] if m["hits"]]
        print(json.dumps(result, indent=2))
    except (OSError, ValueError, struct.error) as error:
        parser.exit(1, f"Inspection failed: {error}\n")


if __name__ == "__main__":
    main()
