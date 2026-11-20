r"""Read-only comparison of completed, copied SnowRunner save snapshots.

Example (output stays in ignored sample-saves/):
  python tools/compare_snapshots.py sample-saves/baseline/remote \
    sample-saves/parked/remote --truck-id INSTANCE_ID \
    > sample-saves/comparison.json

Byte references are evidence only: they do not identify a complete vehicle
record, ownership, an authoritative restore transform, or a drivable truck.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import zlib

try:
    from .inspect_saves import decode_map
except ImportError:  # Direct script execution.
    from inspect_saves import decode_map

MAX_STORED_BYTES = 80 * 1024 * 1024
MAX_FILES = 256
MAX_MARKERS = 8
MAX_OFFSETS = 100
MAX_DIFF_RANGES = 20


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def validate_markers(truck_ids):
    if len(truck_ids) > MAX_MARKERS:
        raise ValueError(f'At most {MAX_MARKERS} truck IDs are supported')
    markers = []
    for truck_id in dict.fromkeys(truck_ids):
        if not truck_id or len(truck_id) > 256 or any(not 32 <= ord(c) <= 126 for c in truck_id):
            raise ValueError('Truck IDs must be 1–256 printable ASCII characters')
        markers.append((truck_id, truck_id.encode('ascii')))
    return markers


def snapshot_files(root):
    if not root.is_dir():
        raise ValueError(f'Snapshot directory does not exist: {root}')
    files = {}
    for path in root.iterdir():
        if path.suffix.lower() != '.cfg':
            continue
        if path.is_symlink():
            raise ValueError(f'Symlinked save file is not accepted: {path.name}')
        if path.is_file():
            files[path.name] = path
            if len(files) > MAX_FILES:
                raise ValueError(f'Snapshot exceeds {MAX_FILES} .cfg files')
    if not files:
        raise ValueError(f'Snapshot contains no .cfg files: {root}')
    return files


def read_stable(path):
    before = path.stat()
    if before.st_size > MAX_STORED_BYTES:
        raise ValueError(f'Stored file exceeds {MAX_STORED_BYTES} bytes: {path.name}')
    with path.open('rb') as stream:
        raw = stream.read(MAX_STORED_BYTES + 1)
    after = path.stat()
    if (len(raw) > MAX_STORED_BYTES or len(raw) != before.st_size or
            (before.st_size, before.st_mtime_ns, before.st_ino) !=
            (after.st_size, after.st_mtime_ns, after.st_ino)):
        raise ValueError(f'File changed during inspection: {path.name}')
    return raw


def marker_references(data, markers):
    result = {}
    for label, marker in markers:
        offsets, count, start = [], 0, 0
        while True:
            offset = data.find(marker, start)
            if offset < 0:
                break
            count += 1
            if len(offsets) < MAX_OFFSETS:
                offsets.append(offset)
            start = offset + 1  # Include overlapping occurrences.
        result[label] = {'count': count, 'offsets': offsets,
                         'offsets_truncated': count > len(offsets)}
    return result


def describe(raw, name, markers):
    info = {'stored_bytes': len(raw), 'stored_sha256': sha256(raw)}
    if 'sts' in name.lower():
        try:
            payload = decode_map(raw)
        except (ValueError, zlib.error) as error:
            info.update(payload_kind='invalid_map', decode_error=str(error))
            return info, None
        info.update(payload_kind='decoded_map', decoded_bytes=len(payload),
                    decoded_sha256=sha256(payload), trailer_hex=raw[-4:].hex())
    else:
        payload = raw
        info['payload_kind'] = 'raw_cfg'
    info['truck_id_references'] = marker_references(payload, markers)
    return info, payload


def byte_changes(before, after):
    """Positional differences, not an insertion-aware record alignment."""
    count, ranges, range_start = 0, [], None
    for offset in range(max(len(before), len(after))):
        changed = (offset >= len(before) or offset >= len(after) or
                   before[offset] != after[offset])
        if changed:
            count += 1
            if range_start is None:
                range_start = offset
        elif range_start is not None:
            if len(ranges) < MAX_DIFF_RANGES:
                ranges.append([range_start, offset])
            range_start = None
    if range_start is not None and len(ranges) < MAX_DIFF_RANGES:
        ranges.append([range_start, max(len(before), len(after))])
    return {'positional_differing_bytes': count,
            'length_delta': len(after) - len(before),
            'first_differing_ranges_half_open': ranges,
            'range_limit': MAX_DIFF_RANGES,
            'note': 'Positional only; insertions can shift all later bytes. Ranges are capped.'}


def compare(before_root, after_root, truck_ids=()):
    markers = validate_markers(truck_ids)
    before_files, after_files = snapshot_files(Path(before_root)), snapshot_files(Path(after_root))
    rows, errors = [], 0
    counts = {'added': 0, 'removed': 0, 'changed': 0, 'unchanged': 0}
    for name in sorted(before_files.keys() | after_files.keys()):
        row, payloads = {'file': name}, {}
        for side, paths in [('before', before_files), ('after', after_files)]:
            if name in paths:
                row[side], payloads[side] = describe(read_stable(paths[name]), name, markers)
                errors += int('decode_error' in row[side])
        if 'before' not in row:
            status = 'added'
        elif 'after' not in row:
            status = 'removed'
        else:
            status = 'unchanged' if row['before']['stored_sha256'] == row['after']['stored_sha256'] else 'changed'
            if payloads['before'] is not None and payloads['after'] is not None:
                row['payload_comparison'] = byte_changes(payloads['before'], payloads['after'])
        row['status'] = status
        counts[status] += 1
        rows.append(row)
    return {'schema_version': 1, 'summary': counts, 'decode_errors': errors,
            'files': rows, 'limitations': [
                'Only top-level .cfg files are inspected; use the actual copied remote folders.',
                'Use completed, quiescent snapshots; this tool cannot establish capture consistency.',
                'Truck IDs are exact ASCII byte searches, not parsed records or ownership evidence.',
                'A persisted byte reference does not establish a visible or drivable vehicle.',
                'Correlate host/guest observations and captures; offsets are capture-specific.',
                'Output may contain private filenames and IDs; keep it outside Git or in sample-saves/.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('before_directory', type=Path)
    parser.add_argument('after_directory', type=Path)
    parser.add_argument('--truck-id', action='append', default=[], help='Exact instance ID to locate; repeat up to eight times')
    args = parser.parse_args()
    try:
        result = compare(args.before_directory, args.after_directory, args.truck_id)
    except (OSError, ValueError) as error:
        parser.exit(2, f'Comparison failed: {error}\n')
    print(json.dumps(result, indent=2))
    return 1 if result['decode_errors'] else 0


if __name__ == '__main__':
    sys.exit(main())
