"""Transport-side orchestration: readiness, allowlisting, bounded prediction, isolated scoring.

All ML work is delegated to A's facade (src.pipeline / src.evaluation.service). The facade
is injected so tests can use clearly synthetic fakes; production imports the real modules.
"""
from __future__ import annotations

import importlib
import logging
import threading
import time
from dataclasses import dataclass, field, replace
from types import SimpleNamespace
from typing import Any, Optional

from src.contracts import (
    DataNotConfiguredError,
    ModelNotReadyError,
    PathSnapError,
    PredictionFailedError,
    PredictOptions,
    ScoringSettings,
    UnknownTripError,
    check_prediction_invariants,
    validate_trip_id_syntax,
)

from . import API_VERSION
from .bundle_check import check_bundle
from .config import ApiConfig
from .serialize import PARTITION_LABELS, evaluation_to_wire, model_identity, prediction_to_wire

log = logging.getLogger("pathsnap.api")


class BusyError(PathSnapError):
    code, http_status, retryable = "busy", 429, True


def load_real_facade() -> SimpleNamespace:
    pipeline = importlib.import_module("src.pipeline")
    scorer = importlib.import_module("src.evaluation.service")
    return SimpleNamespace(
        load_model_bundle=pipeline.load_model_bundle,
        list_trip_ids=pipeline.list_trip_ids,
        load_prediction_input=pipeline.load_prediction_input,
        predict_trip=pipeline.predict_trip,
        evaluate_completed_prediction=scorer.evaluate_completed_prediction,
    )


@dataclass
class PathSnapService:
    config: ApiConfig
    facade: Any = None
    bundle: Any = None
    not_ready: list[str] = field(default_factory=list)
    _slots: threading.BoundedSemaphore = field(init=False)

    def __post_init__(self) -> None:
        self._slots = threading.BoundedSemaphore(self.config.max_concurrent_predictions)

    # -- startup -----------------------------------------------------------------
    def start(self) -> None:
        t0 = time.perf_counter()
        self.not_ready = []
        if self.facade is None:
            try:
                self.facade = load_real_facade()
            except Exception as exc:  # noqa: BLE001 - surfaced as a readiness reason
                log.error("facade_import_failed error=%r", exc)
                self.not_ready.append("pipeline_code_unavailable")
                return
        problems = check_bundle(self.config.pipeline.bundle_root, self.config.mode)
        if problems:
            self.not_ready.extend(problems)
            log.warning("bundle_check_failed problems=%s", problems)
            return
        try:
            self.bundle = self.facade.load_model_bundle(self.config.pipeline)
        except ModelNotReadyError as exc:
            self.not_ready.append("model_not_ready")
            log.warning("model_not_ready message=%s detail=%s", exc.message, exc.detail)
            return
        except Exception as exc:  # noqa: BLE001
            self.not_ready.append("model_load_failed")
            log.exception("model_load_failed error=%r", exc)
            return
        info = self.bundle.info
        if info.model_kind == "diagnostic" and self.config.mode == "evaluator":
            self.bundle = None
            self.not_ready.append("diagnostic_bundle_not_allowed_in_evaluator_mode")
            return
        log.info(
            "startup_ready mode=%s model_version=%s kind=%s family=%s decoder=%s run_id=%s startup_ms=%.1f",
            self.config.mode, info.model_version, info.model_kind, info.model_family, info.decoder,
            info.run_id, (time.perf_counter() - t0) * 1000,
        )

    # -- read endpoints ----------------------------------------------------------------
    def _data_configured(self) -> bool:
        if self.facade is None:
            return False
        try:
            self.facade.list_trip_ids(self.config.mode, self.config.pipeline)
            return True
        except DataNotConfiguredError:
            return False
        except Exception:  # noqa: BLE001
            log.exception("list_trip_ids_failed")
            return False

    def health(self) -> dict:
        data_ok = self._data_configured()
        reasons = list(self.not_ready)
        if not data_ok and "data_not_configured" not in reasons:
            reasons.append("data_not_configured")
        ready = self.bundle is not None and data_ok
        return {
            "service": "pathsnap-api",
            "api_version": API_VERSION,
            "status": "ok" if ready else "degraded",
            "ready": ready,
            "mode": self.config.mode,
            "data_configured": data_ok,
            "model": model_identity(self.bundle.info) if self.bundle is not None else None,
            "not_ready_reasons": reasons,
        }

    def trips(self) -> dict:
        if self.facade is None:
            raise DataNotConfiguredError("Trip data is not configured on the server.")
        ids = sorted(str(t) for t in self.facade.list_trip_ids(self.config.mode, self.config.pipeline))
        return {
            "mode": self.config.mode,
            "partition_label": PARTITION_LABELS[self.config.mode],
            "trip_ids": ids,
            "count": len(ids),
        }

    # -- prediction ----------------------------------------------------------------
    def predict(self, trip_id: str, request_id: str, started: float) -> dict:
        validate_trip_id_syntax(trip_id)
        if self.bundle is None:
            raise ModelNotReadyError("The model is not loaded on the server.")
        allowed = set(self.trips()["trip_ids"])
        if trip_id not in allowed:
            raise UnknownTripError(f"Trip {trip_id} is not one of the {len(allowed)} trips this server offers.")
        if not self._slots.acquire(blocking=False):
            raise BusyError("Another reconstruction is running. Try again in a few seconds.")
        try:
            info = self.bundle.info
            log.info("predict_start request_id=%s trip_id=%s mode=%s model_version=%s",
                     request_id, trip_id, self.config.mode, info.model_version)
            t_load = time.perf_counter()
            trip_input = self.facade.load_prediction_input(trip_id, self.config.mode, self.config.pipeline)
            load_ms = (time.perf_counter() - t_load) * 1000
            try:
                result = self.facade.predict_trip(trip_input, self.bundle, PredictOptions())
            except PathSnapError:
                raise
            except Exception as exc:  # noqa: BLE001
                raise PredictionFailedError("The prediction pipeline failed for this trip.", detail=repr(exc)) from exc
            problems = check_prediction_invariants(result)
            if problems or result.trip_id != trip_id:
                raise PredictionFailedError("The pipeline returned an invalid result.", detail=str(problems))
            timings = dict(result.timings_ms)
            timings.setdefault("load_input", load_ms)
            log.info("predict_done request_id=%s trip_id=%s observations=%d matched=%d pieces=%d stages_ms=%s",
                     request_id, trip_id, result.observation_count,
                     sum(1 for o in result.observations if o.status == "matched"), len(result.route),
                     {k: round(v, 1) for k, v in timings.items()})
            # Scoring runs only after prediction has completed, through A's isolated scorer.
            t_score = time.perf_counter()
            try:
                summary = self.facade.evaluate_completed_prediction(
                    result, ScoringSettings(settings=self.config.pipeline, mode=self.config.mode)
                )
                evaluation = evaluation_to_wire(summary)
            except Exception as exc:  # noqa: BLE001 - scoring failure never fails the prediction
                log.exception("scoring_failed request_id=%s trip_id=%s error=%r", request_id, trip_id, exc)
                evaluation = {
                    "status": "unavailable", "policy_id": "unknown", "policy_status": "provisional",
                    "metrics": [], "unavailable_reason": "Scoring failed on the server; see API logs.",
                }
            scoring_ms = (time.perf_counter() - t_score) * 1000
            log.info("scoring_done request_id=%s trip_id=%s status=%s scoring_ms=%.1f",
                     request_id, trip_id, evaluation["status"], scoring_ms)
            result = replace(result, timings_ms=timings)
            return prediction_to_wire(
                request_id=request_id, result=result, model=model_identity(info), evaluation=evaluation,
                scoring_ms=scoring_ms, request_ms=(time.perf_counter() - started) * 1000,
            )
        finally:
            self._slots.release()
