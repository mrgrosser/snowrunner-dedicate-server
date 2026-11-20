# SnowRunner server binary analysis

Date: 2026-11-20. Scope: read-only NAS inventory and static inspection of selected copied files; no game execution, patches, NAS writes, commits, or publishing.

## Decision

**No working dedicated/headless server entrypoint is established.** The executable contains more server infrastructure than the two previously recorded config strings alone: it has a real delay-import table referencing Steam game-server initialization and callback APIs, plus server-specific configuration names. That is a useful next investigation target, not proof of an available dedicated runtime or a fifth, non-player host slot.

The supplied Sources tree has no separately named dedicated-server executable/DLL or server launch script. This is a bounded filename inventory, not proof that no ordinary-named DLL embeds server functionality or that no separate server distribution exists. Do not advertise `-dedicated`, `-headless`, or guessed `--set` paths as working commands.

## Tool availability / evidence class

Applied the installed `reverse-engineer-anything` skill and its connection-and-recovery guidance. No native REA tools were exposed in this child tool catalog. `command -v rea` failed; explicit common launcher paths `/home/it/.npm-global/bin/rea`, `/usr/local/bin/rea`, and `/usr/bin/rea` were absent. PATH includes the npm prefix. `ghidra`, `analyzeHeadless`, `rizin`, and `radare2` were not found on PATH; Python `capstone` and `pefile` were unavailable. These checks do not prove absence elsewhere or diagnose gateway registration.

Continued with **non-REA static evidence** using GNU objdump/strings 2.42 and Python standard-library parsing. No REA Evidence IDs, decompiler output, runtime observations, registration repairs, package acquisition, or heavyweight engines were produced. `rg` was unavailable, so subsequent searches used grep/Python.

## Acquisition and identity

Source share `//10.10.0.25/Snowrunner`, using the existing authentication file without printing its contents. Selected files were fetched twice independently with `smbclient get`; each pair had matching full-file SHA-256 and NAS-reported lengths. This establishes repeatable reads, not publisher authenticity or a transactionally consistent whole installation.

| NAS path below `game-copy/` | Bytes | SHA-256, both reads |
| --- | ---: | --- |
| `Sources/Bin/SnowRunner.exe` | 46,810,152 | `d46623b23808d19a40f7ebeec15332d11f97317637ec4d4e072a501bc78a77c8` |
| `Sources/Bin/dxvk.conf` | 29 | `fdebdf6cba1d8216bc69d90a4db25fa91abcb91d5810fce38ca5da2cf74eaa38` |
| `Sources/Bin/CompileShaders_README.txt` | 2,714 | `ca1055c8120b2844d22b2c0a84cdd09fca2ae6e9dd549404407b83f08434beed` |

Copies and inspection outputs are in ignored `private-evidence/binary/`. Verification copies use `.verify` in the filename. `git check-ignore` confirmed the executable is ignored. No large PAKs, editor executable, or DLL payloads were downloaded in this pass.

Retained local evidence: `sources-inventory.txt` (recursive Sources listing), `acquisition.txt`, `recheck.txt`, `pe-headers.txt`, `strings-ascii.txt`, `strings-utf16.txt`, and the six selected file copies. Some focused Python/disassembly outputs exist in the task transcript rather than standalone files; the addresses and parsing method are recorded here for reproduction.

## Executable layout and launch boundary

Observed PE facts:

- Native AMD64 PE32+, Windows GUI subsystem (2), image base `0x140000000`; CLR directory is zero.
- PE timestamp says 2026-10-23 16:07:03 UTC. This is header metadata, not a verified release date.
- AddressOfEntryPoint RVA `0x2dcd310`, preferred VA `0x142dcd310`, file offset `0x2c68b10`, in `.bind`, not the main `.text` section.
- `.text`: RVA `0x1000`, file offset `0x600`, virtual size `0x21be17f`.
- `.rdata`: RVA `0x21c0000`, file offset `0x21be800`, virtual size `0x7e6a30`.
- `.bind`: RVA `0x2dcd000`, file offset `0x2c68800`, size `0x39248`.
- Entry disassembly saves registers, calls `0x142dcd3d0` at `0x142dcd345`, restores registers and returns at `0x142dcd36f`. It does not directly identify the application-level command parser/main loop. A loader/wrapper layer is a reasonable inference, not a proved unpacking or DRM diagnosis.
- Export directory has 371 named exports; the inspected beginning is Scaleform C++ infrastructure, not evidence of a server API. Export inventory was not deeply classified.

An exhaustive byte-pattern search over the main `.text` virtual extent for seven-byte `48/4c 8d` RIP-relative LEAs to the two dedicated strings found none. Full-file searches for their preferred-VA 64-bit literal pointers also found none. The same checks on `Debug.LaunchMode` found none. These deliberately narrow searches do **not** establish dead code: address construction, relocations, hashes, other instruction encodings, or wrapper transformations are unresolved. No xref or function was validated from these negative results.

## Imports: client requirements and real server API references

Ordinary PE imports include `d3d11.dll` / `D3D11CreateDevice`, `dxgi.dll`, USER32 / `CreateWindowExW`, DINPUT8, `XAudio2_9Redist.dll`, EOSSDK, `pros.sdk.x64.dll`, HFFBSDK, GFSDK Aftermath, WS2_32, MSVCP140, VCRUNTIME140, and Universal CRT API-set DLLs. KERNEL32 imports include `GetCommandLineW` and LoadLibrary variants; SHELL32 includes `CommandLineToArgvW`.

These support a Windows graphical retail-client interpretation. Imports alone do not prove that a GPU/window/audio device must be instantiated on every possible branch. Native Linux service support is not demonstrated. Windows dependency provisioning (or a separately validated compatibility environment), game resources, and platform identity remain relevant even if a headless branch is eventually found.

The delay-import directory at RVA `0x2998b44` has three nonzero descriptors followed by the terminator:

- `D3DCOMPILER_47.dll`: D3DPreprocess, D3DDisassemble, D3DCompile.
- `ATICompressDLL.dll`: ATI_TC_DLL_ConvertTexture, ATI_TC_DLL_CalculateBufferSize.
- `steam_api64.dll`: 15 named imports, including **SteamInternal_GameServer_Init**, **SteamGameServer_RunCallbacks**, **SteamGameServer_GetHSteamUser**, and **SteamInternal_FindOrCreateGameServerInterface**, alongside SteamAPI initialization/callback/shutdown functions.

This is format-aware delay-import evidence, stronger than arbitrary string presence. It still does not establish invocation or successful initialization. The descriptor was decoded using PE optional-header data-directory index 13, eight little-endian DWORDs per 32-byte descriptor, section-based RVA mapping, and 64-bit import-name thunks. Ordinary `objdump -p` import headings alone would miss this Steam dependency.

The NAS inventory includes `steam_api64.dll` (298,384 bytes), EOSSDK (18,266,584), and pros SDK (11,592,704), but their content/exports and authenticity were not inspected. No dedicated DLL name is apparent in recursive `Sources/Bin` or `Sources/BinEditor` listings.

## Precise string leads (not verified switches)

All offsets below are hexadecimal **file offsets** in the executable above. These literals are in `.rdata`; preferred VA = `0x140000000 + file_offset + 0x1800`. Actual loaded addresses may differ due to ASLR.

| Offset | ASCII literal | Interpretation boundary |
| --- | --- | --- |
| `0x2299950` | `Multiplayer.IsDedicatedServer` | Config-looking dedicated predicate; semantics/default/reachability unresolved |
| `0x22fc6e0` | `Debug.IsDedicatedServerDll` | DLL-specific predicate; does not prove that such a DLL shipped |
| `0x22c5500` | `steam.gameServer.modsDir` | Steam server config lead |
| `0x22c5520` | `steam.gameServer.productName` | Product configuration lead |
| `0x22c5540` | `steam.gameServer.productDesc` | Product configuration lead |
| `0x22c5560` | `steam.gameServer.productVersion` | Version configuration lead |
| `0x22c5580` | `steam.gameServer.gameServerAccountToken` | Token field name only; no token value obtained |
| `0x22c55a8` | `steam.gameServer.steamPort` | No default or operational port established |
| `0x22c55c8` | `steam.gameServer.gamePort` | No firewall rule justified by this string |
| `0x22c55e8` | `steam.gameServer.queryPort` | No default port established |
| `0x22c58a8` | `SteamGameServer014` | Interface-name lead |
| `0x22c59e8` | `Failed to initialize game server API.` | Failure-path text, not an observed failure |
| `0x22c5a10` | `steam/game/server` | Logging/category lead |
| `0x238e370` | `Multiplayer.IsServerScene` | Server scene lead, not necessarily dedicated |
| `0x238e3b8` | `debug_server.dsc` | Referenced name, not an inventoried launch file |
| `0x238e3d0` | `Debug.DscFileNameServer` | Debug-script configuration lead |
| `0x2390dc0` | `Debug.AutomationMode` | Automation is not synonymous with headless |
| `0x2390e58` | `ConCfg.RunAutoexecStartup` | Startup configuration lead |
| `0x2390eb8` | `ConCfg.AutoexecStartupScripts` | Startup script lead |
| `0x2391080` | `startup` | Parser vocabulary only |
| `0x2391088` | `game_cfg` | Parser vocabulary only |
| `0x2391118` | `Debug.LaunchMode` | Allowed modes unresolved |
| `0x2392540` | `+connect_lobby` | Lobby launch lead |
| `0x23926c8` | `--startup --set /Config/EpicLoginConfig/provider epic` | Concrete embedded argument template for Epic provider; not a dedicated template |
| `0x2392814` | `--set` | Generic configuration syntax lead |

ASCII and UTF-16LE string searches found no `headless`, `nullrender`, `norender`, or `nosound` match. Dedicated-related ASCII hits additionally included GPU-memory/Vulkan allocation text, which is unrelated to multiplayer. Negative string searches cannot rule out hashed, encoded, assembled, or differently named options.

## Supplied launch configuration / inventory boundary

`dxvk.conf` contains only `d3d11.dcSingleUseMode = False`; it is not a server configuration. The Russian shader README concerns shader build batches/platforms, compiler flags `--jobCount`, `--debug`, and `--preserve-intermediates`, and runtime shader debugging. It establishes no server launch instructions. Referenced batch files were not present in the Sources listing.

The `game-copy` root lists Sources, Media and preload. Media's top-level child is `Mod Templates`; preload/paks has `client`. Only Sources was recursively inventoried in this assignment; archives, Mod Templates and client PAKs are outside this pass's negative filename claims. Earlier FINDINGS.md records an initial.pak text scan with no dedicated/headless matches; that historical scan was not repeated or expanded here.

## Requirements, unknowns and next focused tests

1. **Static next step:** make an existing compatible REA native provider available without changing this gateway in the current task; bind the exact SHA-256 above. Inspect the `.bind` entry handoff and recovered application entry before tracing config registration/getters. A normal main-entry assumption is not yet justified.
2. Trace the two dedicated predicates and `Debug.LaunchMode` through registration, default values, getter callers, and parser path construction. Determine whether these are read-only computed flags, development-only values, or user-settable configuration. Verify whether the DLL flag selects a distinct build or runtime library.
3. Follow the actual delay-import thunk for SteamInternal_GameServer_Init to callers, gates and cleanup; distinguish compiled generic SDK support from SnowRunner lobby creation. Inventory any dynamically assembled DLL filename before requesting another specific NAS download.
4. Inspect narrowly selected startup/config records from existing resource evidence for `ConCfg`, server scene, debug_server.dsc, and launch-mode enumeration. Do not bulk-copy game assets merely because the first string scan was negative.
5. **Only in a separately authorized isolated runtime experiment:** provision the verified Windows client dependency set and isolated saves/cloud state. Measure window/GPU initialization, platform authentication, hosting, player capacity and simulation when no player is active. No launch command is validated by this report.
6. Separately test guest-disconnect truck retention, host restart restoration and four-human capacity. Even a true dedicated launch would not automatically solve campaign persistence or guest cleanup semantics.

Question status: executable identity/layout **answered**; Sources dedicated-file inventory **answered within stated boundary**; Steam game-server import presence **answered**; launch/config mechanism **partially answered**; functioning headless startup, non-player host capacity, DLL semantics and durable multiplayer persistence **unresolved**.

## Minimal reproduction

From repository root, after the selected SMB copies exist:

```sh
sha256sum private-evidence/binary/SnowRunner*.exe
objdump -p private-evidence/binary/SnowRunner.exe
objdump -h private-evidence/binary/SnowRunner.exe
strings -t x private-evidence/binary/SnowRunner.exe
strings -el -t x private-evidence/binary/SnowRunner.exe
objdump -d --start-address=0x142dcd310 --stop-address=0x142dcd380 private-evidence/binary/SnowRunner.exe
```

To reacquire one selected file without changing the NAS:

```sh
smbclient //10.10.0.25/Snowrunner -A /home/it/.config/jarvis/unas-smb.credentials -c 'get game-copy\Sources\Bin\SnowRunner.exe private-evidence/binary/SnowRunner.exe'
```

No credentials or proprietary binary contents should be added to version control; this report records bounded metadata, short investigation strings and verification hashes only.
