import json
from pathlib import Path
import numpy as np
import pytest
from src.contracts import (PipelineSettings, PredictOptions, InvalidTripIdError,
    DataNotConfiguredError, ModelNotReadyError, check_prediction_invariants)
from src.models.export import export_bundle
from src.pipeline import load_model_bundle, load_prediction_input, list_trip_ids, predict_trip


def fixture_settings(tmp_path):
    root = tmp_path/'data'
    p = root/'student_test'/'00000007'
    p.mkdir(parents=True)
    (p/'00000007.track').write_text('10 50 1\n10.0005 50 2\nnan 50 3\n10.0008 50 50\n')
    (p/'00000007.nodes').write_text('10 50\n10.001 50\n')
    (p/'00000007.arcs').write_text('0 1\n1 0\n')
    settings = PipelineSettings(root, tmp_path/'bundle')
    export_bundle(settings.bundle_root)
    return settings


def test_real_facade_without_any_reference_file_and_no_bridge(tmp_path):
    settings = fixture_settings(tmp_path)
    assert list_trip_ids('development', settings) == ['00000007']
    with pytest.raises(DataNotConfiguredError):
        list_trip_ids('evaluator', settings)
    with pytest.raises(InvalidTripIdError):
        load_prediction_input('../bad', 'development', settings)
    data = load_prediction_input('00000007', 'development', settings)
    result = predict_trip(data, load_model_bundle(settings), PredictOptions())
    assert not check_prediction_invariants(result)
    assert result.observation_count == 4
    assert result.observations[2].index == 2
    assert result.observations[2].status == 'invalid'
    assert result.observations[2].lon is None
    assert len(result.route) == 2
    assert result.model_kind == 'diagnostic'
    assert result.score_kind == 'normalized_score'
    assert result.scorer_evidence['candidates']
    assert all(arc.arc_id in (0, 1) for piece in result.route for arc in piece.arcs)


def test_artifact_integrity_and_feature_order(tmp_path):
    settings = fixture_settings(tmp_path)
    path = settings.bundle_root/'feature-schema.json'
    path.write_text('{}')
    with pytest.raises(ModelNotReadyError):
        load_model_bundle(settings)


def test_diagnostic_cannot_run_in_evaluator_mode(tmp_path):
    from dataclasses import replace
    settings = fixture_settings(tmp_path)
    data = replace(load_prediction_input('00000007', 'development', settings), mode='evaluator')
    with pytest.raises(ModelNotReadyError):
        predict_trip(data, load_model_bundle(settings), PredictOptions())
