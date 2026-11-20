# Copied NAS save evidence

## Scope and custody

Read-only reproduction performed 2026-11-20, 11:49:05–11:49:09 UTC, against the supplied NAS share's `sample-saves/remote`, `sample-saves/after move/remote`, and `sample-saves/base`. Authentication used the existing local credentials file without printing or copying its contents. Only SMB listing, directory selection, and download commands were issued; no NAS uploads/deletions, original-save replacement, game launch, or Cloud changes occurred.

Private evidence is under ignored `private-evidence/saves/nas-review-20261120/`. It contains `pass1/{before,after,base}`, an independent `pass2/`, four recursive metadata listings per source, download logs, SHA-256 manifest, inspector outputs, and comparison reports. Actual account/vehicle identifiers and raw saves are not included in this document.

| Source label | Files per download | Bytes | Four metadata listings stable | Two independently downloaded hash manifests equal |
| --- | ---: | ---: | --- | --- |
| before | 28 | 1,116,428 | yes | yes |
| after | 28 | 1,118,560 | yes | yes |
| base | 6 | 177 | yes | yes |

Each pass listed the source recursively immediately before and after downloading. Equality compares file/directory listings including names, sizes, and displayed modification timestamps; free-space footer lines are excluded. Every downloaded file was SHA-256 hashed and compared across passes, including relative names and sizes. All SMB calls succeeded without reported `NT_STATUS_` errors.

This establishes stable supplied-copy contents during acquisition, not atomicity or consistency of the original game capture. SMB listing timestamps have finite precision, and source-side hashes were not computed directly: hash equality is between two separate downloads. No host/guest observation manifest accompanies these samples.

The `base` sample has a small sandbox JSON, shared settings, four zero-byte logs, and empty account-storage/mod-cache directories. It supplies no additional campaign/map snapshot or nonempty runtime log that establishes co-op activity.

## Reproduced inventory

Both snapshots have two campaign wrappers, with `objVersion` 8 and 9. The unprefixed campaign is byte-identical across snapshots.

| Campaign | Snapshot | Owned total | Warehouse descriptors | Occupied garage slots | Residual owned count |
| --- | --- | ---: | ---: | ---: | ---: |
| CompleteSave.cfg | both | 5 | 2 | 0 | 3 |
| CompleteSave1.cfg | before | 19 | 16 | 1 | 2 |
| CompleteSave1.cfg | after | 20 | 16 | 1 | 3 |

The active profile's `saveSlot` is 1 in both copies. The second campaign's Fleetstar count increases from one to two; its Loadstar count stays one. Residual count is arithmetic only, **not** a verified number of deployed vehicles. Warehouse contents change despite unchanged list length. Preserve complete descriptors and relationships, not just truck-type totals.

All seven map containers in each snapshot decode successfully with the existing length/zlib/trailer checks. Four are level-state files and three mud-map files. Trailer bytes remain `4b173401` for prefixed files and `47173401` for unprefixed files; trailer semantics remain unknown.

## Snapshot changes and semantic refinement

Existing `compare_snapshots.py` reports 7 changed, 21 unchanged, 0 added, 0 removed files, and 0 decoding errors.

| Changed file | Decoded/raw length delta | Interpretation |
| --- | ---: | --- |
| 1_fog_level_us_02_01.cfg | +166 | Raw CFG change; not decoded as an sts map |
| 1_sts_level_us_02_01.cfg | +60 | Only changed sts map; 327,879 → 327,939 decoded bytes |
| CompleteSave1.cfg | +1,603 | Campaign JSON changes |
| CommonSslSave.cfg | 0 | Shared JSON changes |
| GameVersionSave.cfg | 0 | Parsed JSON values equal |
| user_profile.cfg | 0 | Parsed JSON values equal |
| user_social_data.cfg | 0 | Parsed JSON values equal |

The last three are byte-level differences without semantic JSON differences; they are not evidence of changed version, selected profile, or social state. The comparator intentionally performs positional comparison, not semantic JSON or insertion-aware alignment.

Campaign keys changed: `objectiveStates`, `gameTime`, `saveTime`, `gameStat`, `persistentProfileData`, and `tutorialStates`. Within persistent profile data, changed keys are `distance`, `trucksInWarehouse`, and `ownedTrucks`. Alaska distance increases 0 → 383. Shared `platformStatsInfo.totalDistanceMeters` increases 4,833 → 5,216. This is not a movement-only controlled experiment.

Selected raw SHA-256 fingerprints:

| File | Before | After |
| --- | --- | --- |
| CompleteSave.cfg | `31df28eacf09de77352e0fceba5317279f4f74e0f83f11c0c481cce11266baac` | same |
| CompleteSave1.cfg | `6e9d2ce442c5d17f8424373bf0a7eae24ef5ffcd12d213a0e6694c511ac922c9` | `94fa1d59d5c1b97eb7b1e2ffbd3a09c9432060a04627dc472f7179b187b3d9bd` |
| 1_sts_level_us_02_01.cfg | `f003f31a14c8aa28423220efca54b078db84277ed9c669bed227a902327e0eec` | `6f61375c590dbc6c4864796c6895b7ce42c7b3b17a285430f163ad2ff7becbc5` |

## Reproduced candidate movement

In both decoded `1_sts_level_us_02_01.cfg` payloads:

- `international_loadstar_1700` begins at byte 61,761.
- A matching stable 38-character printable instance identifier begins at 61,794, followed by NUL. The two bytes immediately before it are `27 00`, consistent with a little-endian length of 39 including NUL. This is a local framing observation, not a general parser specification.
- Searching that exact identifier using the existing comparator finds one occurrence in this map per snapshot and none in the other top-level CFG payloads. The identifier is kept private.
- A plausible little-endian 16-float transform starts at byte 62,956. Its final row changes from approximately `(722.598083, 86.151352, -212.935226, 1)` to `(393.126587, 83.681488, -362.075623, 1)`.
- Euclidean translation displacement is **361.663414 map units**. Rotation components also change; homogeneous entries are consistent with a transform matrix.

The prior findings record the player's confirmation that the driven vehicle was the Loadstar in North Port. This reproduction independently confirms the bytes, not that gameplay observation. Coordinate units, axis conventions, complete record boundaries, authoritative restore matrix, and ownership are not established by the float cluster. Do not reuse these offsets for other saves.

## Is there co-op evidence?

No observed connected/guest-left/restarted sequence is present. Both campaigns in both snapshots have:

- `MULTIPLAYER_SESSIONS_PLAYED = 0`
- `MULTIPLAYER_MISSIONS_FINISHED = 0`
- `MULTIPLAYER_MONEY_EARNED = 0`

Shared `platformStatsInfo.totalCoopSessions` is also zero in both snapshots. Ordinary `SESSION_NUMBER` changes 2 → 3 in the second campaign; it is not the multiplayer-session counter. Social data contains a blocked-player list, but it is semantically unchanged and does not identify a participant in this capture. Neither field names nor a social list prove co-op.

These facts provide **no positive evidence of guest truck persistence**. They do not prove co-op has never occurred: counters may be incomplete, profile-specific, reset, or updated under conditions not understood here. No host/guest role, disconnect time, truck visibility/control observation, or restart test can be reconstructed reliably from this sample alone.

## Requirements and gates for persistent shared vehicles

1. **Identity and complete state:** Establish per-instance identities, ownership, full descriptor/record boundaries, map identity, authoritative transform, fuel/damage/add-ons, cargo/trailer/winch relationships, and all cross-file references. Type counts cannot safely serve as inventory records.
2. **Serialization and disconnect behavior:** Capture both host and guest at baseline, connected/parked, guest-left/host-saved, and host-restarted/guest-absent stages. Correlate records with actual visibility, enterability, and driving observations. Follow [the existing capture protocol](COOP_CAPTURE_PROTOCOL.md).
3. **Runtime authority:** Determine whether guest departure deletes/despawns/transfers the vehicle and whether the host can own or simulate it independently. A database of snapshots does not prevent runtime cleanup. Ownership-transfer hooks or a runtime change are research possibilities, not demonstrated capabilities.
4. **Safe restoration:** Do not build a production save writer until framing, IDs, schema/build compatibility, trailer meaning, transaction/linkage requirements, and round-trip restore behavior are verified on disposable copies. Prevent duplicate instances and inventory/currency duplication across logout/rejoin/recovery/garage paths; test rollback and interrupted saves.
5. **Independent replication test:** Repeat with another truck and separately vary attachments, fuel/damage, garage/recovery, map travel, reconnect, normal restart, and crash. A retained string reference alone never satisfies persistence.
6. **Hosting capacity:** A stock unattended player host occupies a player slot. Four humans plus a non-player host requires separate proof of supported runtime capacity/server operation; these saves do not provide it.

## Requirements and gates for separate multiplayer profiles

- Isolate **every participating client's** writable save environment. A different campaign slot alone is insufficient: these copies demonstrate shared profile/common/social files outside slot-specific campaign files.
- Before any future game launch, identify exact live/test paths, protect and hash original campaigns outside active save/Cloud paths, disable Cloud for the test, and check symlinks/junctions/aliases and filesystem write access.
- Verify a test-only save changes only the intended isolated tree and that originals retain their hashes. The current read-only acquisition does not satisfy this launch-time gate.
- Keep the multiplayer campaign/fleet authoritative and separate. Optional solo-fleet imports must be explicit one-time snapshots with stable identity remapping and duplicate/entitlement checks; never silently write multiplayer progression back to original solo campaigns.
- Preserve full per-profile and shared save state together for rollback. Keep Cloud disabled through the experiment; resuming Cloud or moving saves back requires a separate reconciliation decision.

## Reproduction and verification

From the repository root, against the completed ignored copies:

```bash
python3 -m unittest discover -s tests -v
python3 tools/inspect_saves.py private-evidence/saves/nas-review-20261120/pass1/before > private-evidence/saves/nas-review-20261120/inspect-before.json
python3 tools/inspect_saves.py private-evidence/saves/nas-review-20261120/pass1/after > private-evidence/saves/nas-review-20261120/inspect-after.json
python3 tools/compare_snapshots.py private-evidence/saves/nas-review-20261120/pass1/before private-evidence/saves/nas-review-20261120/pass1/after > private-evidence/saves/nas-review-20261120/compare.json
```

The private acquisition script records exact SMB commands and verifies two downloads; its analysis script extracts the candidate marker locally, keeps it in ignored output, and uses the existing comparator. A first exploratory four-byte string-length hypothesis failed ASCII decoding; inspecting framing showed the two-byte length above. No decoder or save files were modified to make that hypothesis pass.

Verification: **14 existing unit tests passed**; both inspector runs completed; comparison reported zero decoder errors; all 62 downloaded files per pass matched the corresponding second-pass hashes. No new parser/writer is claimed. No commits or pushes were performed.
