"""Portable runtime configuration, read from environment variables only."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from src.contracts import Mode, PipelineSettings

REPO_ROOT = Path(__file__).resolve().parent.parent


def _path(name: str, default: Optional[Path]) -> Optional[Path]:
    raw = os.environ.get(name)
    if raw:
        return Path(raw).expanduser().resolve()
    return default


@dataclass(frozen=True)
class ApiConfig:
    mode: Mode
    pipeline: PipelineSettings
    cors_origins: tuple[str, ...]
    max_concurrent_predictions: int = 1

    @staticmethod
    def from_env() -> "ApiConfig":
        mode = os.environ.get("PATHSNAP_MODE", "development")
        if mode not in ("development", "evaluator"):
            raise SystemExit(f"PATHSNAP_MODE must be 'development' or 'evaluator', got {mode!r}")
        # Default only works from the original checkout (sibling Student_folder). Worktrees
        # sit one level deeper, so a missing default is a hard error instead of a silent miss.
        default_root = (REPO_ROOT.parent / "Student_folder").resolve()
        data_root = _path("PATHSNAP_DATA_ROOT", default_root if default_root.is_dir() else None)
        if data_root is None:
            raise SystemExit(
                "PATHSNAP_DATA_ROOT is not set and ../Student_folder does not exist. "
                "Set PATHSNAP_DATA_ROOT to the absolute path of the dataset folder."
            )
        bundle_root = _path("PATHSNAP_BUNDLE_ROOT", REPO_ROOT / "artifacts" / "final")
        evaluator_root = _path("PATHSNAP_EVALUATOR_ROOT", None)
        origins = tuple(
            o.strip()
            for o in os.environ.get(
                "PATHSNAP_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173"
            ).split(",")
            if o.strip()
        )
        return ApiConfig(
            mode=mode,  # type: ignore[arg-type]
            pipeline=PipelineSettings(data_root=data_root, bundle_root=bundle_root, evaluator_root=evaluator_root),
            cors_origins=origins,
            max_concurrent_predictions=max(1, int(os.environ.get("PATHSNAP_MAX_CONCURRENT", "1"))),
        )
