"""Shared, serialisable boundary types for PathSnap (contract owner: LLM B).

These types are the agreed seam between the scientific pipeline (``src.pipeline``,
``src.evaluation.service``; owned by A) and the transport layer (``api/``; owned by B).
They are deliberately stdlib-only (dataclasses + typing) so the ML code needs no web
framework and the API never has to import pandas/sklearn/networkx objects.

Conventions (see contracts/interfaces.md for the full text):
- Coordinates on every boundary are WGS84 ``(lon, lat)`` in that order.
- Bounds are ``(west, south, east, north)`` i.e. ``(min_lon, min_lat, max_lon, max_lat)``.
- Times are seconds (as in the raw ``.track`` file), distances metres, timings milliseconds.
- Trip IDs are strings (leading zeros preserved). Arc/node IDs are graph-local integers
  equal to the 0-based row index in that trip's ``.arcs`` / ``.nodes`` file.
- No NaN/inf anywhere: missing numeric values are ``None``.
- Nothing in PredictionResult or EvaluationSummary may carry reference-route arcs,
  per-observation reference labels or correctness masks.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, Optional, Protocol, Sequence

CONTRACT_VERSION = "0.1.0"

# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

Mode = Literal["development", "evaluator"]
"""Server operating mode. development -> student_test partition; evaluator -> reserved root."""

Partition = Literal["train", "student_test", "evaluator_test"]

MODE_TO_PARTITION: dict[str, str] = {
    "development": "student_test",
    "evaluator": "evaluator_test",
}

ModelKind = Literal["trained", "diagnostic"]
"""diagnostic = reference-free geometric adapter used only for M1 wiring; never final."""

DecoderKind = Literal["hmm_viterbi", "classifier_only", "none"]

ScoreKind = Literal["calibrated_probability", "normalized_score", "none"]
"""Semantics of ObservationPrediction.score. A normalised relevance score is NOT a probability."""

ObservationStatus = Literal[
    "matched",       # decoder/classifier assigned an arc
    "no_candidate",  # valid observation, but no candidate arc inside the candidate policy
    "invalid",       # removed by cleaning (bad coordinate, duplicate/backward timestamp, ...)
    "unmatched",     # had candidates, but the decoder could not assign a state (e.g. unreachable)
]

ArcRole = Literal["observed", "connector"]
"""observed = arc chosen for at least one observation; connector = graph path between them."""

EvaluationStatus = Literal["scored", "unavailable"]
PolicyStatus = Literal["provisional", "agreed"]

TRIP_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
"""Syntactic guard only. Membership in the configured partition's allowlist is still required."""


# ---------------------------------------------------------------------------
# Errors (shared so the API maps them to HTTP without string matching)
# ---------------------------------------------------------------------------


class PathSnapError(Exception):
    """Base class. ``code`` is the stable machine-readable error code used on the wire."""

    code: str = "internal_error"
    http_status: int = 500
    retryable: bool = False

    def __init__(self, message: str, *, detail: Optional[str] = None) -> None:
        super().__init__(message)
        self.message = message
        # detail is for server logs only; never sent to the browser.
        self.detail = detail


class InvalidTripIdError(PathSnapError):
    code, http_status = "invalid_request", 422


class UnknownTripError(PathSnapError):
    code, http_status = "unknown_trip", 404


class DataNotConfiguredError(PathSnapError):
    """The partition for the active mode is not provisioned (e.g. evaluator root absent)."""

    code, http_status = "data_not_configured", 503


class TripDataUnavailableError(PathSnapError):
    """Allowlisted trip whose input files are missing/unreadable/malformed, or that has no
    valid observation at all (so no finite bounds exist; no sentinel bounds are emitted)."""

    code, http_status = "trip_data_unavailable", 503


class ModelNotReadyError(PathSnapError):
    """Artifacts missing, checksum mismatch, incompatible schema/feature version, or a
    diagnostic bundle (model_kind="diagnostic") loaded while mode == "evaluator"."""

    code, http_status, retryable = "model_not_ready", 503, True


class PredictionFailedError(PathSnapError):
    code, http_status = "prediction_failed", 500


# ---------------------------------------------------------------------------
# Settings / options
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PipelineSettings:
    """Explicit, portable configuration. No implicit CWD-relative paths.

    data_root:      development dataset root containing ``train/`` and ``student_test/``.
    evaluator_root: reserved evaluator root (``<root>/<trip_id>/<trip_id>.{track,nodes,arcs}``),
                    or None when not provisioned. Never substituted by student_test.
    bundle_root:    directory holding the artifact manifest (``manifest.json``) and files.
    """

    data_root: Path
    bundle_root: Path
    evaluator_root: Optional[Path] = None


@dataclass(frozen=True)
class PredictOptions:
    """Server-side options; NOT exposed to HTTP clients."""

    decoder: DecoderKind = "hmm_viterbi"
    include_network_context: bool = True
    max_network_segments: int = 6000


@dataclass(frozen=True)
class ScoringSettings:
    settings: PipelineSettings
    mode: Mode
    policy_id: str = "pathsnap-scoring-v0"


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TripInput:
    """Reference-free inputs for one trip (.track, .nodes, .arcs only; never .route).

    ``payload`` is private to A's pipeline (arrays/graph); B treats it as opaque and never
    serialises it. ``observation_count`` is the number of rows in the raw .track file.
    """

    trip_id: str
    mode: Mode
    partition: Partition
    observation_count: int
    node_count: int
    arc_count: int
    payload: Any = field(repr=False, compare=False, default=None)


class ModelBundleInfo(Protocol):
    model_version: str
    model_kind: ModelKind
    model_family: str
    decoder: DecoderKind
    run_id: str
    manifest_sha256: str


class ModelBundle(Protocol):
    """Opaque to B. Must expose ``info``; everything else is A-private."""

    @property
    def info(self) -> ModelBundleInfo: ...


@dataclass(frozen=True)
class BundleInfo:
    """Concrete ModelBundleInfo that A may use."""

    model_version: str
    model_kind: ModelKind
    model_family: str
    decoder: DecoderKind
    run_id: str
    manifest_sha256: str


# ---------------------------------------------------------------------------
# Prediction output
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ObservationPrediction:
    """One record per raw .track row, in original order (index == 0-based row number)."""

    index: int
    lon: Optional[float]
    lat: Optional[float]
    t: Optional[float]
    status: ObservationStatus
    segment_id: Optional[int] = None  # decoding segment; a new id starts after a break
    arc_id: Optional[int] = None
    snapped_lon: Optional[float] = None
    snapped_lat: Optional[float] = None
    distance_m: Optional[float] = None  # GPS point -> snapped point, metres
    score: Optional[float] = None  # semantics given by PredictionResult.score_kind
    candidate_count: int = 0
    reason: Optional[str] = None  # short machine code for invalid/no_candidate/unmatched


@dataclass(frozen=True)
class RouteArc:
    arc_id: int
    role: ArcRole


@dataclass(frozen=True)
class RoutePiece:
    """A connected stretch of predicted route. Pieces are never joined by straight lines."""

    segment_id: int
    first_index: int  # first original observation index covered
    last_index: int
    arcs: tuple[RouteArc, ...]
    coordinates: tuple[tuple[float, float], ...]  # (lon, lat) along actual arc geometry


@dataclass(frozen=True)
class NetworkSegment:
    arc_id: int
    from_node: int
    to_node: int
    coordinates: tuple[tuple[float, float], ...]  # (lon, lat), from_node -> to_node


@dataclass(frozen=True)
class PipelineWarning:
    code: str  # e.g. "gps_gap", "decoder_break", "no_candidates", "network_context_truncated"
    message: str
    observation_indices: Optional[tuple[int, ...]] = None


@dataclass(frozen=True)
class PredictionResult:
    trip_id: str
    mode: Mode
    model_version: str
    model_kind: ModelKind
    model_family: str
    decoder: DecoderKind
    score_kind: ScoreKind
    observation_count: int
    observations: tuple[ObservationPrediction, ...]
    route: tuple[RoutePiece, ...]
    network_context: tuple[NetworkSegment, ...]
    network_context_policy: str  # human-readable, e.g. "arcs within 150 m of any GPS point"
    network_context_truncated: bool
    bounds: tuple[float, float, float, float]  # (west, south, east, north)
    timings_ms: dict[str, float]  # stage -> ms; keys documented in interfaces.md
    warnings: tuple[PipelineWarning, ...] = ()
    # Server-private, reference-free evidence for A's scorer (e.g. per-observation candidate
    # score distributions for conditional log loss). B never serialises, logs or returns it.
    scorer_evidence: Any = field(default=None, repr=False, compare=False)


# ---------------------------------------------------------------------------
# Evaluation output (aggregate only)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MetricValue:
    name: str  # registry in interfaces.md (top1_accuracy, macro_f1, ...)
    value: Optional[float]
    unit: Optional[str]  # "fraction", "nats", "count", "ms", ...
    numerator: Optional[int]
    denominator: Optional[int]
    denominator_policy: str
    unavailable_reason: Optional[str] = None


@dataclass(frozen=True)
class EvaluationSummary:
    """Aggregate metrics only. Never per-observation labels/correctness or reference geometry."""

    status: EvaluationStatus
    policy_id: str
    policy_status: PolicyStatus
    metrics: tuple[MetricValue, ...] = ()
    unavailable_reason: Optional[str] = None
    elapsed_ms: Optional[float] = None


# ---------------------------------------------------------------------------
# Facade signatures implemented by A (documented here for type checking)
# ---------------------------------------------------------------------------


class PipelineFacade(Protocol):
    def load_model_bundle(self, settings: PipelineSettings) -> ModelBundle: ...

    def list_trip_ids(self, mode: Mode, settings: PipelineSettings) -> Sequence[str]: ...

    def load_prediction_input(
        self, trip_id: str, mode: Mode, settings: PipelineSettings
    ) -> TripInput: ...

    def predict_trip(
        self, trip_input: TripInput, bundle: ModelBundle, options: PredictOptions
    ) -> PredictionResult: ...


class ScorerFacade(Protocol):
    def evaluate_completed_prediction(
        self, prediction: PredictionResult, scoring_settings: ScoringSettings
    ) -> EvaluationSummary: ...


# ---------------------------------------------------------------------------
# Small validators shared by producer and consumer tests
# ---------------------------------------------------------------------------


def validate_trip_id_syntax(trip_id: str) -> str:
    if not isinstance(trip_id, str) or not TRIP_ID_PATTERN.fullmatch(trip_id):
        raise InvalidTripIdError("trip_id must be 1-64 characters of [A-Za-z0-9_-]")
    return trip_id


def _finite_or_none(x: Optional[float]) -> bool:
    return x is None or (isinstance(x, (int, float)) and math.isfinite(x))


def check_prediction_invariants(result: PredictionResult) -> list[str]:
    """Return a list of contract violations (empty list == valid)."""
    problems: list[str] = []
    if len(result.observations) != result.observation_count:
        problems.append("observations length != observation_count")
    for i, ob in enumerate(result.observations):
        if ob.index != i:
            problems.append(f"observation {i} has index {ob.index}; must preserve input order")
            break
        if ob.status == "matched" and ob.arc_id is None:
            problems.append(f"observation {i} matched without arc_id")
        if ob.status != "matched" and ob.arc_id is not None:
            problems.append(f"observation {i} status {ob.status} carries arc_id")
        for v in (ob.lon, ob.lat, ob.t, ob.snapped_lon, ob.snapped_lat, ob.distance_m, ob.score):
            if not _finite_or_none(v):
                problems.append(f"observation {i} has non-finite number")
                break
    w, s, e, n = result.bounds
    if not (w <= e and s <= n):
        problems.append("bounds must be (west, south, east, north)")
    for piece in result.route:
        if len(piece.coordinates) < 2:
            problems.append(f"route piece {piece.segment_id} has <2 coordinates")
        if piece.first_index > piece.last_index:
            problems.append(f"route piece {piece.segment_id} index range reversed")
    return problems
