"""Folium generator mechanics on a SYNTHETIC DevVisualisation document (no real data)."""
from __future__ import annotations

import pytest

from src.visualisation.folium.make_maps import build_map


def synthetic(partition="student_test"):
    return {
        "schema": "pathsnap-dev-vis/1", "partition": partition, "trip_id": "SYNTH0001", "run_id": "synthetic",
        "source_git_sha": "0" * 40, "model_version": "synthetic",
        "gps": [[0, 10.0, 50.0, 0.0], [1, 10.001, 50.0, 1.0]],
        "network": [{"arc_id": 0, "coordinates": [[10.0, 50.0], [10.001, 50.0]]}],
        "reference": {"arc_ids": [0], "pieces": [[[10.0, 50.0], [10.001, 50.0]]]},
        "predictions": {
            "classifier_only": {"pieces": [[[10.0, 50.0], [10.0005, 50.0]], [[10.0008, 50.0], [10.001, 50.0]]]},
            "hmm_viterbi": {"pieces": [[[10.0, 50.0], [10.001, 50.0]]]},
        },
    }


def test_map_has_all_layers_legend_and_no_bridging(tmp_path):
    html = build_map(synthetic()).get_root().render()
    for name in ["Raw GPS points", "Road network (nearby)", "Reference route (development data)",
                 "Predicted route (classifier + HMM)", "Predicted route (classifier only)"]:
        assert name in html
    assert "L.control.layers" in html
    # two classifier-only pieces stay two polylines (lat,lon order after conversion)
    assert html.count("[50.0, 10.0005]") == 1 and html.count("[50.0, 10.0008]") == 1


def test_evaluator_partition_refused():
    doc = synthetic()
    doc["partition"] = "evaluator_test"
    with pytest.raises(ValueError):
        build_map(doc)
