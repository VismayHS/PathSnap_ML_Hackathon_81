"""FastAPI app. Run on Laptop 1:  uvicorn api.main:app --host 0.0.0.0 --port 8000

Handlers are plain `def` so FastAPI runs CPU-bound prediction in its worker threadpool and
/health stays responsive; PathSnapService bounds concurrent predictions (429 when busy).
"""
from __future__ import annotations

import json
import logging
import re
import sys
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any, Optional

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

from src.contracts import CONTRACT_VERSION, PathSnapError

from .config import ApiConfig
from .service import PathSnapService

log = logging.getLogger("pathsnap.api")
_RID = re.compile(r"^[A-Za-z0-9-]{8,64}$")


def configure_logging() -> None:
    root = logging.getLogger("pathsnap")
    if not root.handlers:
        h = logging.StreamHandler(sys.stdout)
        h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
        root.addHandler(h)
        root.setLevel(logging.INFO)


class StrictJSONResponse(JSONResponse):
    """Refuse NaN/Infinity on the wire (contract rule) instead of emitting invalid JSON."""

    def render(self, content: Any) -> bytes:
        return json.dumps(content, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")


class PredictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    trip_id: str


def _error(request_id: str, status: int, code: str, message: str, retryable: bool) -> StrictJSONResponse:
    headers = {"X-Request-ID": request_id}
    if status in (429, 503):
        headers["Retry-After"] = "5"
    return StrictJSONResponse(
        status_code=status,
        content={"schema_version": CONTRACT_VERSION, "request_id": request_id,
                 "error": {"code": code, "message": message, "retryable": retryable}},
        headers=headers,
    )


def create_app(service: Optional[PathSnapService] = None) -> FastAPI:
    configure_logging()
    svc = service or PathSnapService(config=ApiConfig.from_env())

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        log.info("startup mode=%s data_root_configured=%s evaluator_root_configured=%s cors=%s",
                 svc.config.mode, svc.config.pipeline.data_root is not None,
                 svc.config.pipeline.evaluator_root is not None, list(svc.config.cors_origins))
        svc.start()
        yield

    app = FastAPI(title="PathSnap API", version=CONTRACT_VERSION, lifespan=lifespan,
                  default_response_class=StrictJSONResponse)
    app.state.service = svc
    app.add_middleware(
        CORSMiddleware, allow_origins=list(svc.config.cors_origins), allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-Request-ID"], expose_headers=["X-Request-ID", "Retry-After"],
    )

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        incoming = request.headers.get("X-Request-ID", "")
        rid = incoming if _RID.fullmatch(incoming) else uuid.uuid4().hex
        request.state.request_id = rid
        request.state.started = time.perf_counter()
        client = request.client.host if request.client else "-"
        try:
            response = await call_next(request)
        except Exception:  # noqa: BLE001 - last-resort safe envelope
            log.exception("unhandled request_id=%s", rid)
            response = _error(rid, 500, "internal_error", "Unexpected server error.", False)
        response.headers["X-Request-ID"] = rid
        log.info("request request_id=%s client=%s method=%s path=%s status=%d ms=%.1f", rid, client,
                 request.method, request.url.path, response.status_code,
                 (time.perf_counter() - request.state.started) * 1000)
        return response

    @app.exception_handler(PathSnapError)
    async def pathsnap_error(request: Request, exc: PathSnapError):
        log.warning("error request_id=%s code=%s message=%s detail=%s", request.state.request_id,
                    exc.code, exc.message, exc.detail)
        return _error(request.state.request_id, exc.http_status, exc.code, exc.message, exc.retryable)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        return _error(request.state.request_id, 422, "invalid_request",
                      'Send JSON exactly like {"trip_id": "00000000"}.', False)

    @app.get("/health")
    def health(request: Request):
        return {"schema_version": CONTRACT_VERSION, **svc.health()}

    @app.get("/trips")
    def trips(request: Request):
        return {"schema_version": CONTRACT_VERSION, **svc.trips()}

    @app.post("/predict")
    def predict(body: PredictRequest, request: Request):
        return svc.predict(body.trip_id, request.state.request_id, request.state.started)

    return app


def __getattr__(name: str):  # lazy `app` so importing api.main in tests has no side effects
    if name == "app":
        globals()["app"] = create_app()
        return globals()["app"]
    raise AttributeError(name)
