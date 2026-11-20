# Compiled script evidence

Checked 2026-11-20. Static, read-only resource analysis; no game execution or modification. This expands the historical text-only `initial.pak` search into its three compiled SSL bundles. It does not establish a server launch recipe.

## Acquisition

Two independent SMB downloads of `game-copy/preload/paks/client/initial.pak` match: 29,925,376 bytes, SHA-256 `07f98eec2d802b04ba5917f6b275c4de95fff2c4fce01bb8cfdd1c1770dba7a6`. Copies are ignored under `private-evidence/resources/`. ZIP parsing inventories 12,171 entries: 12,152 XML, 13 STR, three SSL bundles, and three other entries. No raw resources are committed.

## Verified container framing

`tools/inspect_ssl_bundle.py` validates the observed S3DB header, 2,284 length-prefixed module names, a size table, and exact consumption of the complete bundle. Every module begins with the observed SSLB header and its declared payload length equals its directory size minus 16. All three shipped debug/profile/release bundles pass these checks for all modules (6,852 framed module records). These checks establish module attribution and boundaries, not bytecode interpretation.

| Bundle | Bytes | SHA-256 |
| --- | ---: | --- |
| initial_debug.sslbundle | 13,784,773 | `2b9f7abd90bb1ded844bf640002c926d40c2899562ad77ef24269d5ce6a2bc43` |
| initial_profile.sslbundle | 13,256,917 | `ff287127d3fb28ddec018833c2123dd2316638a6bd4ed96af606b8b596f1f69a` |
| initial_release.sslbundle | 13,230,511 | `22ce203da583faba881e148bec83af1a2e87d37c47328c6fb59e829937df8ad8` |

## Attributed leads

Offsets below are decimal positions in the **release bundle**, not executable offsets. Names preserve shipped spelling.

| Literal | Bundle offset | Owning module | Module start | Relative offset |
| --- | ---: | --- | ---: | ---: |
| NetDeleteDisconnectedUserTrucks | 1407844 | game.game_modes.game_session | 1364060 | 43784 |
| SetServerDedicated | 4262653 | main.application_modes.application_backend_network_blackboad | 4259651 | 3002 |
| LEECH_DEDICATED_SERVER_MODE | 4512607 | main.ds_config_consts | 4511495 | 1112 |
| Multiplayer.IsDedicatedServer | 11934642 | autotest.auto_test_abstract | 11932880 | 1762 |
| --startup | 12152857 | cmd_line_options.cmd_line_options | 12150675 | 2182 |

All five leads also occur in the corresponding debug/profile modules. The selected game_session and network-blackboard module hashes match between release and profile; ds_config_consts and cmd_line_options hashes match across all three variants. This is byte identity, not evidence that any variant is selected at runtime.

Important correction to interpretation: the dedicated predicate's compiled-script occurrence is in an **autotest** module. It must not be presented as an ordinary user-facing server launcher. The ds_config module also names matchmaking/backend settings; these may be shared engine infrastructure rather than SnowRunner gameplay-server support. No backend token values were obtained or needed.

The game_session module contains names for adding saved trucks/cargo to a network entity manager, preparing to leave, and deleting disconnected users' trucks. That is a narrower target for the persistence question, but a symbol name does not establish when deletion runs, what it removes, or a safe way to disable it.

## Reproduction

Use Python `zipfile.ZipFile` to read the three entries `[ssl_cache]\\initial_{debug,profile,release}.sslbundle` from the private archive and pass the returned bytes to `tools.inspect_ssl_bundle.inspect`. This avoids extracting the archive. The CLI accepts a privately extracted bundle:

```sh
python3 tools/inspect_ssl_bundle.py /private/initial_release.sslbundle --marker NetDeleteDisconnectedUserTrucks --marker SetServerDedicated --hits-only
python3 -m unittest discover -s tests -v
```

Generated manifests belong under ignored private evidence. The parser deliberately rejects unfamiliar headers, inconsistent lengths, and trailing/truncated data; it does not write, repack, decompile, or execute any resource. Synthetic tests cover offset attribution and malformed framing.

## Next investigation

Recover the compiled payload schema and reference relationships for the named modules before inferring control flow or configuration values. Continue native server-init call-path work in parallel. A controlled host/guest runtime experiment remains necessary to establish actual truck retention and four-human non-player hosting.
