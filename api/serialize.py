"""Map contract dataclasses to the HTTP wire format (contracts/http.schema.json).

Explicit field-by-field mapping on purpose: nothing A adds to PredictionResult (e.g.
scorer_evidence, TripInput.payload) can leak to the browser unless it is listed here.
"""
from __future__ import annotations

from typing import Any, Optional

from src.contracts import CONTRACT_VERSION, EvaluationSummary, PredictionResult

PARTITION_LABELS = {
    "development": "Student-testing trips (development mode)",
    "evaluator": "Reserved evaluation trips",
}


def model_identity(info: Any) -> dict:
    return {
        "version": info.model_version,
        "kind": info.model_kind,
        "family": info.model_family,
        "decoder": info.decoder,
        "run_id": info.run_id,
    }


def _lonlat(lon: Optional[float], lat: Optional[float]) -> Optional[list[float]]:
    if lon is None or lat is None:
        return None
    return [lon, lat]


def evaluation_to_wire(summary: EvaluationSummary) -> dict:
    return {
        "status": summary.status,
        "policy_id": summary.policy_id,
        "policy_status": summary.policy_status,
        "unavailable_reason": summary.unavailable_reason,
        "metrics": [
            {
                "name": m.name,
                "value": m.value,
                "unit": m.unit,
                "numerator": m.numerator,
                "denominator": m.denominator,
                "denominator_policy": m.denominator_policy,
                "unavailable_reason": m.unavailable_reason,
            }
            for m in summary.metrics
        ],
    }


def prediction_to_wire(
    *,
    request_id: str,
    result: PredictionResult,
    model: dict,
    evaluation: dict,
    scoring_ms: Optional[float],
    request_ms: float,
) -> dict:
    return {
        "schema_version": CONTRACT_VERSION,
        "request_id": request_id,
        "mode": result.mode,
        "partition_label": PARTITION_LABELS[result.mode],
        "trip_id": result.trip_id,
        "model": model,
        "score_kind": result.score_kind,
        "observation_count": result.observation_count,
        "observations": [
            {
                "index": o.index,
                "lon": o.lon,
                "lat": o.lat,
                "t": o.t,
                "status": o.status,
                "segment_id": o.segment_id,
                "arc_id": o.arc_id,
                "snapped": _lonlat(o.snapped_lon, o.snapped_lat),
                "distance_m": o.distance_m,
                "score": o.score,
                "candidate_count": o.candidate_count,
                "reason": o.reason,
            }
            for o in result.observations
        ],
        "route": {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "LineString", "coordinates": [list(c) for c in p.coordinates]},
                    "properties": {
                        "segment_id": p.segment_id,
                        "first_index": p.first_index,
                        "last_index": p.last_index,
                        "arc_ids": [a.arc_id for a in p.arcs],
                        "arc_roles": [a.role for a in p.arcs],
                    },
                }
                for p in result.route
            ],
        },
        "network": {
            "type": "FeatureCollection",
            "policy": result.network_context_policy,
            "truncated": result.network_context_truncated,
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "LineString", "coordinates": [list(c) for c in s.coordinates]},
                    "properties": {"arc_id": s.arc_id, "from_node": s.from_node, "to_node": s.to_node},
                }
                for s in result.network_context
            ],
        },
        "bounds": list(result.bounds),
        "timings": {
            "pipeline_ms": dict(result.timings_ms),
            "scoring_ms": scoring_ms,
            "request_ms": request_ms,
        },
        "warnings": [
            {
                "code": w.code,
                "message": w.message,
                "observation_indices": list(w.observation_indices) if w.observation_indices is not None else None,
            }
            for w in result.warnings
        ],
        "evaluation": evaluation,
        "synthetic": False,
    }
