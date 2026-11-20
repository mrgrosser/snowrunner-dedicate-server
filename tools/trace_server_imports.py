#!/usr/bin/env python3
"""Read-only, bounded PE evidence. Requires pefile and capstone; never runs input."""
import argparse, collections, hashlib, json, re, struct
from pathlib import Path
import pefile
import capstone

def rip_target(address, size, displacement):
    return address + size + displacement

def analyze(path):
    raw = Path(path).read_bytes()
    pe = pefile.PE(data=raw, fast_load=True)
    pe.parse_data_directories(directories=[3, 5, 13])
    base = pe.OPTIONAL_HEADER.ImageBase
    cs = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    def decode(va, size=48):
        try: data = pe.get_data(va-base, size)
        except pefile.PEFormatError: return []
        return [[hex(a), m, o] for a,n,m,o in cs.disasm_lite(data, va)]
    sections = []
    for s in pe.sections:
        sections.append(dict(name=s.Name.rstrip(b'\0').decode(), rva=hex(s.VirtualAddress),
          offset=hex(s.PointerToRawData), virtual_size=hex(s.Misc_VirtualSize),
          raw_size=hex(s.SizeOfRawData), flags=hex(s.Characteristics), entropy=s.get_entropy(),
          first_instructions=decode(base+s.VirtualAddress)))
    imports=[]
    for d in getattr(pe, 'DIRECTORY_ENTRY_DELAY_IMPORT', []):
        for i in d.imports:
            if d.dll.lower() != b'steam_api64.dll': continue
            value=struct.unpack('<Q',pe.get_data(i.address-base,8))[0]
            imports.append(dict(name=i.name.decode(),va=hex(i.address),initial_value=hex(value),initial_decode=decode(value)))
    strings=[]
    for literal in [b'Multiplayer.IsDedicatedServer',b'Debug.IsDedicatedServerDll',b'Debug.LaunchMode',
                    b'steam.gameServer.steamPort', b'steam.gameServer.gamePort',b'SteamGameServer014',
                    b'Failed to initialize game server API.']:
        start=0
        while (off:=raw.find(literal+b'\0',start))>=0:
            strings.append(dict(name=literal.decode(),offset=hex(off),va=hex(base+pe.get_rva_from_offset(off))))
            start=off+1
    targets={int(x['va'],16):x['name'] for x in imports+strings}
    targets.update({int(x['initial_value'],16):x['name']+' initial thunk' for x in imports})
    hits=[]
    # Every possible start for FF15/FF25 and REX LEA/MOV RIP-relative encoding.
    # This finds candidates, not instruction-boundary-validated callers.
    pattern=re.compile(rb'(?=([\xe8\xe9]|\xff[\x15\x25]|[\x48-\x4f][\x8d\x8b\x89][\x05\x0d\x15\x1d\x25\x2d\x35\x3d]))')
    for s in pe.sections:
        if not s.Characteristics & 0x20000000: continue
        data=s.get_data()
        for m in pattern.finditer(data):
            pos=m.start(); prefix=len(m.group(1))
            if pos+prefix+4>len(data):continue
            va=base+s.VirtualAddress+pos
            dest=rip_target(va,prefix+4,struct.unpack_from('<i',data,pos+prefix)[0])
            if dest in targets:
                hits.append(dict(site=hex(va),target=targets[dest],section=s.Name.rstrip(b'\0').decode(),decode=decode(va,24)))
    relocs=[e for b in getattr(pe,'DIRECTORY_ENTRY_BASERELOC',[]) for e in b.entries]
    pointers=[]
    for target,name in targets.items():
        needle=struct.pack('<Q',target);start=0
        while (off:=raw.find(needle,start))>=0:
            rva=pe.get_rva_from_offset(off)
            pointers.append(dict(target=name,offset=hex(off),rva=hex(rva),
              relocation_type=[e.type for e in relocs if e.rva==rva]))
            start=off+1
    funcs=getattr(pe,'DIRECTORY_ENTRY_EXCEPTION',[])
    samples=[]
    for e in funcs[:12]:
        rva=e.struct.BeginAddress
        samples.append(dict(begin=hex(base+rva),end=hex(base+e.struct.EndAddress),decode=decode(base+rva,32)))
    return dict(sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),versions=dict(pefile=pefile.__version__,capstone=capstone.__version__),
      base=hex(base),entry=hex(base+pe.OPTIONAL_HEADER.AddressOfEntryPoint),
      sections=sections,imports=imports,strings=strings,candidate_references=hits,absolute_pointer_references=pointers,
      relocations=dict(collections.Counter(e.type for e in relocs)),relocations_by_section=dict(collections.Counter(
      (pe.get_section_by_rva(e.rva).Name.rstrip(b'\0').decode() if pe.get_section_by_rva(e.rva) else 'headers') for e in relocs if e.type)),
      exception_count=len(funcs),exception_start_samples=samples)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('binary');a=p.parse_args()
    print(json.dumps(analyze(a.binary),indent=2))
