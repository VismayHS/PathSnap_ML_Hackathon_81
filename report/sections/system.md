## Geographical Visualisation using Folium

The Folium maps are made by `src/visualisation/folium/make_maps.py` from development-only visualisation exports (train or student-test trips only). Each map has five layers, each switchable in a layer control and named in a legend:

| Layer | Encoding |
|---|---|
| Raw GPS observations | small hollow orange circles; the tooltip gives the observation index and time |
| Road network near the trajectory | thin grey lines |
| Reference route (development data only) | wide translucent green line |
| Predicted route, classifier + HMM | solid blue line |
| Predicted route, classifier only | dashed purple line |

Each connected piece of a predicted route is drawn as its own line. Where the decoder breaks the route (no legal connection on the directed road graph), the map shows a gap instead of a straight line across buildings. The map fits its bounds to the trip's GPS extent. The basemap is OpenStreetMap, credited on the map.

PENDING: representative map screenshot(s) for a student-test trip, with the classifier-only and HMM layers (needs A's development visualisation export of the final model).

Interactive HTML maps: `maps/<run_id>/trip_<id>_<partition>.html`. Regenerate them with `python -m src.visualisation.folium.make_maps --input results/hmm/visualisation/<run_id> --output maps/<run_id>`.

Evaluator trips are never mapped. The generator rejects any partition other than train or student-test, and the evaluator UI never receives reference geometry.

## API, UI and Deployment

### Architecture

```
Laptop 2: React UI                      Laptop 1: FastAPI
  GET /trips ───────────────────────►   allowlisted trip IDs
  POST /predict {trip_id} ──────────►   load .track/.nodes/.arcs (never .route)
                                        clean > candidates > features > model
                                        > HMM/Viterbi > route geometry
                                        then, separately: scorer reads reference
  ◄─────────────────────────────────    route, statuses, timings, aggregate metrics
```

**Backend (`api/`).** The backend has three endpoints:

- `GET /health` gives readiness, the mode and the model identity.
- `GET /trips` lists the allowed trip IDs for the configured mode.
- `POST /predict` takes `{"trip_id": "…"}`.

How it works:

- The mode (`development` = student-test trips, `evaluator` = reserved trips) is server configuration and never a request field. Evaluator mode never falls back to student-test data.
- Requests are checked against the partition's allowlist.
- At startup the service checks the model bundle's manifest: its schema, contract version and the SHA-256 of every file. Any failure leaves the service running but "not ready", with a reason.
- Prediction runs in a worker thread, one at a time, so `/health` stays responsive. A second request while one is running gets HTTP 429.
- Scoring runs only after the prediction finishes, through a separate scorer. A scoring failure yields "metrics unavailable", never a failed prediction.
- Responses are mapped field by field, so no reference arcs, per-point labels or correctness masks can reach the browser. The JSON schema rejects unknown fields.
- Every response carries an `X-Request-ID`, and Laptop 1 logs that ID with the trip, model version and per-stage timings.

**Frontend (`ui/`).** The frontend is built with React, TypeScript, Vite and Leaflet:

- One left panel holds the connection state, the mode badge, the ten trips, the "Reconstruct route" action and the results. The rest of the screen is the map, with a layer control, an observation inspector and route playback.
- Coordinates arrive as `[lon, lat]` and are converted once for Leaflet.
- Each route piece is drawn separately.
- An earlier request's late response can never overwrite a newer selection.
- All states are designed: connecting, unreachable, not ready, evaluator data not configured, running, failed (with the request ID) and diagnostic model.
- The design research and decisions are in `docs/ui-research.md` and `DESIGN.md`.

PENDING: UI screenshots from the final trained model (selection, result, inspector).

### Verification

| Check | Result | Evidence |
|---|---|---|
| API contract, errors, leakage, readiness (pytest) | PENDING: final count at M4 | `tests/api` |
| Browser workflows (Playwright: keyboard, small screens, errors, stale responses, LAN origin) | PENDING: final count at M4 | `ui/tests/workflow.spec.ts` |
| All ten development trips through HTTP | PENDING: final run | integration manifest |
| End-to-end latency per trip | PENDING: profiled with the final model | `results/system/` |

### Two-laptop deployment

The step-by-step guide is `docs/deployment/two-laptops.md`. In short:

- **Laptop 1** runs `uvicorn api.main:app --host 0.0.0.0 --port 8000` with `PATHSNAP_DATA_ROOT`, `PATHSNAP_BUNDLE_ROOT`, `PATHSNAP_MODE` and `PATHSNAP_CORS_ORIGINS` set.
- **Laptop 2** builds the UI with `VITE_PATHSNAP_API_URL=http://<Laptop-1-IP>:8000` and serves it with `npm run preview`.

PENDING: screenshot of a successful API response in Laptop 1's terminal while Laptop 2 makes requests (Deliverables §7). This must be a real capture from the two-laptop setup.
