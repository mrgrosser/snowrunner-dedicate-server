# SnowRunner native call-path boundary

2026-11-20; follow-up to SERVER_BINARY_ANALYSIS.md. Read-only static inspection of
the existing copied executable only. No target execution, patching, DRM bypass,
NAS changes, commits or publishing.

## Result

**Actual application callers and a reachable dedicated mode remain unresolved.**
There is now a concrete reason why ordinary string-xref searches failed: the
on-disk main code section is essentially uniform high-entropy data, and bytes at
both PE-declared function starts and Steam delay-thunk destinations do not decode
as credible ordinary AMD64 application code. The absence of xrefs must not be
interpreted as dead server code.

This is consistent with protected/transformed code behind an entry wrapper.
It does **not** identify a protection product, prove a particular encryption
algorithm, or authorize recovery/bypass. A better decompiler alone cannot infer
the original program from these bytes.

## Identity and reproducibility

Input: `private-evidence/binary/SnowRunner.exe`, 46,810,152 bytes.
SHA-256:
`d46623b23808d19a40f7ebeec15332d11f97317637ec4d4e072a501bc78a77c8`.

Added `tools/trace_server_imports.py`: a read-only PE/Capstone evidence helper.
Dependencies were installed only into ignored `private-evidence/trace-venv`:
pefile 2024.8.26, Capstone 5.0.7. No global configuration was changed.

```sh
private-evidence/trace-venv/bin/python tools/trace_server_imports.py \
  private-evidence/binary/SnowRunner.exe \
  > private-evidence/binary/server-call-paths-overlap.json
objdump -d --start-address=0x141da0a28 --stop-address=0x141da0a48 \
  private-evidence/binary/SnowRunner.exe
objdump -d --start-address=0x142dcd310 --stop-address=0x142dcd370 \
  private-evidence/binary/SnowRunner.exe
```

These are ordinary-tool observations, not REA native-analysis Evidence IDs.
Private JSON preserves short disassembly samples, section metadata, names, exact
addresses, pointer/relocation associations and tool versions. Keep it and the
binary out of version control.

## Existing native provider inspection

The parent identified /opt/hopper; it was inspected rather than assumed absent.
Hopper and hopper_mcp exist. Cached REA 6.9.0 is available at
`/home/it/.npm/_npx/1919570b910cc3db/node_modules/rea-agents/scripts/rea.mjs`.
No REA MCP tools were exposed to this child.

A read-only `rea doctor --provider hopper --target <exact executable> --format json`
reported the requested scope healthy, Hopper release 6.6.2 (signed-package-cache
identity), and private-display readiness. Thus **Hopper is present**, and Java
presence or missing PATH launchers are not a justified provider blocker.
Broader environment readiness was false, separately from this healthy scope.
The diagnostic is retained as `private-evidence/binary/rea-hopper-doctor.json`.

A direct Hopper help probe without DISPLAY aborted at Qt initialization.
An offscreen probe started but supplied no help within 15 seconds; its logs
searched CPU/loader plugin locations, and the inspected /opt/hopper and user
plugin trees had no CPU/loader directories. That is a bounded observation, not
a definitive provider-availability diagnosis.

A subsequent exact-target `rea analyze <absolute exe> --provider hopper --format json`
with process-local `QT_QPA_PLATFORM=offscreen` and a 45-second timeout returned
a structured cancellation with `operation: hopper`, nested `binary_overview`,
and `cleanup: complete`. It produced no native overview or xrefs in that
budget. The shell timeout exited 124; retained output is
`private-evidence/binary/rea-hopper-analysis.json`. A process check afterward
found no Hopper, hopper_mcp, REA analyze or Xvfb processes left running.
The same cold analysis was not retried. This is a bounded provider-analysis
timeout, **not proof Hopper cannot work**. Independent of that tool budget,
the raw-code validity boundary below remains the substantive obstacle.

## Mapping and code-validity evidence

Preferred image base is `0x140000000`. Mapping is section-specific:
`file = section.raw_offset + RVA - section.RVA`, not one global adjustment.

| Section | RVA | Raw file offset | Entropy, bits/byte |
| --- | --- | --- | --- |
| .text | 0x1000 | 0x600 | 7.999995 |
| .rdata | 0x21c0000 | 0x21be800 | 5.649135 |
| .data | 0x29a7000 | 0x29a5400 | 4.036176 |
| .pdata | 0x2bba000 | 0x2a57600 | 7.025964 |
| _RDATA | 0x2d82000 | 0x2c1f600 | 7.284524 |
| .rsrc | 0x2d8c000 | 0x2c28a00 | 6.406409 |
| .reloc | 0x2d97000 | 0x2c33600 | 5.469221 |
| .bind | 0x2dcd000 | 0x2c68800 | 7.960006 |

Entropy uses raw section bytes (including alignment). As a separate check, all
539 complete 64-KiB blocks of the .text virtual extent had entropy between
7.996421 and 7.998006. Thus the section-wide result is not caused merely by one
large high-entropy suffix hiding normal code.

The PE exception directory supplies 155,643 runtime-function records. Decoding
the first 12 declared starts produces implausible stack/segment/I/O operations
and early decode termination. Example: the first record starts at
`0x140001070`, ending `0x140001222`; its bytes decode to `jl`, `pop rsp`,
then unrelated arithmetic and I/O operations. This sample does not establish
that every function is transformed, but corroborates the entropy result.

For a positive control, entry `0x142dcd310` in .bind decodes coherently in
objdump: register saves, aligned call to `0x142dcd3d0`, restores, then return.
Importantly, after the call it writes RAX into the saved return slot at
`0x142dcd353`. This is an indirect entry handoff through the callee's return
value, not proof of a direct call to ordinary application main. The handoff
destination was not recovered or executed.

## Exact Steam delay-IAT mappings

All addresses below are preferred VAs except the explicit file column.
These are initial on-disk thunk pointers, **not recovered callers**.

| Import | Delay IAT VA | IAT file offset | Initial pointer |
| --- | --- | --- | --- |
| SteamGameServer_RunCallbacks | 0x142a590b0 | 0x2a574b0 | 0x141da09bc |
| SteamGameServer_GetHSteamUser | 0x142a590b8 | 0x2a574b8 | 0x141da09ce |
| SteamInternal_FindOrCreateGameServerInterface | 0x142a590c0 | 0x2a574c0 | 0x141da09e0 |
| SteamInternal_GameServer_Init | 0x142a590d8 | 0x2a574d8 | 0x141da0a28 |

Each of these IAT storage RVAs has an IMAGE_REL_BASED_DIR64 (type 10)
relocation. All 15 Steam initial thunk addresses occur as full 64-bit literal
pointers in their respective delay-IAT slots. This is a useful positive control
for the pointer search and section mapping.

At `0x141da0a28`, Capstone decodes only `sub edx, ecx` before stopping.
Objdump independently reports an invalid instruction at `0x141da0a2a` and
several more shortly afterward. Treating this as a conventional delay-load
stub or tracing its accidental decoded branches would be unsound.

The relocation inventory is 105,953 DIR64 entries and 277 padding entries;
85,222 non-padding entries lie in .rdata and 20,731 in .data; none lie in .text.
Relocations adjust absolute data pointers for ASLR. They do not explain away
the missing RIP-relative string references: ordinary intra-image RIP-relative
displacements are invariant under a uniform image-base slide.

## Xref search scope and limitations

The helper examines every possible start (including overlapping candidates) in
sections flagged executable, covering:

- `FF 15` indirect calls and `FF 25` indirect jumps through RIP-relative slots.
- REX-prefixed RIP-relative LEA, MOV-load and MOV-store forms.
- `E8` direct calls and `E9` direct jumps to initial thunk addresses.
- Full-file 64-bit preferred-address pointers, correlated with relocations.

Targets include all 15 Steam delay-IAT slots and initial thunk addresses, plus
seven exact NUL-terminated config/interface/error literals:
`Multiplayer.IsDedicatedServer`, `Debug.IsDedicatedServerDll`,
`Debug.LaunchMode`, `steam.gameServer.steamPort`,
`steam.gameServer.gamePort`, `SteamGameServer014`, and
`Failed to initialize game server API.`.

Result: **zero instruction-reference candidates** for these targets, and exactly
15 absolute-pointer hits, all the expected Steam delay-IAT initial values.
There were no preferred-VA literal pointers to the selected strings or IAT slots.
The final overlapping scan is retained in server-call-paths-overlap.json.

This is an encoding-based candidate search, not whole-program disassembly.
It does not cover every possible instruction, hashed/assembled references,
interior-string references, computed calls, or code after a loader transformation.
No candidate is a validated reachable caller simply because its bytes match.

## Next evidence needed

1. Obtain a legitimately supplied analysis-friendly build or matching native
   symbols/source from the developer, or an explicitly authorized supported
   diagnostic artifact that exposes the actual loaded code. Do not decrypt,
   patch, bypass protection, or run this game as part of this static task.
2. On such an artifact, bind its own hash and map the four IAT references above
   to caller functions; establish init arguments, gates, cleanup, and callers
   of those callers before asserting a game-specific dedicated path.
3. Follow config registration/defaults and getter callers, then correlate with
   resource-script evidence being investigated separately. Literal names and
   generic Steam infrastructure do not establish user-settable launch flags.
4. A runtime-capable isolated Windows test environment is the next evidence
   step. The user has authorized continuing the investigation, but no game-runtime
   control is available in the current tool set; host access and save isolation
   must be established before launching. Host capacity, no-player simulation and persistence remain
   unproved even if a native server branch is eventually recovered.

No dedicated/headless switch recipe is justified by this pass.
