# Public existing-solutions preflight

Checked: **2026-11-20, 13:18 UTC**. Bounded public read-only research using actual `web_fetch` requests; no installs, execution of third-party code, credentials, remote writes, or commits. Read workspace AGENTS.md, project README, FINDINGS.md and DEDICATED_SERVER_DESIGN.md first. This report supplies the previously missing public preflight; the earlier design pass's statement that it fetched no public sources remains historical, not the current research boundary.

## Decision

**No runnable non-player SnowRunner dedicated-server release or implementation was established in the sources inspected.** This is not proof none exists globally. One concrete automation project was found, but it explicitly requires starting ordinary SnowRunner co-op on a separately licensed account and a display. It is a potential full-client-host helper, not evidence of a dedicated simulation runtime, four human guests, or guest-independent truck persistence.

## Publisher and Steam evidence

All URLs below were fetched on the checked date. HTTP 200 means transport success only; extraction and challenge limitations are noted.

| Source | Observed evidence | Boundary |
| --- | --- | --- |
| [Steam SnowRunner store page](https://store.steampowered.com/app/1465360/SnowRunner/) | HTTP 200, untruncated extraction. Lists Online Co-op, desktop client system requirements, and release date May 17, 2021. | Extracted page supplied no dedicated-server binary, server AppID, or launch recipe. Store marketing is not an exhaustive distribution inventory. Do not interpret client hardware requirements as server sizing. |
| [Focus Entertainment SnowRunner page](https://www.focus-entmt.com/en/games/snowrunner) | HTTP 200, untruncated extraction; publisher/developer attribution, shop, support and community links. | Extraction was largely navigation/footer material. No usable server documentation was obtained; dynamic page content may be missing. |
| [Steamworks Game Servers](https://partner.steamgames.com/doc/features/multiplayer/game_servers) | HTTP 200. Documents Steam's game-server API and links separate server-distribution instructions. | Generic developer documentation, not SnowRunner support. API imports in a game do not establish a shipped standalone server. |
| [Steamworks Distributing Your Dedicated Game Server](https://partner.steamgames.com/doc/sdk/uploading/distributing_gs) | HTTP 200. Describes a separate TOOL AppID, depot containing server binaries, release checklist, optional anonymous SteamCMD package inclusion, and testing download/run. | Provides a concrete standard of distribution evidence to seek, not a SnowRunner server AppID. No SteamCMD install was attempted. |
| [Valve Developer Community Dedicated Servers List](https://developer.valvesoftware.com/wiki/Dedicated_Servers_List) | HTTP 200 redirected to an Anubis “Making sure you're not a bot!” page under `/.within.website/`. | **Access blocked by challenge; the list was not read.** No absence claim can be drawn from this fetch. No challenge bypass attempted. |

## Bounded GitHub discovery

Unauthenticated public repository searches returned HTTP 200 with `incomplete_results: false`:

- [Query `snowrunner dedicated server`, first 10](https://api.github.com/search/repositories?q=snowrunner+dedicated+server&per_page=10): total_count 1, `mrgrosser/snowrunner-dedicate-server`.
- [Query `snowrunner server`, first 10](https://api.github.com/search/repositories?q=snowrunner+server&per_page=10): total_count 3, the above plus `mr-ukko/snowrunner-server-tool` and `EvanTrow/SnowRunner-Server`.

These are repository metadata searches, not global code searches or an exhaustive catalog. No pagination was necessary for these returned counts. No save editors or generic co-op guides were treated as dedicated-server implementations.

### mr-ukko/snowrunner-server-tool — ordinary-client automation candidate

- [Repository](https://github.com/mr-ukko/snowrunner-server-tool), [fetched README](https://raw.githubusercontent.com/mr-ukko/snowrunner-server-tool/main/README.md), [releases query](https://api.github.com/repos/mr-ukko/snowrunner-server-tool/releases?per_page=5): all HTTP 200; releases returned `[]`.
- README describes a Python web panel, automatic contract approval every ten minutes, and map changes. Requires a separate account with SnowRunner; installation lists `pyperclip`, `vgamepad`, `pywinauto`, and `pygetwindow`.
- Usage explicitly starts with “Start the SnowRunner co-op.” Its “headless server” instructions still require the game to start on a virtual display.
- Classification: potentially reusable control-plane/UI automation for the unattended full-client fallback. **Not a standalone authoritative engine.** README claims were not execution-tested; source correctness, license, maintenance, security and compatibility were not audited. Its web-control port is not evidence of the game's network ports. No exposure or deployment is recommended from this preflight alone.

### EvanTrow/SnowRunner-Server — placeholder, no runtime in inspected tree

- [Repository](https://github.com/EvanTrow/SnowRunner-Server), [fetched README](https://raw.githubusercontent.com/EvanTrow/SnowRunner-Server/main/README.md), [recursive main tree](https://api.github.com/repos/EvanTrow/SnowRunner-Server/git/trees/main?recursive=1), [releases query](https://api.github.com/repos/EvanTrow/SnowRunner-Server/releases?per_page=5): all HTTP 200.
- README is only a heading and “Node.js web app for managing a server instance of SnowRunner.” The complete returned main tree (`truncated: false`, SHA `347391953d1148be6343d0c876661807a989058a`) contains only `.gitignore`, `LICENSE`, and `README.md`; releases returned `[]`.
- Classification: no executable implementation or packaged release in the inspected branch/release inventory. Other refs and external artifacts were not searched.

### mrgrosser/snowrunner-dedicate-server — this research, not independent validation

- [Repository](https://github.com/mrgrosser/snowrunner-dedicate-server), [fetched README](https://raw.githubusercontent.com/mrgrosser/snowrunner-dedicate-server/main/README.md), [releases query](https://api.github.com/repos/mrgrosser/snowrunner-dedicate-server/releases?per_page=5): all HTTP 200; releases returned `[]`.
- Public README describes research and a read-only inspector and explicitly says a running dedicated server has yet to be demonstrated. It matches this project's research scope; do not count its search appearance as independent confirmation of feasibility.

GitHub README discovery also used the public `/repos/mr-ukko/snowrunner-server-tool/readme` and `/repos/EvanTrow/SnowRunner-Server/readme` API endpoints; both returned HTTP 200 and the raw URLs above. No HTTP failures or rate-limit errors occurred in these requests. The Valve challenge and publisher extraction quality are the substantive access limitations.

## Concrete next action

Continue the existing **runtime-feasibility gate**: trace callers of the copied build's dedicated predicates and Steam game-server initialization to establish a reachable startup path before preparing a deployment wrapper. Independently run the already-designed isolated host/guest disconnect-and-restart capture when the test environment is available. Neither a database nor the discovered GUI helper resolves these unknowns.

If a three-guest unattended ordinary client becomes the accepted fallback, review `mr-ukko/snowrunner-server-tool` source, license and build compatibility before implementing duplicate UI automation; test only on isolated profiles. For the four-human/non-player target, require an actual obtainable server artifact or reproducible source build plus measured capacity and persistence evidence. Stop this preflight here: useful classification evidence is acquired, but no runtime was validated.
