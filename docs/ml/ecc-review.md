# ECC assessment and applied verification

Reviewed 18 November 2026: [affaan-m/ECC](https://github.com/affaan-m/ECC), revision `3f14a103a8694e51c1df9a806217a6d0b5f7a6f7`. GitHub's unauthenticated commit API returned a rate-limit error; the revision was obtained with `git ls-remote`. The official README, MIT license and relevant guidance were inspected through public source endpoints.

ECC is useful as development guidance here. Its [verification loop](https://github.com/affaan-m/ECC/blob/3f14a103a8694e51c1df9a806217a6d0b5f7a6f7/skills/verification-loop/SKILL.md), [research-first workflow](https://github.com/affaan-m/ECC/blob/3f14a103a8694e51c1df9a806217a6d0b5f7a6f7/skills/search-first/SKILL.md), and [review checklist](https://github.com/affaan-m/ECC/blob/3f14a103a8694e51c1df9a806217a6d0b5f7a6f7/agents/code-reviewer.md) support researching dependencies, verifying actual outcomes, checking trust boundaries and reporting only concrete review findings. We applied that guidance manually within the existing two-worker protocol. No ECC installer, global hooks, agent orchestration, application runtime dependency or third-party task implementation was installed/copied.

## Applied to the scientific M1 handoff

| Verification area | Executed evidence and practical limit |
|---|---|
| Compilation/imports | Scientific source and tests compiled; scientific/API package imports passed. |
| Static types | No static type checker configured. Compilation is not a static type check. |
| Lint | No Python linter configured. The CRLF-aware diff whitespace check passed; that is not a lint result. |
| Tests | 11 scientific tests passed; actual outcomes retained in `results/experiments/m1-diagnostic-v1/checks.json`. No coverage percentage claimed. |
| Data/secret checks | Scanned tracked paths for raw trip files, `.env` and key files, and text for specified private-key/token patterns; no matches. This is a targeted check, not a comprehensive security certification. |
| Diff/review | Reviewed scientific ownership boundaries and B's explicit HTTP serialization; private scoring evidence is excluded and disconnected route pieces remain separate. Sent concrete data-root/timing/diagnostic-label findings to B. |
| Target acceptance | All ten development diagnostic trips ran and first-trip CLI/core signatures matched. HTTP/UI, physical two-laptop and reserved evaluator acceptance remain separate checks; those were not established by this scientific handoff. |

The machine-readable supplemental review lives in the shared mailbox at `handoffs/a/A-M1-ECC-verification.json`. The published source revision changed during the user's metadata cleanup; the verified mapping in `results/experiments/source-revision-map.json` connects original evidence revisions with byte-identical public source trees. Earlier test outcomes are retained as executed, not presented as newly rerun tests under a different SHA.

## How this changes subsequent work

Before adding a model/dependency, inspect the existing code and official library documentation, compare fit with the task and measured budget, and retain a clear decision. Before handing off a milestone, record checks with precise PASS/failure/unconfigured status and keep local correctness separate from deployment acceptance. Use manual review with exact failure scenarios rather than speculative style findings. Record substantive fixes and their executed verification in meaningful commits.

A subsequent concrete parser review finding was fixed in source `8634384`: blank/comment rows now fail explicitly instead of shifting IDs. The latest suite has 14 passing tests and the new immutable `m1-diagnostic-v2/checks.json` records unchanged all-trip counts, fingerprints and prediction signatures. The original 11-test evidence above remains historical.
