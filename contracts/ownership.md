# File ownership — one writer per tracked file

Status: proposed with contract 0.1.0; becomes the record once A ACKs. Source: `PATHSNAP_TWO_LLM_PROTOCOL.md` (workspace root). The more specific path wins inside mixed directories.

## A — scientific system

- `src/data_processing/**`, `src/features/**`, `src/models/**`, `src/evaluation/**`, `src/hpo/**`, `src/hmm/**`
- `src/pipeline.py`, `src/__init__.py`
- `src/visualisation/plots/**`, `notebooks/**`, `configs/ml/**`, `configs/hmm/**`
- `artifacts/**`, `data/README.md`, ignored `data/processed/**`
- `results/eda/**`, `results/experiments/**`, `results/hpo/**`, `results/hmm/**`, `results/figures/**`
- `requirements.txt`, Python lock/packaging (`pyproject.toml` etc.), root Python test configuration (e.g. `pytest.ini`)
- `tests/ml/**` (incl. `tests/ml/conftest.py`), `report/sections/science.md`, `docs/ml/**`, `docs/repository-references-ml.md`
- `docs/team/science-notes.md` (added at bootstrap, see below)

## B — application, delivery, integration

- `api/**`, `ui/**` (incl. `ui/package.json`, lockfile, browser tests), `src/contracts.py`, `contracts/**`, `configs/api/**`
- `src/visualisation/folium/**`, `maps/**`, `tests/api/**`, `tests/integration/**`
- Root `README.md`, `.gitignore`, `.env.example`, `DESIGN.md`
- `docs/ui-research.md`, `docs/deployment/**`, `docs/repository-references.md`, `docs/repository-references-app.md`
- `docs/requirements-traceability.md`, `docs/validation/**`, `scripts/**`
- `report/**` except `report/sections/science.md`; `results/system/**`; root CI/deployment config if justified
- Pre-existing shared READMEs: `src/visualisation/README.md`, `configs/README.md`, `results/README.md`
- `tests/conftest.py` (root, if needed)
- `docs/team/**` except `docs/team/science-notes.md` (added at bootstrap, see below)

## Bootstrap additions (proposed by B, need A's ACK)

| Path | Owner | Why |
|---|---|---|
| `docs/team/README.md`, `docs/team/progress-log.md`, `docs/team/glossary.md` | B | User request (2026-11-18): plain-language docs so the human team can follow what is happening. |
| `docs/team/science-notes.md` | A | A's plain-language running notes on data/model/HMM decisions for the team. |
| `contracts/fixtures/**`, `contracts/current-manifest.json`, `scripts/contract_hash.py` | B | Contract fixture + reproducible hash per protocol. |

The bootstrap commit contains pre-existing scaffold files authored before the split; committing them does not transfer authorship or later ownership.

## Shared rules

- Python dependencies needed by B are requested from A by message; A edits `requirements.txt`.
- New unlisted paths: ask the owner or add a row here with the peer's ACK first.
- No root formatter that rewrites the other worker's files.
