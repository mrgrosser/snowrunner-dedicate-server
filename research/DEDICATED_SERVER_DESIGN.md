# Standalone SnowRunner host: design and acceptance gates

Date: 2026-11-20. Status: requirements and experiment design only; no deployed server, validated launch mode, save writer, or runtime ownership hook.

## Decision

Keep three deliverables separate. Investigate the runtime and guest ownership before building a persistence service. The current repository is a useful read-only evidence tool, not a server implementation.

| Deliverable | Meaning | Current decision |
| --- | --- | --- |
| True dedicated host | A separate authoritative simulation process with no player occupying a slot; four humans can join and play simultaneously | Research blocked on reachable server startup and capacity proof |
| Unattended full-client host | An ordinary graphical player client kept hosting, with three guest slots under the existing four-player model | Possible fallback to test, not equivalent to the four-human target; no unattended deployment demonstrated |
| Persistence sidecar | Captures, validates, catalogs and restores supported state around an existing simulation runtime | Read-only capture/inspection is available; restoration and runtime retention are unproven |

A server entrypoint alone would not prove persistent guest trucks. A database alone cannot simulate the game or stop its disconnect cleanup. Four humans including a human host is also not four humans plus an unattended host.

## Evidence and existing-solutions preflight boundary

Reviewed the repository README and research reports below. The supplied Sources filename inventory found no separately named dedicated executable/DLL or launch script within its stated boundary. Actual Steam game-server delay imports and dedicated predicates exist in the copied retail executable, but their callers and reachable launch behavior are unresolved. These findings do not establish a separately distributable server or valid switches.

The copied saves reproduce vehicle movement; they do not contain an observed co-op/disconnect/restart sequence. Zero co-op counters supply no positive co-op evidence and are not proof that co-op never happened.

Existing local solutions should be reused: `tools/inspect_saves.py`, `tools/compare_snapshots.py`, and the controlled capture protocol already cover read-only inspection and evidence comparison. Do not replace them with a custom database or deployment wrapper before runtime feasibility is established. A generic process supervisor or backup tool could later handle lifecycle and immutable snapshots, but neither solves game simulation, ownership, or capacity.

**Public preflight is incomplete.** No primary public documentation or open-source server implementation was fetched or validated in this bounded design pass; the coordinator requested wrap-up without broadening external research. There were no attempted public fetches and therefore no HTTP/access failures to report. Do not interpret this as a search proving that no solution exists. Before commissioning a custom runtime, check publisher support/distribution documentation and any candidate open-source implementation for an actual runnable release, supported game build, licensing, four-human/non-player capacity evidence, persistence behavior, and maintenance. No third-party candidate is recommended on the present evidence.

Local evidence sources:

- [Project scope and current tooling](../README.md).
- [Verified findings and design constraints](FINDINGS.md).
- [Binary evidence, exact build identity, and bounded inventory](SERVER_BINARY_ANALYSIS.md).
- [Repeated NAS acquisition and movement analysis](NAS_SAVE_ANALYSIS.md).
- [Host/guest isolation and four-stage capture protocol](COOP_CAPTURE_PROTOCOL.md).

## Required behavior

1. **Authoritative campaign:** one isolated multiplayer campaign and full fleet state; no implicit synchronization back into solo campaigns. Define who may operate, recover, store, or sell shared vehicles before implementing transfer.
2. **Guest-independent fleet:** vehicles accepted into the shared fleet remain visible and usable after the contributing guest leaves, after all guests leave, and after host restart. Ordinary private guest vehicles need an explicit policy; do not silently convert every borrowed vehicle into shared property.
3. **Complete state:** preserve identity, map and authoritative position/orientation, configuration, fuel, damage, attachments and verified cargo/trailer relationships. Preserve relevant campaign and shared profile files together. Unsupported relationships must block a restore rather than be silently dropped.
4. **Isolation:** protect original saves on every client, not only the host. Keep account identifiers and raw captures private. DLC/mod availability and build compatibility must be verified using legitimately available content; copied descriptors are not entitlement proof.
5. **Lifecycle:** expose actual runtime readiness, authenticated hosting, save health and guest connectivity separately. A live PID, open socket, or accepted supervisor start is insufficient evidence of a joinable server.
6. **Capacity:** the primary target requires four active human clients plus a non-player host. Report the unattended full-client fallback as three guests unless a separate measured result establishes otherwise.

No CPU/RAM/GPU sizing, ports, firewall rule, headless flag, or command-line syntax is specified here: none has been validated. Measure the selected runtime and its actual networking before defining those requirements.

## Minimal lab topology

Start with two isolated game environments: host H and guest G1, each with its own legitimate platform session, test profile and writable save tree. Use the already documented North Port scenario with a distinctive guest truck. Capture to a third logical location E outside live save and Cloud paths; E may be protected storage on an existing lab machine, not another game client. Give the capture process read-only access to live state and write access only to evidence storage.

Do not infer that a VM, container, Linux compatibility layer, remote desktop disconnect, or GPU-less boot works. Start with the verified client dependency environment identified by the runtime investigation; isolation may use separate machines or independently verified environments.

Only after two-client persistence succeeds, expand to four human client environments G1–G4 plus the candidate non-player H. For the fallback test, H is the ordinary player host and only G1–G3 are guests. Record build, DLC/mod set, platform, authentication, network arrangement and observed resource use. Determine networking through runtime observation and vendor guidance, not guessed port lists. No new public exposure is required for the initial controlled experiment.

## Guest disconnect: the ownership problem

Track the same unique guest vehicle across four independent observations: connected/parked, guest departed/host saved, host restarted/guest absent, and later guest rejoined. Capture both profiles as prescribed by the existing protocol.

- If the host does not serialize enough state, a snapshot-only sidecar cannot reconstruct a verified complete vehicle.
- If bytes remain but the vehicle disappears or cannot be controlled, disk retention has not solved runtime authority.
- If the host serializes the vehicle but disconnect deletes it, retention may require a verified ownership-transfer mechanism before cleanup or another supported runtime change. No such hook is currently established.
- If a restored host vehicle and the guest's inventory both retain authority, reconnect/recovery/garage operations may duplicate or destroy it. Stable identity, transfer policy and reconciliation are prerequisites, not cleanup work after deployment.

Test ordinary departure separately from connection loss, client crash and host crash. Later vary cargo, trailer attachment, recovery, garage storage, map travel and guest reconnect one variable at a time. A successful empty-truck experiment must not be generalized to unsupported attachments or maps.

## Phased gates

| Gate | Work | Evidence required to advance |
| --- | --- | --- |
| 0: isolation | Follow the protocol for H and every guest; hash originals, disable game Cloud, verify test paths and access restrictions | Test save modifies only isolated state; protected original hashes unchanged; no alias/junction route to originals |
| 1A: runtime feasibility | Trace dedicated predicate callers and actual Steam server-init callers, then test only a justified launch path in the isolated lab | Reproducible startup recipe for the exact build, authentication, host creation, simulation without an active player, and normal shutdown; otherwise retain fallback classification |
| 1B: persistence feasibility | Run the existing paired host/guest capture protocol independently of 1A | Identity-correlated saves plus observed visibility/control after logout and restart with guest absent; repeat on a second distinctive truck |
| 2: restoration design | Establish complete record framing, schema/build constraints, ownership and cross-file links; only then prototype on disposable copies | Unmodified round-trip restores correctly, deliberate state change restores correctly, invalid/incomplete inputs rejected, no duplicate identity on reconnect |
| 3: lifecycle sidecar | Add versioned snapshot manifests, stopped-runtime restore, compatibility checks and recovery workflow around a proven runtime | Consistent recovery set, single-writer enforcement, interrupted-operation recovery and successful rollback; sidecar restart does not mutate state |
| 4: capacity and soak | Exercise the exact selected topology and fleet operations | Four humans plus non-player host for primary target, or explicit three-guest fallback; persistence and resource criteria below pass |

1A and 1B are independent investigations; neither must wait for a database or service wrapper. Failure at a gate produces a documented limitation, not a claim of approximate success.

## Cloud/save isolation and restore contract

Use full per-client save-tree backups outside live save and Cloud directories. A different campaign slot alone is insufficient because common/profile files are shared. Keep Cloud disabled for the entire lab run, verify path canonicalization and filesystem permissions, and recheck originals after every destructive fault experiment. Do not automatically re-enable Cloud afterward; reconciliation is a separate transition.

Until consistency can be proven, authoritative restore points are complete copies taken after a normal stopped-game save. Connected captures are diagnostic evidence and may be cross-file inconsistent even when two hash passes match. Never promote them automatically into production recovery points.

A future sidecar must restore only with the game stopped and a verified exclusive writer. Stage the entire validated recovery set, preserve the previous known-good set, and record which generation is authoritative. Design explicit interruption recovery for cross-file replacement; do not assume a sequence of individual atomic file renames is an atomic campaign transaction. Check hashes, supported decoding, exact schema/build compatibility, and external references before use. Fail closed on unknown formats. Avoid mixing timestamps from unrelated profile/map generations.

## Acceptance criteria

These are proposed lab gates, not achieved results or publisher specifications.

- **Normal restart:** pass three consecutive normal host shutdown/restart cycles with guests absent. On each, verify the retained truck in-game and drive it; compare fleet identities/counts, fuel/damage, configuration, map position and campaign progress to the corresponding known-good save, allowing only documented simulation changes.
- **Reconnect integrity:** guest rejoins without duplicated/lost shared trucks or unintended changes to their private fleet. Exercise recovery, garage and map travel as separate tests before claiming those operations supported.
- **Crash recovery:** inject interruption only in disposable test state, including during snapshot/restore staging. Recover the last acknowledged complete generation or explicitly declare recovery failure. Never silently combine partial generations. Record measured data loss and recovery time; set service RPO/RTO only after observations and user requirements are reconciled.
- **Isolation:** original solo save hashes remain unchanged on H and all guests; no Cloud upload or test-to-solo propagation occurs. A failed isolation check blocks further runtime testing.
- **Capacity:** all four humans simultaneously join, drive and interact in a session hosted by a demonstrably non-player H; repeat after H restart. Confirm lobby occupancy and actual simulation behavior, not just advertised lobby metadata. An idle player avatar is not a non-player host.
- **Continuity:** all guests can leave and later rejoin the same campaign with shared fleet intact. Distinguish persistence across process restart from an always-running simulation while empty; verify both if continuous simulation is required.
- **Soak:** proposed initial test is a two-hour active four-human session plus an overnight empty-host interval and subsequent reconnect. Log disconnects, hangs, save failures, resource trends and hosting readiness. This is an initial acceptance exercise, not a reliability guarantee; repeat after game/runtime changes.
- **Resource sizing:** measure peak and steady CPU, memory, GPU requirement, storage growth and network usage under the accepted workload; provision documented headroom afterward. No hardware guarantee can be derived from the current static artifacts.

## Next decision

The smallest decisive action is the isolated two-client capture run, alongside bounded tracing of dedicated-mode/runtime initialization. If neither a supported server distribution nor a reachable dedicated runtime can be demonstrated, explicitly choose whether three guests on an unattended client meets the need; do not label that fallback a completed four-human standalone server. If disconnect ownership cannot be transferred or faithfully restored, stop at read-only archival/inspection rather than presenting snapshots as a persistent shared fleet.
