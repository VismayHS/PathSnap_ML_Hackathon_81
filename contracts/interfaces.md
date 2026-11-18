# PathSnap boundary interfaces — contract 0.1.0 (PROPOSED)

Status: **proposal by B, awaiting A's scientific review and ACK.** Nothing here claims an implementation exists. Canonical types: [`src/contracts.py`](../src/contracts.py). Wire schema: [`http.schema.json`](http.schema.json). Artifact/results/dev-visualisation schema: [`artifacts.schema.json`](artifacts.schema.json). Synthetic example: [`fixtures/predict_response.synthetic.v0.1.0.json`](fixtures/predict_response.synthetic.v0.1.0.json).

## 1. Conventions

| Item | Rule |
|---|---|
| Coordinates | WGS84 `[lon, lat]` on every boundary and in GeoJSON. The React/Leaflet adapter converts once to `[lat, lon]`. Folium code converts once at its own boundary. |
| Bounds | `[west, south, east, north]` (= GeoJSON bbox order). |
| Units | time **s** (raw `.track` timestamps), distance **m**, timings **ms**. |
| IDs | Trip IDs are strings (leading zeros kept). Arc/node IDs are **graph-local** ints = 0-based row index of that trip's `.arcs`/`.nodes`. Never compared across trips. |
| Order | `observations[i].index == i == raw .track row`. Every raw row appears exactly once, including invalid ones. |
| Missing numbers | `null`; NaN/Infinity are forbidden on the wire. |
| Route gaps | Each connected route stretch is its own piece/feature. No straight-line bridges between pieces. |
| Leakage | Prediction inputs never include `.route`. Responses/fixtures/HTML/UI state never include reference arcs, per-observation labels or correctness masks. Only aggregate metrics leave the scorer. |

## 2. Python facade (A implements; B calls)

```python
# src/pipeline.py  (A)
load_model_bundle(settings: PipelineSettings) -> ModelBundle          # once at startup; raises ModelNotReadyError
list_trip_ids(mode: Mode, settings: PipelineSettings) -> list[str]     # sorted; raises DataNotConfiguredError
load_prediction_input(trip_id: str, mode: Mode, settings) -> TripInput # .track/.nodes/.arcs only; raises UnknownTripError / TripDataUnavailableError
predict_trip(trip_input: TripInput, bundle, options: PredictOptions) -> PredictionResult   # pure, no reference, no network, no retraining

# src/evaluation/service.py  (A)
evaluate_completed_prediction(prediction: PredictionResult, scoring_settings: ScoringSettings) -> EvaluationSummary
```

- `mode -> partition`: `development -> <data_root>/student_test`, `evaluator -> <evaluator_root>`. If `evaluator_root` is `None` or missing, evaluator mode raises `DataNotConfiguredError`; it never falls back to student_test.
- `train` partition is reachable only through A's own CLI/experiment code, not through `Mode`.
- `predict_trip` must be deterministic for identical inputs/bundle. The CLI and API call this same function.
- **Diagnostic bundles (M1 only).** There is no diagnostic flag in settings. A diagnostic adapter ships as its own bundle whose `manifest.json` has `model_kind: "diagnostic"`. The API accepts it only in `development` mode, shows it as "diagnostic" in `/health` and the UI, and adds a `diagnostic_model` warning. In `evaluator` mode a diagnostic bundle is `ModelNotReadyError`. Missing final assets never fall back to a diagnostic bundle.
- **No valid observations.** A trip with zero valid observations raises `TripDataUnavailableError` (503); no sentinel/non-finite bounds are produced.
- `list_trip_ids` is owned/implemented by A (single place for partition resolution); B only calls it.
- `ModelBundle.info` exposes `model_version, model_kind, model_family, decoder, run_id, manifest_sha256` (see `BundleInfo`). Everything else is A-private.
- The scorer is the **only** code path that reads `.route`. It returns `status="unavailable"` with a reason (never zeros) when the reference is missing or the policy cannot score. Scoring failure never turns a successful prediction into an HTTP error.
- B's API runs `predict_trip` in a worker thread (bounded to 1 concurrent prediction by default; extra requests get `429 busy`), then calls the scorer, then serialises.

### `PredictionResult` semantics (A to confirm)

| Field | Meaning |
|---|---|
| `observations[].status` | `matched` (arc assigned) · `no_candidate` (valid point, no candidate under the candidate policy) · `invalid` (dropped by cleaning; `reason` = code) · `unmatched` (had candidates but decoder assigned no state, e.g. unreachable/break) |
| `segment_id` | decoding segment; increments when the decoder restarts after a gap/unreachable break |
| `score`, `score_kind` | score of the chosen candidate. `calibrated_probability` only if calibration was actually fitted/validated; otherwise `normalized_score`. |
| `route[]` | `RoutePiece` per connected stretch: ordered `arcs` with role `observed` / `connector`, `coordinates` from real arc geometry (node-to-node, optionally trimmed at projected endpoints). |
| `network_context` | arcs near the trajectory for display only; `network_context_policy` describes the selection; capped at `PredictOptions.max_network_segments` with `network_context_truncated`. |
| `timings_ms` keys | `load_input, clean, candidates, features, model, decode, geometry, predict_total` (missing stages omitted, not zero). |
| `scorer_evidence` | optional, **server-private**, reference-free (e.g. per-observation candidate score distributions). Only A's scorer reads it; B never serialises/logs/returns it. |
| `warnings[].code` | registry: `gps_gap`, `decoder_break`, `no_candidates`, `invalid_observations`, `network_context_truncated`, `diagnostic_model`. |

## 3. Scoring policy (A owns; PROVISIONAL until A + organisers settle it)

Policy id `pathsnap-scoring-v0`, `policy_status="provisional"`. Metric registry (names on the wire):

| name | unit | intended denominator (A to define precisely) |
|---|---|---|
| `top1_accuracy` | fraction | all scorable observations (alignment-derived labels), **including** candidate misses and unmatched |
| `macro_f1` | fraction | per-trip macro over graph-local arcs present in labels ∪ predictions |
| `precision_macro`, `recall_macro` | fraction | as macro_f1 |
| `candidate_miss_rate` | fraction | scorable observations whose label arc is absent from the candidate set |
| `route_continuity` | fraction | consecutive matched pairs that are the same/adjacent/legally connected arcs |
| `sequence_*` | A to define | e.g. route-arc overlap / edit-distance based |
| `log_loss` | nats | observation-level candidate distribution, **conditional on candidate coverage**; misses reported separately. In the API it is `null` with an explicit reason unless the scorer gets the full candidate distribution via `scorer_evidence`; the experiment runner computes the full value for the report. |
| `scorable_observations` | count | — |

Every `MetricValue` carries `numerator`, `denominator`, `denominator_policy` text and a nullable `value` + `unavailable_reason`.

## 4. HTTP (B implements)

| Endpoint | Success | Errors |
|---|---|---|
| `GET /health` | 200 always while alive; `ready` = bundle loaded **and** partition configured | — |
| `GET /trips` | 200 `{mode, partition_label, trip_ids, count}` | 503 `data_not_configured` |
| `POST /predict` `{"trip_id": "..."}` | 200 `PredictResponse` | 404 `unknown_trip` · 422 `invalid_request` · 429 `busy` · 500 `prediction_failed`/`internal_error` · 503 `model_not_ready`/`data_not_configured`/`trip_data_unavailable` |

- Mode is server configuration (`PATHSNAP_MODE`), never a request field. No paths, hyperparameters or labels in requests.
- Every response has `X-Request-ID` == body `request_id`; Laptop 1 logs `request_id, trip_id, mode, model_version, stage timings, outcome`.
- Error `message` is display-safe (no paths/tracebacks/labels). Details go to server logs only.
- `synthetic` is `false` for every live response; `true` only in fixtures.

## 5. Artifacts and results (A produces, B validates)

- `<bundle_root>/manifest.json` follows `BundleManifest`. All file paths relative to `bundle_root`; SHA-256 verified at startup.
- Result records (`ResultRecord`) live under `results/{experiments,hpo,hmm}/<run_id>/`; B's report tooling reads them verbatim and never recomputes metrics.
- Development Folium handoff (`DevVisualisation`): train/student_test trips only, written by A to `results/hmm/visualisation/<run_id>/<trip_id>.json`. Read only by `src/visualisation/folium/**`. Not reachable from the API or `ui/`.

## 6. Ports and processes

| Process | Owner | Port |
|---|---|---|
| FastAPI (`uvicorn api.main:app`) | B | 8000 |
| Vite dev / preview UI | B | 5173 / 4173 |
| A's ad-hoc tools (if any) | A | 8100–8199 |

Each worker records PID/port in its own status file before starting a server and stops only its own processes.

## 7. Change process

Owner edits the canonical file on their branch → updates `contracts/current-manifest.json` (`python3 scripts/contract_hash.py --write`) → sends PROPOSAL with version + aggregate hash → peer recomputes and ACKs that hash. Breaking changes bump the version.
