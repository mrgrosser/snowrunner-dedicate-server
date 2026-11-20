"""Bounded protobuf-wire structural probe; not an SSL bytecode decoder."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import zipfile
if __package__:
    from .inspect_ssl_bundle import inspect
else:
    from inspect_ssl_bundle import inspect

TARGETS = ("main.ds_config_consts", "cmd_line_options.cmd_line_options",
           "game.game_modes.game_session")


def varint(data, pos):
    value = 0
    for shift in range(0, 70, 7):
        if pos >= len(data):
            raise ValueError("truncated varint")
        b = data[pos]
        pos += 1
        if shift == 63 and b > 1:
            raise ValueError("varint exceeds uint64")
        value |= (b & 127) << shift
        if b < 128:
            return value, pos
    raise ValueError("overlong varint")


def fields(data):
    if len(data) > 64 * 1024 * 1024:
        raise ValueError("message exceeds bound")
    pos = 0
    out = []
    while pos < len(data):
        start = pos
        tag, pos = varint(data, pos)
        number, wire = tag >> 3, tag & 7
        if not 0 < number < (1 << 29):
            raise ValueError("invalid field number")
        if wire == 0:
            value, pos = varint(data, pos)
        elif wire in (1, 5):
            end = pos + (8 if wire == 1 else 4)
            if end > len(data):
                raise ValueError("truncated fixed field")
            value, pos = data[pos:end], end
        elif wire == 2:
            length, pos = varint(data, pos)
            end = pos + length
            if end > len(data):
                raise ValueError("truncated length field")
            value, pos = data[pos:end], end
        else:
            raise ValueError("unsupported wire type")
        out.append((number, wire, value, start, pos))
        if len(out) > 1000000:
            raise ValueError("field count exceeds bound")
    return out


def bundles(path):
    with zipfile.ZipFile(path) as archive:
        for entry in archive.infolist():
            if entry.filename.endswith(".sslbundle"):
                if entry.file_size > 64 * 1024 * 1024:
                    raise ValueError("bundle exceeds bound")
                yield entry.filename, archive.read(entry)


def structural_links(decoded, strings):
    """Report name/literal and name/body table links without decoding instructions."""
    classes = [v for n,w,v,*_ in decoded if n == 7 and w == 2]
    bodies = [v for n,w,v,*_ in decoded if n == 8 and w == 2]
    out = []
    for ci, record in enumerate(classes):
        cf = fields(record)
        class_name = next((v for n,w,v,*_ in cf if n == 1 and w == 0), None)
        if class_name is None or class_name >= len(strings):
            continue
        members = [v for n,w,v,*_ in cf if n == 3 and w == 2]
        for mi, member in enumerate(members):
            mf = fields(member)
            scalars = {n:v for n,w,v,*_ in mf if w == 0}
            si = scalars.get(1)
            if si is None or si >= len(strings):
                continue
            name = strings[si]
            if strings[class_name] in ("SessionTypeServer", "LeechDSMode", "DsConfigConsts"):
                for n,w,v,*_ in mf:
                    if n == 5 and w == 2:
                        literal = {a:x for a,b,x,*_ in fields(v) if b == 0}
                        item = {"class": strings[class_name], "member": name,
                                "raw_literal_fields": literal}
                        if literal.get(1) == 4 and literal.get(5, len(strings)) < len(strings):
                            item["candidate_string_value"] = strings[literal[5]]
                        out.append(item)
            if name in ("NetDeleteDisconnectedUserTrucks", "SetServerDedicated"):
                bi = scalars.get(4)
                matched = False
                if bi is not None and bi < len(bodies):
                    for n,w,v,*_ in fields(bodies[bi]):
                        if n == 2 and w == 2:
                            matched = any(a == 1 and b == 0 and x == si
                                          for a,b,x,*_ in fields(v))
                out.append({"class": strings[class_name], "member": name,
                            "class_record_index": ci, "member_record_index": mi,
                            "candidate_body_index": bi, "body_name_matches": matched})
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pak", type=Path)
    args = parser.parse_args()
    failures = 0
    for name, data in bundles(args.pak):
        result = inspect(data)
        counts = Counter()
        for module in result["modules"]:
            chunk = data[module["offset"]:module["offset"] + module["size"]]
            try:
                decoded = fields(chunk[16:])
                counts["wire_parse_ok"] += 1
            except ValueError:
                counts["wire_parse_failed"] += 1
                failures += 1
                continue
            if module["name"] in TARGETS or b"SetServerDedicated" in chunk:
                strings = [v.decode("utf-8") for n,w,v,_,_ in decoded if n == 6 and w == 2]
                wanted = ("NetDeleteDisconnectedUserTrucks", "SetServerDedicated")
                print(json.dumps({"bundle": name, "module": module["name"],
                    "sha256": hashlib.sha256(chunk).hexdigest(),
                    "field_counts": dict(Counter(str((n,w)) for n,w,_,_,_ in decoded)),
                    "target_string_slots": {s: [i for i,v in enumerate(strings) if v == s] for s in wanted},
                    "string_count": len(strings),
                    "structural_links": structural_links(decoded, strings)}))
        print(json.dumps({"bundle": name, "module_count": result["module_count"], **counts}))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
