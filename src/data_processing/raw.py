"""Strict reference-free parsing with original row IDs and explicit cleaning masks."""
from dataclasses import dataclass
from pathlib import Path
import numpy as np


@dataclass
class RawTrip:
    trip_id: str
    partition: str
    track: np.ndarray
    nodes: np.ndarray
    arcs: np.ndarray
    valid: np.ndarray
    reasons: tuple[str | None, ...]


def table(path: Path, columns: int) -> np.ndarray:
    values = np.loadtxt(path, ndmin=2)
    if not len(values) or values.shape[1] != columns:
        raise ValueError(f"Expected nonempty {columns}-column {path.suffix} table")
    return values


def valid_coordinates(coords: np.ndarray) -> np.ndarray:
    return (np.isfinite(coords).all(axis=1) & (abs(coords[:, 0]) <= 180)
            & (abs(coords[:, 1]) <= 90))


def clean_mask(track: np.ndarray) -> tuple[np.ndarray, tuple[str | None, ...]]:
    good = valid_coordinates(track[:, :2]) & np.isfinite(track[:, 2])
    reasons = [None if ok else "invalid_coordinate_or_time" for ok in good]
    previous = -np.inf
    for i, row in enumerate(track):
        if not good[i]:
            continue
        if row[2] <= previous:
            good[i] = False
            reasons[i] = "nonincreasing_timestamp"
        else:
            previous = row[2]
    return good, tuple(reasons)


def load_raw_trip(directory: Path, partition: str) -> RawTrip:
    """Read exactly three prediction files; no reference route lookup."""
    tid = directory.name
    track = table(directory / f"{tid}.track", 3)
    nodes = table(directory / f"{tid}.nodes", 2)
    arcs = table(directory / f"{tid}.arcs", 2)
    if not np.isfinite(arcs).all() or not np.equal(arcs, np.floor(arcs)).all():
        raise ValueError("Arc endpoints must be finite integers")
    if (arcs < 0).any() or (arcs >= len(nodes)).any():
        raise ValueError("Arc endpoint outside original node row range")
    mask, reasons = clean_mask(track)
    return RawTrip(tid, partition, track, nodes, arcs.astype(np.int64), mask, reasons)
