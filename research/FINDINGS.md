# SnowRunner persistence investigation

## Scope

Persistent campaign for up to four human players, with multiplayer vehicle state separate from original single-player saves. All inspections used provided copies. No game launch, patching, or save replacement has occurred.

## Verified from supplied files

- CompleteSave.cfg and CompleteSave1.cfg are JSON wrappers with SslValue campaign data, using objVersion 8 and 9 respectively.
- Their owned truck totals are 5 and 19. Warehouse descriptors number 2 and 16; occupied garage slots number 0 and 1. Ownership totals alone do not locate deployed trucks.
- Truck descriptors contain component configuration, fuel, damage, add-ons, identifiers, and other fields. Preserve raw descriptors rather than rebuilding from a short inventory.
- All seven supplied sts files contain a four-byte little-endian uncompressed length, a zlib stream, and a four-byte trailer. Decoded lengths match headers. Trailers are 4b173401 for the prefixed files and 47173401 for the unprefixed files; their meaning is unknown. This covers four level-state files and three mud-map files.
- Decoded level-state data contains truck and component identifiers. References repeat and include world objects; they are not a reliable count of player-owned trucks. A controlled movement sample identified candidate position data. Ownership, complete record boundaries, cargo relationships, and write support still need verification.
- initial.pak is ZIP-readable and contains 12,171 entries, including truck XML definitions and compiled SSL bundles.
- SnowRunner.exe contains ASCII strings Multiplayer.IsDedicatedServer at file offset 0x2299950 and Debug.IsDedicatedServerDll at 0x22fc6e0. These may be shared engine infrastructure. No functioning server startup mode is established.
- A scan of XML/CFG/TXT/SSO/LUA entries in initial.pak found neither dedicated-server string nor Headless/headless. Compiled bundles were not interpreted.
- Executable log strings reference replication spawn and ownership policies on client disconnect. These provide investigation targets, not confirmed hook addresses.

## Reproducible inspection

Run the commands in README.md from the repository root. The inspector only reads the supplied copies. Its five decoder tests check length, stream integrity, trailer length, and the decompression size limit.

## Confirmed movement in North Port, Alaska

- The player confirmed driving the International Loadstar 1700. The retail English localization maps US_02_01_NAME to North Port.
- In both snapshots, the changed map file was 1_sts_level_us_02_01.cfg. Its decoded length grew from 327,879 to 327,939 bytes.
- In the decoded data, the driven truck's type starts at offset 61,761 and its stable instance ID starts at 61,794. The length-prefixed type and instance ID distinguish it from another Loadstar with the world label WASTE.
- A candidate 4x4 little-endian float matrix starts at offset 62,956 in both snapshots. Its translation changed from (722.598, 86.151, -212.935) to (393.127, 83.681, -362.076), a straight-line change of about 361.66 map units. Nearby transforms shifted coherently.
- The profile's Alaska distance rose from 0 to 383. Its count of owned Fleetstars rose from one to two. Other campaign fields also changed during the capture.
- The Loadstar instance and transform cluster can be matched between these two captures. The engine's authoritative restore transform and guest ownership behavior still need verification.

## Next experiments

1. Establish an isolated test profile and verify save writes and cloud sync cannot reach the original campaign before launching experiments.
2. Repeat controlled captures for another truck, fuel use, garage storage, and trailer attachment, changing one variable per capture.
3. Use decompressed binary differences to identify record boundaries and transforms. Validate on another truck before attempting a writer.
4. Capture host and guest saves before joining, after deploying a guest truck, after guest logout, and after host restart. Track actual in-game observations alongside saves.
5. Trace references to dedicated-server and replication ownership strings in a disassembler. Determine whether the code is reachable in this retail build and how configuration is loaded; do not assume a string is a launch switch.

## Design constraints

The game remains responsible for simulation until an alternative is demonstrated. A persistence database cannot prevent guest cleanup by itself. Keeping a truck in-world may require ownership transfer or a runtime modification before disconnect cleanup. Separate save isolation is necessary on every participating client, not just on the host. Runtime capability determines whether an idle host occupies a player slot. Imported inventory is a snapshot, not proof of DLC entitlement or authoritative multiplayer identity.
