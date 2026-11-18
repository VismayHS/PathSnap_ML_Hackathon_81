"""Provisional development/scoring target alignment, isolated from inference.

States are ordered reference traversal occurrences (not unique arc IDs). The
monotone dynamic program minimizes robust geometric and directional residuals;
forward skips allow arcs traversed between GPS samples. Endpoints are free.
This is a derived-label policy, not an organizer-certified pointwise ground truth.
"""
from dataclasses import dataclass
import numpy as np
from src.features.candidate import motion

POLICY_ID = 'pathsnap-scoring-v0'


@dataclass
class Alignment:
    arc_ids: np.ndarray
    occurrences: np.ndarray
    residuals_m: np.ndarray
    scorable: np.ndarray
    low_margin: np.ndarray


def align_reference(trip, geometry, reference, residual_limit_m=100.):
    n, m = len(trip.track), len(reference)
    if not m:
        raise ValueError("Reference traversal is empty")
    u = geometry.start[reference]; d = geometry.delta[reference]
    lengths = geometry.length[reference]
    valid_arcs = np.isfinite(lengths) & (lengths > 0)
    if not valid_arcs.all():
        raise ValueError("Reference includes non-geometric or zero-length arc; alignment unavailable")
    indices = np.flatnonzero(trip.valid)
    arcs = np.full(n, -1, dtype=int); occurrence = np.full(n, -1, dtype=int)
    residuals = np.full(n, np.nan); margins = np.zeros(n, dtype=bool)
    if not len(indices):
        return Alignment(arcs, occurrence, residuals, trip.valid.copy(), margins)
    directions, _, _, heading_valid = motion(trip, geometry)
    back = np.empty((len(indices), m), dtype=np.int32)
    costs = np.zeros(m)
    orient = d/lengths[:, None]
    for row, i in enumerate(indices):
        fraction = np.clip(np.sum((geometry.xy[i]-u)*d, axis=1)/lengths**2, 0, 1)
        distances = np.linalg.norm(geometry.xy[i]-u-fraction[:, None]*d, axis=1)
        # Capping prevents one extreme outlier dominating the whole trajectory.
        emission = (np.minimum(distances, residual_limit_m)/20.)**2
        if heading_valid[i]:
            emission += 2.*(1.-np.clip(orient @ directions[i], -1, 1))
        prefix = np.minimum.accumulate(costs)
        predecessors = np.maximum.accumulate(np.where(costs <= prefix, np.arange(m), 0))
        back[row] = predecessors
        costs = prefix+emission
        costs -= costs.min()
        # Distance ambiguity is a diagnostic, not hidden filtering of hard examples.
        unique = {}
        for arc_id, distance in zip(reference, distances):
            unique[arc_id] = min(unique.get(arc_id, np.inf), float(distance))
        best = sorted(unique.values())[:2]
        margins[i] = len(best) > 1 and best[1]-best[0] < 3
    state = int(np.argmin(costs))
    for row in range(len(indices)-1, -1, -1):
        i = indices[row]; occurrence[i] = state; arcs[i] = reference[state]
        fraction = np.clip(np.dot(geometry.xy[i]-u[state], d[state])/lengths[state]**2, 0, 1)
        residuals[i] = np.linalg.norm(geometry.xy[i]-u[state]-fraction*d[state])
        state = int(back[row, state])
    scorable = trip.valid & np.isfinite(residuals) & (residuals <= residual_limit_m)
    return Alignment(arcs, occurrence, residuals, scorable, margins)
