"""Stable log-space Viterbi with explicit invalid, gap and unreachable restarts."""
from dataclasses import dataclass
import numpy as np

DEFAULT_CONFIG = dict(gap_s=30., max_speed_mps=65., transition_scale_m=25.,
                      gps_slack_m=50., stationary_projection_noise_m=15.)


@dataclass
class Decoded:
    choices: np.ndarray
    segments: np.ndarray
    breaks: list[tuple[int, str]]


def normalized_scores(raw):
    """Normalize binary relevance estimates; these are not calibrated road probabilities."""
    values = np.asarray(raw, dtype=float)
    if not len(values):
        return values
    if not np.isfinite(values).all() or (values < 0).any():
        raise ValueError("Relevance scores must be finite and nonnegative")
    values = np.maximum(values, 1e-12)
    return values / values.sum()


def decode(trip, geometry, candidates, probabilities, graph, config=None):
    cfg = {**DEFAULT_CONFIG, **(config or {})}
    count = len(candidates)
    choices = np.full(count, -1, dtype=int); segments = np.full(count, -1, dtype=int)
    breaks = []
    indices, backs, previous = [], [], None
    segment = -1

    def finish():
        if not indices:
            return
        state = int(np.argmax(previous))
        for i, back in zip(reversed(indices), reversed(backs)):
            choices[i] = state; segments[i] = segment
            state = int(back[state])

    for i, c in enumerate(candidates):
        if not len(c.arc_ids):
            finish(); indices, backs, previous = [], [], None
            continue
        emission = np.log(normalized_scores(probabilities[i]))
        restart = None
        if indices:
            j = indices[-1]
            dt = trip.track[i, 2]-trip.track[j, 2]
            if i != j+1 or not 0 < dt <= cfg['gap_s']:
                restart = 'gps_gap'
            else:
                pc = candidates[j]
                displacement = float(np.linalg.norm(geometry.xy[i]-geometry.xy[j]))
                limit = cfg['max_speed_mps']*dt + cfg['gps_slack_m']
                transition = np.full((len(pc.arc_ids), len(c.arc_ids)), -np.inf)
                for a, (aid, af) in enumerate(zip(pc.arc_ids, pc.fractions)):
                    for b, (bid, bf) in enumerate(zip(c.arc_ids, c.fractions)):
                        dist, _ = graph.between(aid, af, bid, bf, limit,
                                                cfg['stationary_projection_noise_m'])
                        if np.isfinite(dist):
                            transition[a, b] = -abs(dist-displacement)/cfg['transition_scale_m']
                lattice = previous[:, None] + transition
                if not np.isfinite(lattice).any():
                    restart = 'unreachable'
                else:
                    back = np.argmax(lattice, axis=0)
                    current = lattice[back, np.arange(len(c.arc_ids))] + emission
        if restart:
            finish(); indices, backs, previous = [], [], None
            breaks.append((i, restart))
        if not indices:
            segment += 1
            current = emission.copy()
            back = np.full(len(c.arc_ids), -1, dtype=int)
        # Subtract a common offset to bound accumulation without altering the optimum.
        previous = current - np.max(current)
        indices.append(i); backs.append(back)
    finish()
    return Decoded(choices, segments, breaks)
