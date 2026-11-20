# SnowRunner persistent co-op research

The goal is a persistent campaign for up to four human players, with a separate multiplayer fleet and no writes to original single-player saves. This is research and a read-only inspector. A running dedicated server has yet to be demonstrated.

## Current assessment — 2026-11-20

A true non-player dedicated server is **not yet demonstrated**. The copied executable has Steam game-server API delay imports and dedicated-mode predicates, but neither a working launch command nor four-human capacity without a player host has been verified. An unattended ordinary client is a separate fallback with three guest slots; it does not automatically retain departing guests' trucks.

The NAS save copies are stable across independent downloads. The Loadstar movement evidence was reproduced, but the supplied samples do not establish guest-disconnect or restart persistence. No game was launched or original save modified in this investigation.

- [Binary evidence and exact investigation targets](research/SERVER_BINARY_ANALYSIS.md)
- [Reproduced NAS save evidence](research/NAS_SAVE_ANALYSIS.md)
- [Dedicated-server requirements, lab topology, and acceptance gates](research/DEDICATED_SERVER_DESIGN.md)
- [Research log and verification](research/RESEARCH_LOG.md)

The next decisive work requires an isolated runnable host/guest environment, or an analysis-friendly native artifact: the supplied executable's transformed/protected code prevents reliable ordinary caller tracing. The isolated host/guest capture protocol is below. A persistence database or Docker wrapper alone cannot establish either capability.

## Follow-up evidence

- [Native call-path boundary](research/SERVER_CALL_PATHS.md): mapped Steam imports; high-entropy code and implausible decoding prevent validated caller recovery. Hopper exists but its bounded attempt yielded no analysis.
- [Compiled script structure](research/SSL_SEMANTICS.md): all 6,852 module payloads parse with protobuf wire rules; dedicated setter and disconnect-cleanup declarations link to bodies. Instruction semantics and runtime reachability remain unknown.

- [Compiled script module attribution](research/COMPILED_SCRIPT_EVIDENCE.md): validated 2,284 modules per bundle and located dedicated-mode and guest-truck cleanup symbols; bytecode behavior remains unproven.
- [Public existing-solutions preflight](research/EXISTING_SOLUTIONS.md): identified an ordinary-client automation helper, but no verified non-player dedicated runtime in the inspected sources.

## Start here

- Read research/FINDINGS.md for the save format, evidence, and open questions.
- Run `python -m unittest discover -s tests -v` from the repository root.
- Run `python tools/inspect_saves.py /path/to/copied/remote` against a separate copy of the Steam save files. The inspector prints JSON to stdout.

## Next experiment

Use dedicated test profiles on the host and guest. Start with North Port, Alaska, and use a guest-owned truck that is easy to distinguish from the host's fleet. Save and copy both profiles before joining, after the guest parks and while they remain connected, and after the guest leaves and the host saves again. Also capture after the host restarts if testing persistence across restarts. Record the truck model and whether it remains visible and drivable at each step. Compare the decompressed map files and check whether the host or guest saves the truck ID and position. Verify that the active profiles are separate from original campaigns before running the test.

An ordinary unattended client host occupies one slot, leaving three guest slots. Treat support for four humans on a non-player host as a separate research question.

## Controlled co-op capture and comparison

Follow [the host/guest capture protocol](research/COOP_CAPTURE_PROTOCOL.md) before collecting new evidence. It defines isolation checks and four capture stages; no game launch or save modification is automated.

Compare two completed copies of a player's `remote` folder:

```bash
mkdir -p private-evidence
python tools/compare_snapshots.py /private/baseline/remote /private/parked/remote \
  --truck-id KNOWN_INSTANCE_ID > private-evidence/comparison.json
```

Omit `--truck-id` if it is not known; repeat it for up to eight IDs. Reports include hashes, decoded map differences and exact ID byte references. Positional differences are not record alignment; retained references do not establish ownership or visible/drivable persistence. Compare host and guest separately and correlate with observations.

Keep all raw captures and generated reports private. `private-evidence/`, `exports/`, `sample-saves/`, and `game-copy/` are ignored by Git. Decoder errors are reported with a nonzero exit code; do not treat partial reports as complete evidence.
