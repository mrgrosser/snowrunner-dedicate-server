# Guest-truck persistence capture protocol

## Question and boundary

Does the host write a connected guest's parked truck into its own save files, and does that state remain after guest logout and host restart?

This experiment collects evidence only. It does not patch the game, write reconstructed saves, or establish a dedicated-server mode. An unattended stock client host still occupies one of the four player slots; four humans with a non-player host remains unverified.

Use North Port, Alaska (`level_us_02_01`) and one distinctive guest-owned truck. Avoid cargo, trailers, towing, garage transfers, recovery, purchases, and other intentional state changes during this run. Test those separately later.

## Isolation gate — both players, before the experiment

Do not proceed until every item below is recorded for **both** host and guest:

- Exit SnowRunner. Identify the Steam account, Windows user, active save directory, and intended test campaign on that machine. Keep account identifiers in private evidence, not public notes.
- Make a complete, dated backup of the original save directory outside all live game/save and Steam Cloud paths. Hash the backup and preserve it unchanged. A copied folder or extra campaign slot alone does not prove isolation.
- Disable SnowRunner Steam Cloud synchronization on each participating Steam client before creating or loading test state. Record that it is disabled; keep it disabled for the whole run. Do not resolve Cloud conflicts by uploading test data over original campaign data.
- Use a dedicated test Windows/account environment with its own writable save directory and no write access to the original campaign files. If existing accounts are reused, first establish an equivalent verified separation. Do not assume a campaign selection isolates shared profile files or cloud state.
- Verify the exact test save path is not a symlink, junction, mapped alias, or other route back to the original saves. Do not point inspection or capture output at an original live directory.
- After originals are protected and Cloud is disabled, perform one test-only save, quit normally, and verify that only the test tree changed. Recheck the protected originals against their hashes. If isolation cannot be demonstrated, stop before the co-op experiment.
- Keep automatic save-import or synchronization tools out of this test. Use a truck already legitimately available to the guest test profile; optional solo-fleet importing is a separate experiment.

Do not re-enable Cloud or move test files into a normal profile as part of cleanup. Review that transition separately after the test evidence is secured.

## Private evidence layout

Use a new run directory outside the public repository, for example:

```text
coop-run-YYYYMMDD-HHMMSSZ/
  manifest.json
  S00_BASELINE/
    host/remote/
    guest/remote/
    observations.md
    checksums.txt
  S10_CONNECTED_PARKED/
    host/remote/
    guest/remote/
    observations.md
    checksums.txt
  S20_GUEST_LEFT_HOST_SAVED/
    host/remote/
    guest/remote/
    observations.md
    checksums.txt
  S30_HOST_RESTARTED_GUEST_ABSENT/
    host/remote/
    guest/remote/
    observations.md
    checksums.txt
```

`remote` means a complete copied save folder, not a newly selected subset of files. Preserve source filenames, prefixes, and directory structure. If a player's folder has not changed, capture it anyway and note that it is unchanged. Never overwrite an earlier stage.

In the private manifest record the run ID, UTC timestamps, game version/build and platform for each player, DLC/mod configuration, host/guest roles, isolated test paths, campaign/slot identification, Cloud-disabled checks, and the guest truck's model and distinguishing configuration. Record its instance ID only when identified from evidence; do not invent it from the model name. Capture screenshots of the truck and its parking position against a fixed landmark.

## Consistent capture method

For each stage, coordinate both players before copying:

1. Stop moving and changing truck state. Wait for each game's save indicator to finish and record the actual observed save event. There is no assumed console command or guaranteed timer in this protocol.
2. Copy the complete save tree to that stage's private directory. Record capture start/end UTC and whether the game was still running and connected.
3. Hash the copied files (SHA-256) and verify the copies decode where supported. Do not alter a snapshot to make it parse.
4. While the players remain idle, compare source file sizes/hashes immediately before and after copying. If any change, retain the attempt as an explicitly unstable capture, then take a fresh numbered attempt after another completed save. Two matching passes improve confidence but do not prove an atomic cross-file snapshot.
5. If a stable connected capture cannot be obtained, report that limitation. Do not disconnect or quit to manufacture `S10`: that would change the condition being measured.

For stopped-game stages, confirm normal shutdown completed before copying. Never use force termination to represent a normal logout/save. If a network disconnect or crash occurs, record it and treat that as a separate experimental condition.

## Stage sequence

### S00_BASELINE

With both games stopped after test-only saves, copy both save trees. Record the guest truck's initial location/status and the host's own fleet. The guest has not joined the host in this run yet.

### S10_CONNECTED_PARKED

1. Host loads the isolated North Port test campaign and starts ordinary co-op through the game UI. Guest joins using their isolated test profile.
2. Guest deploys the selected truck and parks at the recorded landmark. Guest remains connected throughout this capture.
3. Record whether the host can see the truck. Record whether the host can select/enter/control it **without moving it**, if that can be checked without changing the experimental state. Separate “selectable/enterable” from an actual driving test. If driving is necessary, perform it as a separate follow-up run and do not label an untested truck “drivable.”
4. Wait for completed saves as observed on both machines, then copy both save trees using the connected capture method. Record the parked position and guest connection state at copy time.

### S20_GUEST_LEFT_HOST_SAVED

1. Guest leaves through the normal game UI without first recovering, selling, storing, or moving the truck. Record the exact departure action and time.
2. Host remains in the same session. Immediately record whether the guest truck remains visible, disappears, changes ownership indicators, or becomes inaccessible. Do not move or recover it.
3. Observe a subsequent completed host save. Capture both players' save trees. Record guest-side save/shutdown status rather than assuming departure saved their state.
4. If no completed host save can be observed while remaining in-session, record that gap. Do not substitute a restart-stage capture under this label.

### S30_HOST_RESTARTED_GUEST_ABSENT

1. After securing S20, host exits normally and relaunches the same isolated campaign. Guest does **not** reconnect.
2. Return to the same map/location and record whether the truck is visible, selectable/enterable, and actually drive-tested or untested. Do not infer disappearance from a closed garage screen or from being on another map.
3. After an observed completed save, capture both save trees. Record that guest stayed absent and whether the guest's unchanged folder hashes match S20.
4. Any guest rejoin test comes afterward as a separately named stage or new run; a truck reappearing on rejoin does not demonstrate guest-independent persistence.

## Per-stage observations template

```text
Run / stage / capture attempt:
UTC save event(s), copy start, copy end:
Host and guest game/connection state:
Map and landmark:
Truck model / identifying configuration / known instance ID:
Visible to host: yes / no / uncertain
Selectable or enterable by host: yes / no / not tested
Actually drivable by host: yes / no / not tested
Position changed intentionally: no / explain
Guest departure/restart actions, if applicable:
Save-file changes during capture: none observed / unstable / unknown
Original-save and Cloud-isolation checks:
Screenshot/evidence filenames:
Unexpected events / limitations:
```

## Read-only analysis and interpretation

Run the existing inspector against each **copied** `remote` directory:

```bash
python tools/inspect_saves.py /private/path/to/run/S10_CONNECTED_PARKED/host/remote
```

If saving JSON output, write it alongside private evidence, never to a tracked repository file. Compare both raw hashes and decoded map content across stages, concentrating on `level_us_02_01` but retaining all changed files. Match candidate truck identifiers/configuration in host and guest copies; a repeated text occurrence is not proof of a complete truck record, ownership, or an authoritative restore transform. Offset `62,956` belongs only to the earlier movement captures and must not be reused as a universal position field.

Distinguish these outcomes:

- A candidate guest-truck record in S10 host data supports disk serialization during connection, but needs identity/record validation.
- A record surviving S20/S30 supports byte-level retention only. In-game visibility and control observations are independently required to demonstrate usable persistence.
- A missing searched ID does not prove the truck was never serialized; encoding, a different identifier, another file, or capture timing may account for it.
- Disappearance on logout despite a valid S10 record makes snapshot-based reconstruction a possible research direction, not a proven safe writer or runtime solution.
- No host record in available captures means snapshot-only persistence is not yet supported by the evidence; investigate serialization/runtime ownership before building a persistence database.

Publish only redacted conclusions and tool changes. Keep game binaries, raw saves, account IDs, screenshots with personal details, and inventory exports private. Repeat the successful capture with another distinctive truck before generalizing any record layout or persistence behavior.
