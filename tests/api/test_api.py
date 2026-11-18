"""API contract, error and leakage tests. Uses a SYNTHETIC fake facade (no real data/model).

Run from the repo root:  python -m pytest tests/api -q
"""
from __future__ import annotations

import hashlib
import json
import math
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import jsonschema
import pytest
from fastapi.testclient import TestClient

from api.config import ApiConfig
from api.main import create_app
from api.service import PathSnapService
from src.contracts import (
    BundleInfo,
    DataNotConfiguredError,
    EvaluationSummary,
    MetricValue,
    NetworkSegment,
    ObservationPrediction,
    PipelineSettings,
    PipelineWarning,
    PredictionResult,
    RouteArc,
    RoutePiece,
    TripInput,
    UnknownTripError,
)

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = json.loads((ROOT / "contracts" / "http.schema.json").read_text())
FORBIDDEN_KEYS = {"reference", "route_arcs", "reference_arcs", "label", "labels", "correct", "is_correct",
                  "truth", "ground_truth", "scorer_evidence", "payload", "mask"}


def validator(defn: str) -> jsonschema.Draft202012Validator:
    return jsonschema.Draft202012Validator({**SCHEMA, "$ref": f"#/$defs/{defn}"})


def all_keys(obj) -> set[str]:
    if isinstance(obj, dict):
        return set(obj) | set().union(*(all_keys(v) for v in obj.values()))
    if isinstance(obj, list):
        return set().union(*(all_keys(v) for v in obj)) if obj else set()
    return set()


# ---------------------------------------------------------------- synthetic fixtures
def make_bundle_dir(tmp_path: Path, kind: str = "trained") -> Path:
    root = tmp_path / "bundle"
    root.mkdir()
    (root / "model.bin").write_bytes(b"synthetic test bytes")
    manifest = {
        "manifest_version": 1, "contract_version": "0.1.0", "model_version": "synthetic-1",
        "model_kind": kind, "model_family": "synthetic", "decoder": "hmm_viterbi", "run_id": "synthetic",
        "source_git_sha": "0" * 40, "config_sha256": "0" * 64, "data_fingerprint": "synthetic",
        "files": [{"role": "classifier", "path": "model.bin",
                   "sha256": hashlib.sha256(b"synthetic test bytes").hexdigest(), "bytes": 20}],
        "features": [{"name": "distance_m", "dtype": "float64"}], "score_kind": "normalized_score",
        "crs": {"input": "EPSG:4326"}, "graph_assumptions": {}, "candidate_policy": {},
        "decoder_config": {}, "dependencies": {},
    }
    (root / "manifest.json").write_text(json.dumps(manifest))
    return root


def synthetic_result(trip_id: str, mode: str) -> PredictionResult:
    obs = (
        ObservationPrediction(0, 10.0, 50.0, 0.0, "matched", 0, 0, 10.0, 50.00001, 1.1, 0.9, 2),
        ObservationPrediction(1, 10.0005, 50.0, 1.0, "matched", 0, 1, 10.0005, 50.00001, 1.1, 0.8, 2),
        ObservationPrediction(2, None, None, 2.0, "invalid", reason="non_finite_coordinate"),
        ObservationPrediction(3, 10.01, 50.01, 40.0, "no_candidate", reason="outside_candidate_radius"),
        ObservationPrediction(4, 10.002, 50.002, 60.0, "matched", 1, 3, 10.002, 50.00201, 1.1, 0.7, 1),
    )
    return PredictionResult(
        trip_id=trip_id, mode=mode, model_version="synthetic-1", model_kind="trained",
        model_family="synthetic", decoder="hmm_viterbi", score_kind="normalized_score",
        observation_count=5, observations=obs,
        route=(
            RoutePiece(0, 0, 1, (RouteArc(0, "observed"), RouteArc(1, "observed")),
                       ((9.9995, 50.00001), (10.0, 50.00001), (10.001, 50.00001))),
            RoutePiece(1, 4, 4, (RouteArc(3, "observed"),), ((10.0015, 50.00201), (10.0025, 50.00201))),
        ),
        network_context=(NetworkSegment(0, 0, 1, ((9.9995, 50.00001), (10.0, 50.00001))),),
        network_context_policy="synthetic", network_context_truncated=False,
        bounds=(9.9995, 50.0, 10.01, 50.01), timings_ms={"predict_total": 1.0},
        warnings=(PipelineWarning("gps_gap", "synthetic gap", (3, 4)),),
        scorer_evidence={"secret_candidate_scores": [[0.9, 0.1]]},
    )


class FakeFacade:
    """Synthetic stand-in for A's src.pipeline + scorer. Records call order."""

    def __init__(self, trips=("00000000", "00000007"), evaluator_trips=None, kind="trained"):
        self.trips, self.evaluator_trips, self.kind, self.calls = list(trips), evaluator_trips, kind, []
        self.score_raises = False
        self.result_override = None

    def load_model_bundle(self, settings):
        self.calls.append("load_model_bundle")
        return SimpleNamespace(info=BundleInfo("synthetic-1", self.kind, "synthetic", "hmm_viterbi", "synthetic", "x"))

    def list_trip_ids(self, mode, settings):
        if mode == "evaluator":
            if self.evaluator_trips is None:
                raise DataNotConfiguredError("Reserved evaluation trips are not configured.")
            return list(self.evaluator_trips)
        return list(self.trips)

    def load_prediction_input(self, trip_id, mode, settings):
        self.calls.append(("load_prediction_input", trip_id, mode))
        if trip_id not in self.list_trip_ids(mode, settings):
            raise UnknownTripError("unknown")
        return TripInput(trip_id, mode, "student_test", 5, 6, 4)

    def predict_trip(self, trip_input, bundle, options):
        self.calls.append("predict_trip")
        if self.result_override:
            return self.result_override(trip_input)
        return synthetic_result(trip_input.trip_id, trip_input.mode)

    def evaluate_completed_prediction(self, prediction, scoring_settings):
        self.calls.append("evaluate_completed_prediction")
        if self.score_raises:
            raise RuntimeError("synthetic scorer failure")
        return EvaluationSummary("scored", "pathsnap-scoring-v0", "provisional",
                                 (MetricValue("top1_accuracy", 0.5, "fraction", 1, 2, "synthetic"),))


def client_for(tmp_path, facade=None, mode="development", bundle_kind="trained", bundle=True):
    bundle_root = make_bundle_dir(tmp_path, bundle_kind) if bundle else tmp_path / "missing"
    cfg = ApiConfig(mode=mode, pipeline=PipelineSettings(tmp_path, bundle_root, None), cors_origins=("http://ui.test",))
    svc = PathSnapService(config=cfg, facade=facade or FakeFacade())
    return TestClient(create_app(svc)), svc


# ---------------------------------------------------------------- tests
def test_health_ready_and_schema(tmp_path):
    c, _ = client_for(tmp_path)
    with c:
        r = c.get("/health")
    assert r.status_code == 200
    validator("HealthResponse").validate(r.json())
    assert r.json()["ready"] is True and r.json()["mode"] == "development"
    assert r.headers["X-Request-ID"]


def test_trips_lists_partition_ids_as_strings(tmp_path):
    c, _ = client_for(tmp_path)
    with c:
        r = c.get("/trips")
    validator("TripsResponse").validate(r.json())
    assert r.json()["trip_ids"] == ["00000000", "00000007"]
    assert "development" in r.json()["partition_label"]


def test_evaluator_mode_unconfigured_never_substitutes(tmp_path):
    c, _ = client_for(tmp_path, mode="evaluator")
    with c:
        h, t, p = c.get("/health"), c.get("/trips"), c.post("/predict", json={"trip_id": "00000000"})
    assert h.json()["ready"] is False and h.json()["data_configured"] is False
    assert t.status_code == 503 and t.json()["error"]["code"] == "data_not_configured"
    validator("ErrorResponse").validate(t.json())
    assert p.status_code == 503 and p.json()["error"]["code"] == "data_not_configured"


def test_predict_success_schema_request_id_and_order(tmp_path):
    fake = FakeFacade()
    c, _ = client_for(tmp_path, fake)
    with c:
        r = c.post("/predict", json={"trip_id": "00000007"}, headers={"X-Request-ID": "test-req-0001"})
    assert r.status_code == 200, r.text
    body = r.json()
    validator("PredictResponse").validate(body)
    assert body["request_id"] == r.headers["X-Request-ID"] == "test-req-0001"
    assert body["synthetic"] is False and body["trip_id"] == "00000007"
    assert [o["index"] for o in body["observations"]] == list(range(5))
    assert len(body["route"]["features"]) == 2  # disconnected pieces stay separate
    # scorer is called only after prediction completed
    assert fake.calls.index("evaluate_completed_prediction") > fake.calls.index("predict_trip")
    assert "load_input" in body["timings"]["pipeline_ms"]


def test_predict_response_has_no_reference_or_private_fields(tmp_path):
    c, _ = client_for(tmp_path)
    with c:
        body = c.post("/predict", json={"trip_id": "00000000"}).json()
    assert not (all_keys(body) & FORBIDDEN_KEYS)
    assert "secret_candidate_scores" not in json.dumps(body)


@pytest.mark.parametrize("payload,status,code", [
    ({"trip_id": "99999999"}, 404, "unknown_trip"),
    ({"trip_id": "../../etc/passwd"}, 422, "invalid_request"),
    ({"trip_id": "00000000", "mode": "evaluator"}, 422, "invalid_request"),
    ({"trip_id": "00000000", "path": "/tmp"}, 422, "invalid_request"),
    ({}, 422, "invalid_request"),
])
def test_predict_rejections(tmp_path, payload, status, code):
    c, _ = client_for(tmp_path)
    with c:
        r = c.post("/predict", json=payload)
    assert r.status_code == status and r.json()["error"]["code"] == code
    validator("ErrorResponse").validate(r.json())


def test_missing_bundle_is_not_ready(tmp_path):
    c, _ = client_for(tmp_path, bundle=False)
    with c:
        h, p = c.get("/health").json(), c.post("/predict", json={"trip_id": "00000000"})
    assert h["ready"] is False and "bundle_manifest_missing" in h["not_ready_reasons"]
    assert not any(str(tmp_path) in r for r in h["not_ready_reasons"])  # no paths leak
    assert p.status_code == 503 and p.json()["error"]["code"] == "model_not_ready"
    assert p.headers["Retry-After"] == "5"


def test_checksum_mismatch_is_not_ready(tmp_path):
    fake = FakeFacade()
    c, svc = client_for(tmp_path, fake)
    (svc.config.pipeline.bundle_root / "model.bin").write_bytes(b"tampered")
    with c:
        h = c.get("/health").json()
    assert h["ready"] is False and "bundle_checksum_mismatch:classifier" in h["not_ready_reasons"]
    assert "load_model_bundle" not in fake.calls


def test_diagnostic_bundle_refused_in_evaluator_mode(tmp_path):
    fake = FakeFacade(evaluator_trips=["E1"], kind="diagnostic")
    c, _ = client_for(tmp_path, fake, mode="evaluator", bundle_kind="diagnostic")
    with c:
        h = c.get("/health").json()
    assert h["ready"] is False and "diagnostic_bundle_not_allowed_in_evaluator_mode" in h["not_ready_reasons"]


def test_diagnostic_bundle_allowed_and_labelled_in_development(tmp_path):
    c, _ = client_for(tmp_path, FakeFacade(kind="diagnostic"), bundle_kind="diagnostic")
    with c:
        h = c.get("/health").json()
    assert h["ready"] is True and h["model"]["kind"] == "diagnostic"


def test_busy_returns_429(tmp_path):
    c, svc = client_for(tmp_path)
    with c:
        assert svc._slots.acquire(blocking=False)
        try:
            r = c.post("/predict", json={"trip_id": "00000000"})
        finally:
            svc._slots.release()
    assert r.status_code == 429 and r.json()["error"]["retryable"] is True and r.headers["Retry-After"]


def test_scorer_failure_keeps_prediction(tmp_path):
    fake = FakeFacade()
    fake.score_raises = True
    c, _ = client_for(tmp_path, fake)
    with c:
        r = c.post("/predict", json={"trip_id": "00000000"})
    assert r.status_code == 200
    assert r.json()["evaluation"]["status"] == "unavailable"
    assert r.json()["evaluation"]["metrics"] == []


def test_non_finite_result_is_rejected_not_serialised(tmp_path):
    fake = FakeFacade()

    def bad(ti):
        res = synthetic_result(ti.trip_id, ti.mode)
        obs = list(res.observations)
        obs[0] = replace(obs[0], score=math.nan)
        return replace(res, observations=tuple(obs))

    fake.result_override = bad
    c, _ = client_for(tmp_path, fake)
    with c:
        r = c.post("/predict", json={"trip_id": "00000000"})
    assert r.status_code == 500 and r.json()["error"]["code"] == "prediction_failed"
    assert "nan" not in r.json()["error"]["message"].lower()


def test_cors_allows_configured_origin_only(tmp_path):
    c, _ = client_for(tmp_path)
    with c:
        ok = c.options("/predict", headers={"Origin": "http://ui.test", "Access-Control-Request-Method": "POST"})
        bad = c.options("/predict", headers={"Origin": "http://evil.test", "Access-Control-Request-Method": "POST"})
    assert ok.headers.get("access-control-allow-origin") == "http://ui.test"
    assert "access-control-allow-origin" not in bad.headers


def test_synthetic_fixture_matches_schema():
    fx = json.loads((ROOT / "contracts" / "fixtures" / "predict_response.synthetic.v0.1.0.json").read_text())
    validator("PredictResponse").validate(fx)
    assert fx["synthetic"] is True


def test_contract_manifest_is_current():
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "contract_hash.py"), "--check"], capture_output=True)
    assert r.returncode == 0, r.stderr.decode()
