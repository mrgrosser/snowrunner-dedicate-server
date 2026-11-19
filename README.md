# SnowRunner persistent co-op research

The goal is a persistent campaign for up to four human players, with a separate multiplayer fleet and no writes to original single-player saves. This is research and a read-only inspector. A running dedicated server has yet to be demonstrated.

## Start here

- Read research/FINDINGS.md for the save format, evidence, and open questions.
- Run `python -m unittest discover -s tests -v` from the repository root.
- Run `python tools/inspect_saves.py /path/to/copied/remote` against a separate copy of the Steam save files. The inspector prints JSON to stdout.

## Next experiment

Use dedicated test profiles on the host and guest. Start with North Port, Alaska, and use a guest-owned truck that is easy to distinguish from the host's fleet. Save and copy both profiles before joining, after the guest parks and while they remain connected, and after the guest leaves and the host saves again. Also capture after the host restarts if testing persistence across restarts. Record the truck model and whether it remains visible and drivable at each step. Compare the decompressed map files and check whether the host or guest saves the truck ID and position. Verify that the active profiles are separate from original campaigns before running the test.

An ordinary unattended client host occupies one slot, leaving three guest slots. Treat support for four humans on a non-player host as a separate research question.
