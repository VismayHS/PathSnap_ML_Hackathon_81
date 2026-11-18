from types import SimpleNamespace
import numpy as np
import pytest
from src.hmm.graph import RoadGraph
from src.hmm.viterbi import decode, normalized_scores
from src.data_processing.candidates import Candidates, empty_candidates


def candidate(ids, fractions):
    return Candidates(np.array(ids), np.zeros(len(ids)), np.array(fractions), np.zeros((len(ids), 2)))


def test_directed_partials_cycle_and_zero_length_connectors():
    graph = RoadGraph(np.array([[0, 1], [1, 2], [2, 0], [2, 3]]), np.array([100., 100., 100., 0.]))
    distance, path = graph.between(0, .8, 1, .2, 100)
    assert distance == pytest.approx(40)
    assert path == ()
    # Reversed progress beyond noise must traverse a directed loop.
    distance, path = graph.between(0, .8, 0, .2, 1000)
    assert distance == pytest.approx(240)
    assert path == (1, 2)
    assert graph.shortest(2, 3, 0) == (0., (3,))
    assert np.isinf(graph.shortest(3, 0, 1000)[0])


def test_viterbi_known_optimum_and_unreachable_restart():
    arcs = np.array([[0, 1], [1, 2], [3, 4]])
    graph = RoadGraph(arcs, np.array([100., 100., 100.]))
    trip = SimpleNamespace(track=np.array([[0, 0, 0], [0, 0, 1], [0, 0, 2]], dtype=float))
    geometry = SimpleNamespace(xy=np.array([[0, 0], [40, 0], [60, 0]], dtype=float))
    cs = [candidate([0, 2], [.8, .8]), candidate([1], [.2]), candidate([2], [.5])]
    # Initial classifier prefers disconnected arc 2, but the known feasible path is 0 -> 1.
    result = decode(trip, geometry, cs, [np.array([.4, .6]), np.array([1.]), np.array([1.])], graph)
    assert result.choices.tolist() == [0, 0, 0]
    assert result.segments.tolist() == [0, 0, 1]
    assert result.breaks == [(2, 'unreachable')]


def test_empty_and_long_gap_reset_and_score_edges():
    graph = RoadGraph(np.array([[0, 1]]), np.array([100.]))
    trip = SimpleNamespace(track=np.array([[0, 0, 0], [0, 0, 1], [0, 0, 60.]]))
    geometry = SimpleNamespace(xy=np.zeros((3, 2)))
    cs = [candidate([0], [.2]), empty_candidates(), candidate([0], [.3])]
    result = decode(trip, geometry, cs, [[1], [], [1]], graph)
    assert result.choices.tolist() == [0, -1, 0]
    assert result.segments.tolist() == [0, -1, 1]
    assert normalized_scores([0., 0.]).tolist() == [.5, .5]
    with pytest.raises(ValueError):
        normalized_scores([np.nan])
    cs[1] = candidate([0], [.2])
    result = decode(trip, geometry, cs, [[1], [1], [1]], graph)
    assert result.breaks == [(2, 'gps_gap')]


def test_same_arc_forward_travel_respects_physical_bound():
    graph = RoadGraph(np.array([[0, 1]]), np.array([1000.]))
    assert np.isinf(graph.between(0, .1, 0, .9, 115)[0])
    assert graph.between(0, .1, 0, .2, 115)[0] == pytest.approx(100)
