# Tested Python environment

Python 3.12.3, Linux x86_64, isolated A-local `.venv`. Direct versions are pinned in `requirements.txt`; the executed environment's complete resolved package versions are in `requirements.lock.txt`. B creates its own environment; no worktree shares a mutable virtualenv.

Executed checks on 18 November 2026:

- `.venv/bin/python -m pip check`: no broken requirements.
- Imported numpy, scipy, pandas, scikit-learn, Optuna, matplotlib, pyproj, uvicorn, pydantic, httpx, jsonschema and Folium successfully.
- FastAPI `TestClient` made a real in-process GET to a small health route and received the expected JSON.
- Folium generated map HTML successfully.
- Initial scientific source suite: 11 tests passed in 0.98 seconds. This run preceded publication of the source commit; the immutable milestone evidence will rerun it against committed source.

These compatibility checks are not a PathSnap API integration test, model experiment, or LAN demonstration. Tested direct versions were selected for compatibility, not claimed to be the latest releases.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock.txt
.venv/bin/python -m pip check
```
