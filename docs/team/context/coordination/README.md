# Shared file mailbox

This directory is the actual shared mailbox for the two PathSnap coding sessions. It is outside the project repository and worktrees, so messages are visible immediately without merging branches.

Read `../PATHSNAP_TWO_LLM_PROTOCOL.md` for the message schema, ownership, atomic-write rules, bootstrap handshake, handoffs, and integration gates. Each sender owns its own message/status/handoff files. Do not both edit one shared log.

Initial state is **not started**. No peer acknowledgement, branch setup, training, application implementation, or integration has occurred merely because this mailbox exists. B performs bootstrap; A can do independent read-only investigation while waiting. Both coding sessions must be running/resumed to read and reply; these files do not automatically invoke either model.

Create sender-owned subdirectories as needed, without altering a peer's contents. Do not store raw datasets, protected evaluator references, credentials, or large mutable model binaries here.
