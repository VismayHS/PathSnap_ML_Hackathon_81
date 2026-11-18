"""Stable log-space Viterbi with explicit invalid, gap and unreachable restarts.

This file is the HMM (Hidden Markov Model) decoder. It takes, for every GPS point,
the candidate roads and the classifier's score for each of them, and chooses ONE
road per point so that the whole route is drivable on the road network.

  - Hidden state  = which candidate road the car is on at a GPS point.
  - Emission      = how well that road fits the GPS point (the classifier's score).
  - Transition    = how believable it is to drive from the previous road to this one,
                    comparing driving distance on the network with how far the GPS moved.
  - Viterbi       = dynamic programming that finds the best-scoring sequence of roads.
"""
from dataclasses import dataclass
import numpy as np

# Fixed decoder settings, chosen before testing (never tuned on test trips):
#   gap_s                          a time gap longer than this (seconds) starts a new route piece
#   max_speed_mps                  fastest believable speed (65 m/s); farther moves are impossible
#   transition_scale_m             how strongly distance disagreement is penalised (per 25 m)
#   gps_slack_m                    extra allowance (metres) for GPS noise on top of the speed limit
#   stationary_projection_noise_m  small backward jitter on the same road counts as standing still
DEFAULT_CONFIG = dict(gap_s=30., max_speed_mps=65., transition_scale_m=25.,
                      gps_slack_m=50., stationary_projection_noise_m=15.)


@dataclass
class Decoded:
    """The decoder's answer for one trip.

    choices[i]  index of the chosen candidate road for GPS point i (-1 = no road chosen)
    segments[i] which route piece point i belongs to (a new piece starts after every break)
    breaks      list of (point index, reason) where the route had to restart:
                'gps_gap' (time gap too long) or 'unreachable' (no drivable connection)
    """
    choices: np.ndarray
    segments: np.ndarray
    breaks: list[tuple[int, str]]


def normalized_scores(raw):
    """Normalize binary relevance estimates; these are not calibrated road probabilities.

    Turns the classifier's scores for one GPS point's candidates into numbers that
    add up to 1, so they can be used as emission scores. Rejects negative or broken
    values, and replaces exact zeros with a tiny number so that log() never fails.
    """
    values = np.asarray(raw, dtype=float)
    if not len(values):
        return values
    if not np.isfinite(values).all() or (values < 0).any():
        raise ValueError("Relevance scores must be finite and nonnegative")
    values = np.maximum(values, 1e-12)
    return values / values.sum()


def decode(trip, geometry, candidates, probabilities, graph, config=None):
    """Run HMM + Viterbi over one trip and return the chosen road for every GPS point.

    Inputs:
      trip           the raw trip (GPS track with timestamps)
      geometry       GPS points converted to metres (geometry.xy)
      candidates     for each GPS point: its candidate road IDs and positions along them
      probabilities  for each GPS point: the classifier's score for each candidate
      graph          the directed road network (RoadGraph), used for driving distances
      config         optional overrides of DEFAULT_CONFIG

    Walks forward through the GPS points one at a time. At each point it keeps, for
    every candidate road, the best total score of any route ending on that road and a
    back-pointer to the road it came from. When the trip ends or must break (gap, no
    candidates, nothing reachable), it traces the back-pointers to recover the route.
    """
    cfg = {**DEFAULT_CONFIG, **(config or {})}
    count = len(candidates)
    choices = np.full(count, -1, dtype=int); segments = np.full(count, -1, dtype=int)
    breaks = []
    # indices: GPS points in the current route piece; backs: their back-pointers;
    # previous: best score so far for each candidate road at the last point.
    indices, backs, previous = [], [], None
    segment = -1

    def finish():
        """Trace back the current route piece and write its chosen roads.

        Starts from the best-scoring road at the last point of the piece, then follows
        the back-pointers backwards to the first point, recording each chosen road.
        """
        if not indices:
            return
        state = int(np.argmax(previous))
        for i, back in zip(reversed(indices), reversed(backs)):
            choices[i] = state; segments[i] = segment
            state = int(back[state])

    for i, c in enumerate(candidates):
        # No candidate road within 100 m: close the current piece and skip this point.
        if not len(c.arc_ids):
            finish(); indices, backs, previous = [], [], None
            continue
        # EMISSION: log of the classifier's normalised scores for this point's candidates.
        emission = np.log(normalized_scores(probabilities[i]))
        restart = None
        if indices:
            j = indices[-1]
            dt = trip.track[i, 2]-trip.track[j, 2]
            # GAP CHECK: skipped points or a time gap over 30 s break the route.
            if i != j+1 or not 0 < dt <= cfg['gap_s']:
                restart = 'gps_gap'
            else:
                pc = candidates[j]
                # How far the GPS moved (straight line, metres) and the farthest a car could drive.
                displacement = float(np.linalg.norm(geometry.xy[i]-geometry.xy[j]))
                limit = cfg['max_speed_mps']*dt + cfg['gps_slack_m']
                # TRANSITION: score every (previous road a -> current road b) move.
                # -inf means impossible (not connected, or too far to drive in the time).
                transition = np.full((len(pc.arc_ids), len(c.arc_ids)), -np.inf)
                for a, (aid, af) in enumerate(zip(pc.arc_ids, pc.fractions)):
                    for b, (bid, bf) in enumerate(zip(c.arc_ids, c.fractions)):
                        dist, _ = graph.between(aid, af, bid, bf, limit,
                                                cfg['stationary_projection_noise_m'])
                        if np.isfinite(dist):
                            # Best when driving distance matches GPS distance; worse the more they differ.
                            transition[a, b] = -abs(dist-displacement)/cfg['transition_scale_m']
                # VITERBI STEP: best previous score + transition, for every current road.
                lattice = previous[:, None] + transition
                if not np.isfinite(lattice).any():
                    # No current road can be reached from any previous road.
                    restart = 'unreachable'
                else:
                    back = np.argmax(lattice, axis=0)  # best previous road for each current road
                    current = lattice[back, np.arange(len(c.arc_ids))] + emission
        if restart:
            # Close the current piece and start a new one at this point.
            finish(); indices, backs, previous = [], [], None
            breaks.append((i, restart))
        if not indices:
            # First point of a new route piece: only the emission score counts.
            segment += 1
            current = emission.copy()
            back = np.full(len(c.arc_ids), -1, dtype=int)
        # Subtract a common offset to bound accumulation without altering the optimum.
        previous = current - np.max(current)
        indices.append(i); backs.append(back)
    finish()  # trace back the last piece
    return Decoded(choices, segments, breaks)
