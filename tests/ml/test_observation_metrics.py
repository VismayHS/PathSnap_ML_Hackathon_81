import numpy as np
import pytest
from src.evaluation.metrics import observation_metrics, sequence_similarity


def test_candidate_misses_and_unmatched_stay_in_accuracy():
    result = observation_metrics(np.array([1, 2, 2]), np.ones(3, bool), np.array([1, -1, 9]),
        np.array([1, 3, 9, 2]), np.array([0, 1, 2, 2]), np.array([1., 1., .9, .1]))
    assert result['values']['top1_accuracy'] == pytest.approx(1/3)
    assert result['values']['macro_f1'] == pytest.approx(1/3)
    assert result['values']['candidate_miss_rate'] == pytest.approx(1/3)
    assert result['values']['log_loss'] == pytest.approx(-np.log(.1)/2)
    assert result['counts']['candidate_covered'] == 2


def test_unscorable_accounting_and_no_covered_loss():
    result = observation_metrics(np.array([1, 2]), np.array([True, False]), np.array([-1, 2]),
                                 np.array([3, 2]), np.array([0, 1]), np.array([1., 1.]))
    assert result['values']['top1_accuracy'] == 0
    assert result['values']['macro_f1'] == 0
    assert result['values']['log_loss'] is None
    assert result['counts']['unscorable_observations'] == 1


def test_ordered_sequence_similarity_preserves_nonconsecutive_repeats():
    assert sequence_similarity([1, 1, 2, 1], [1, 1])[0] == pytest.approx(1/3)
    assert sequence_similarity([1, 2, 1], [1, 2, 1])[0] == 1
