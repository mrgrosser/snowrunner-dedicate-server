"""Read-only SnowRunner save inspection. Output is evidence, not a world parser."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import zlib


def decode_map(raw, limit=64 * 1024 * 1024):
    if len(raw) < 6:
        raise ValueError('Truncated map header')
    expected = struct.unpack('<I', raw[:4])[0]
    if expected > limit:
        raise ValueError('Map exceeds decoded size limit')
    decoder = zlib.decompressobj()
    decoded = decoder.decompress(raw[4:], expected + 1)
    if len(decoded) != expected or not decoder.eof or len(decoder.unused_data) != 4:
        raise ValueError('Map length/stream validation failed')
    return decoded


def inspect(root):
    result = {'campaigns': [], 'map_files': [], 'source_sha256': {}}
    truck_types = set()
    for path in sorted(root.glob('CompleteSave*.cfg')):
        raw = path.read_bytes()
        result['source_sha256'][path.name] = hashlib.sha256(raw).hexdigest()
        save = json.loads(raw.rstrip(b'\0'))[path.stem]['SslValue']
        profile = save['persistentProfileData']
        owned = profile.get('ownedTrucks', {})
        truck_types.update(owned)
        warehouse = profile.get('trucksInWarehouse', [])
        garages = []
        for map_id, garage in save.get('garagesData', {}).items():
            for slot, data in garage.get('slotsDatas', {}).items():
                if data.get('truckDesc'):
                    garages.append({'map': map_id, 'slot': slot, 'truck': data['truckDesc']})
        result['campaigns'].append({
            'file': path.name, 'schema_version': save.get('objVersion'),
            'rank': profile.get('rank'), 'money': profile.get('money'),
            'owned_counts': owned, 'owned_total': sum(owned.values()),
            'warehouse': warehouse, 'garages': garages,
            'unlocated_owned_count': sum(owned.values()) - len(warehouse) - len(garages),
            'note': 'Unlocated count does not prove deployment or ownership of map records.'
        })
    for path in sorted(root.glob('*sts*.cfg')):
        raw = path.read_bytes()
        result['source_sha256'][path.name] = hashlib.sha256(raw).hexdigest()
        decoded = decode_map(raw)
        references = []
        for match in re.finditer(rb'[ -~]{5,}', decoded):
            value = match.group().decode('ascii')
            if value in truck_types:
                references.append({'offset': match.start(), 'type': value})
        result['map_files'].append({
            'file': path.name, 'stored_bytes': len(raw), 'decoded_bytes': len(decoded),
            'trailer_hex': raw[-4:].hex(),
            'decoded_sha256': hashlib.sha256(decoded).hexdigest(),
            'truck_string_references': references,
            'note': 'String references can include world spawns and repeated records; not vehicle counts.'
        })
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('save_directory', type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect(args.save_directory), indent=2))
