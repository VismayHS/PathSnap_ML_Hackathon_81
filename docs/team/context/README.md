# Working context (snapshot)

This folder holds a copy of the instructions and coordination records that drove this build, so the whole team can see them:

- `prompts/`: the build specification (`PATHSNAP_BUILD_PROMPT.md`), the two-worker protocol, and the A and B role prompts. These were used to direct the AI coding assistance that is disclosed in [../README.md](../README.md).
- `coordination/`: the A/B mailbox, with messages (`messages/from-a`, `messages/from-b`), status files, handoff manifests and integration records.

This is a copy, refreshed with `scripts/snapshot_context.sh`. The live mailbox sits outside the repository. `SNAPSHOT.txt` gives the time of the copy. The student-material PDFs are not copied, because they belong to the organisers.
