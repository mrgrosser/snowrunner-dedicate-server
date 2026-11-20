# Research log

## 2026-11-20 — NAS handoff resumed

### Objective

Determine what is required for a persistent standalone SnowRunner host: up to four human players, a separate multiplayer fleet, and no writes to original single-player campaigns. A full-client unattended host is a fallback, not equivalent to a non-player dedicated server.

### Intake observations

- The supplied NAS share is accessible read-only through SMB client operations. Its root contains `game-copy/`, `sample-saves/`, `research/`, `tests/`, `tools/`, and a handoff ZIP.
- `game-copy/` contains `Media/`, `preload/`, and `Sources/`. `sample-saves/` contains `remote/`, `after move/`, `base/`, and cloud metadata. Folder names alone do not identify controlled co-op stages or prove that every artifact is complete.
- Starting local commit: `8dc7835` on `research/coop-capture-handoff`; observed remote `main`: `fd2ce9a62ab3c513f8fa11e1cd913f7e804e4386`.
- Baseline: all 14 Python unit tests passed with `python3 -m unittest discover -s tests -v`.
- No game was launched and no NAS writes were performed during intake.

### Investigation tracks

1. **Artifact/server mode:** selected game artifacts, reproducible identity, dedicated-mode clues, and limits of static evidence.
2. **Save persistence:** reproduce the supplied movement experiment, classify available captures, and identify what remains missing for guest-independent truck persistence.
3. **Server design:** existing-solutions preflight, practical architecture, and explicit acceptance gates for a true dedicated server versus an unattended client.

### Reviewed results

- [Binary analysis](SERVER_BINARY_ANALYSIS.md): two independent executable downloads match SHA-256 `d46623b23808d19a40f7ebeec15332d11f97317637ec4d4e072a501bc78a77c8`; parent review independently rehashed the retained executable. Real Steam game-server delay imports improve the static evidence, but reachable dedicated startup remains unresolved. No native REA engine was available; these are explicitly ordinary static-tool results, not decompilation or runtime proof.
- [Save analysis](NAS_SAVE_ANALYSIS.md): 62 files per acquisition pass, stable metadata and matching repeated-download hashes. Parent review reran the comparator: 7 changed / 21 unchanged / 0 added / 0 removed. The earlier movement was reproduced; host/guest persistence was not tested by these samples.
- Design and requirements: separate true dedicated operation, an unattended-client fallback, and save persistence so that success in one is not mistaken for success in all three. The completed [design report](DEDICATED_SERVER_DESIGN.md) defines isolated two-client experiments, ownership and restoration constraints, capacity tests, and restart/soak acceptance criteria. Public implementation discovery remains incomplete and is explicitly identified as an outstanding preflight, not evidence that no existing solution exists.
- No game launch, save writer, server deployment, firewall change, or NAS modification was performed. This pass produces an evidence-backed requirements package, not a working dedicated-server release.

### Next decisive evidence

Trace dedicated predicates and Steam server initialization into reachable application code using a suitable native-analysis environment. Separately run the isolated two-client [co-op capture protocol](COOP_CAPTURE_PROTOCOL.md). Those runtime captures must establish guest truck retention and restoration before implementing a persistence writer. Four humans plus a non-player host needs its own capacity test.

Raw saves, binaries, cloud metadata, credential material, and generated private reports are excluded from publication. Published reports describe observations separately from hypotheses and untested designs.
