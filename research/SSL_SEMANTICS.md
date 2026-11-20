# SSLB wire structure and bounded semantics

## Verified 2026-11-20

Read-only standard-library Python inspection of `private-evidence/resources/initial.pak`; no game execution, binary patching, DRM work, or proprietary payload dumps. REA skill methodology was consulted; no REA tools are exposed in this child session, so these are ordinary Python observations, not REA Evidence records. Existing `tools/inspect_ssl_bundle.py` was read and reused unchanged.

`tools/inspect_ssl_wire.py` parses the SSLB payload starting at module byte 16 using protobuf wire rules (uint64 varints, length-delimited records, fixed32/fixed64; bounded lengths/field counts). **All 2,284 modules in each of debug, profile, and release parse completely: 6,852/6,852, zero failures.** This establishes protobuf-wire compatibility, not the original `.proto` schema or a bytecode decoder.

Reproduce:

```sh
python3 tools/inspect_ssl_wire.py private-evidence/resources/initial.pak
```

## Layout established

Top-level field 6 is a repeated UTF-8 string table in the three target modules. Field 7 records contain class-like names and member-like records referencing those string indices. Field 8 contains further nested structures; their executable semantics remain undecoded. Field 5 has heterogeneous typed records, not safely describable as only constants or instructions yet. All indices below are zero-based; field numbers use protobuf numbering.

| Module | Field 5 records | Field 6 strings | Field 7 records | Field 8 records |
|---|---:|---:|---:|---:|
| main.ds_config_consts (all variants identical) | 6 | 75 | 3 | 0 |
| cmd_line_options.cmd_line_options (all variants identical) | 73 | 101 | 2 | 23 |
| game.game_modes.game_session (release/profile identical) | 1007 | 1167 | 11 | 176 |
| game.game_modes.game_session (debug) | 1023 | 1222 | 11 | 176 |

Module SHA-256 identities:

- ds_config_consts: `6f5be7e34bfc5d642801e4dcdb2c2f12397139a0574dfb195346dc3f645a7858`
- cmd_line_options: `3823c0c49a9c6d961c9b8dbf20c03f29417748ae495c1cfed40d6e16fe387159`
- game_session release/profile: `8013f2385e0b770c497ab87106cee0b7b246b65a81e9e2fc51b3d50e77fa6452`
- game_session debug: `81fdf5221cba7097f68a701091504f6ccb0f7278e32ae7beab0ec81ec62db4d4`

## Constant-value recovery (structural inference, not execution)

In `main.ds_config_consts`, each top-level field-7 record has field 1 indexing its class name. Its repeated field-3 member records have field 1 indexing a member name and nested field 5 containing a typed literal. This independently pairs names with values; it is stronger than adjacency in strings output.

For `SessionTypeServer` (class-name string index 4), member names DEBUG_CONNECT, MATCHMAKING, OFFLINE, MATCHMAKING_PRIVATE have nested literal `{1:1,2:0}`, `{1:1,2:1}`, `{1:1,2:2}`, `{1:1,2:3}` respectively. The same 0–3 sequence occurs for `LeechDSMode` (class-name index 9): VIRTUAL_DSM, MANAGED_MODE, AMAZON_GAMELIFT_MODE, LOGS_ONLY_MODE. Strong candidate numeric enum values are therefore 0, 1, 2, 3 in each listed order. Exact scalar signedness/type schema is not recovered (raw protobuf varints alone cannot distinguish int/uint/zigzag); do not promote these to verified operational enum settings.

For `DsConfigConsts` (class-name index 14), 28 member records use nested literal `{1:4,5:<string index>}`. Selected recovered name-to-string mappings:

| Member | String literal |
|---|---|
| SECTION_GAME_CONFIG | GAME_CONFIG |
| IS_DLL_SERVER | isDllServer |
| IS_AUTOCLOSING_SERVER | isAutoClosingServer |
| IS_CHECKPOINT_RESTART | isCheckpointRestart |
| SESSION_TYPE_SERVER | sessionTypeServer |
| EXTERNAL_SESSION_ID | externalSessionId |
| CLIENTS_AT_START | clientsAtStart |
| CLIENTS_AT_START_WAITING_TIMEOUT | clientsAtStartWaitingTimeout |
| SHUTDOWN_ON_NO_CLIENTS_JOINED_TIMEOUT_SEC | shutdownOnNoClientsJoinedTimeoutSec |
| LEECH_DEDICATED_SERVER_IP | leechDedicatedServerIp |
| LEECH_DEDICATED_SERVER_MODE | leechDSMode |

Example exact structural chain: class field 1 = 14 (`DsConfigConsts`), member field 1 = 18 (`IS_DLL_SERVER`), member field 5 = `{1:4,5:19}`, string 19 = `isDllServer`. This supports a config-key constant, **not** a default value for that key, a working launch switch, a recognized config file, or a reachable dedicated-server mode. The module has no top-level field-8 records.

## Requested API names

`NetDeleteDisconnectedUserTrucks` is string slot 1050 in release/profile game_session and slot 1066 in debug. `SetServerDedicated` is absent from the complete string tables of all three selected modules in all variants. String presence alone is not a call site. A focused follow-up **does recover declaration-to-body linkage**, stronger than string presence:

- In release/profile game_session, class record `7[10]` names `GameSession`. Its member `3[231]` contains raw scalar fields `{1:1050,2:235,3:2,4:128}`: name index 1050 and candidate body index 128. Top-level body `8[128]` independently names string 1050 through its nested field 2 / field 1. Its field 5 is a 414-byte wire record containing 69 repeated field-1 varints. This is an actual named compiled member/body association, **not** an incoming call reference or decoded deletion algorithm.
- A bounded whole-release-bundle name search found `SetServerDedicated` in exactly one other module, `main.application_modes.application_backend_network_blackboad` (spelling as shipped). Its SHA-256 is `e5a4b39931b4a56e433b99688456c5edeb41a33156038d4499c4e2d2d7013c73`. Class record `7[0]` names `ApplicationBackendNetworkBlackboard`; member `3[69]` has raw scalar fields `{1:99,2:73,3:2,4:30}`. Body `8[30]` independently names string slot 99 (`SetServerDedicated`). Its field 5 is 30 bytes comprising five repeated field-1 varints.
- Those five raw words are `2147483653,2147483655,2147493692,2147483650,2147483923`. Their decoding is deliberately not guessed; the short body could only become behavior evidence after identifying the interpreter's instruction schema.
- The helper reproduces both named-member/body associations as `body_name_matches` and the 36 constant-member records (eight enum-like, 28 string-like). It additionally includes the out-of-three module only when the exact requested API name occurs.

This narrows the next static target precisely: the named body and its callers, rather than scanning unrelated strings. It does not establish that either function is called during retail gameplay, that the dedicated setter starts a server, or that disconnected trucks are actually deleted.

## cmd_line_options boundary

This module's string table includes `--set` (slot 90), `/` (91), `--startup` (92), and member-like names `GetCmdLine`, `ImplementConfigVariables`, `ImplementVariable`. Its field-4 / repeated-field-2 record for `SetConfigVariable` contains `{1:23,2:67,3:243,4:0}`; only field 1 is interpreted here as the matching string index. The other numeric fields are not indiscriminately treated as string indices. These are concrete locations for a later serializer/config-consumer investigation, **not a verified launch syntax**.

Final helper verification succeeded across all three variants: both API names have matching declaration/body name indices in every variant. Body indices remain 128 and 30 respectively; debug shifts the string indices to 1066 and 100. Each variant yielded 36 recovered constant records. Neither requested API appears in the command-line module.

## Next evidence needed

Recover field-4 import/reference-table layout and trace numeric indices into field-5/field-8 structures. To prove a call, need a validated instruction schema or native SSL loader/interpreter mapping and the containing control-flow path. To prove dedicated configuration operational, need the actual loader path and config ingestion; recovered key constants do not establish either. No working switches are asserted.
