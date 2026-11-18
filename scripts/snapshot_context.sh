#!/usr/bin/env bash
# Copy the project's build prompts and the A/B coordination mailbox into docs/team/context/
# so the team can read the full working context in Git. Run from the repo root (any worktree).
# Usage: scripts/snapshot_context.sh [WORKSPACE]   (default: two levels above a worktree, or ..)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WS="${1:-}"
if [ -z "$WS" ]; then
  for c in "$ROOT/.." "$ROOT/../.."; do [ -f "$c/PATHSNAP_BUILD_PROMPT.md" ] && WS="$(cd "$c" && pwd)" && break; done
fi
[ -n "$WS" ] && [ -f "$WS/PATHSNAP_BUILD_PROMPT.md" ] || { echo "workspace with PATHSNAP_*.md not found" >&2; exit 1; }
OUT="$ROOT/docs/team/context"
mkdir -p "$OUT/prompts" "$OUT/coordination"
cp "$WS"/PATHSNAP_*.md "$OUT/prompts/"
# Mailbox: messages, statuses, handoffs, integration records (skip in-flight .tmp files)
(cd "$WS/.pathsnap_coordination" && find . -type f ! -name '*.tmp' -print0 | while IFS= read -r -d '' f; do
  mkdir -p "$OUT/coordination/$(dirname "$f")"; cp "$f" "$OUT/coordination/$f"; done)
date -u +"Snapshot taken %Y-%m-%dT%H:%M:%SZ" > "$OUT/SNAPSHOT.txt"
echo "updated $OUT"
