"""B's independent startup check of A's artifact manifest (schema + checksums + contract)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import jsonschema

from src.contracts import CONTRACT_VERSION, Mode

_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "contracts" / "artifacts.schema.json"


def check_bundle(bundle_root: Path, mode: Mode) -> list[str]:
    """Return safe, path-free problem codes; empty list means the bundle looks usable."""
    manifest_path = bundle_root / "manifest.json"
    if not manifest_path.is_file():
        return ["bundle_manifest_missing"]
    try:
        manifest = json.loads(manifest_path.read_text("utf-8"))
    except (OSError, ValueError):
        return ["bundle_manifest_unreadable"]
    schema = json.loads(_SCHEMA_PATH.read_text("utf-8"))
    validator = jsonschema.Draft202012Validator({**schema, "$ref": "#/$defs/BundleManifest"})
    if not validator.is_valid(manifest):
        return ["bundle_manifest_schema_invalid"]
    problems: list[str] = []
    if manifest["contract_version"].split(".")[0] != CONTRACT_VERSION.split(".")[0]:
        problems.append("bundle_contract_version_incompatible")
    if manifest["model_kind"] == "diagnostic" and mode == "evaluator":
        problems.append("diagnostic_bundle_not_allowed_in_evaluator_mode")
    root = bundle_root.resolve()
    for entry in manifest["files"]:
        target = (root / entry["path"]).resolve()
        if root not in target.parents:
            problems.append("bundle_file_path_escapes_root")
            continue
        if not target.is_file():
            problems.append(f"bundle_file_missing:{entry['role']}")
            continue
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        if digest != entry["sha256"]:
            problems.append(f"bundle_checksum_mismatch:{entry['role']}")
    return problems


def manifest_sha256(bundle_root: Path) -> str:
    return hashlib.sha256((bundle_root / "manifest.json").read_bytes()).hexdigest()
