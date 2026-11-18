"""Real-data M1 checks; explicitly diagnostic, never a trained benchmark."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
from unittest.mock import patch
from src.contracts import PipelineSettings, PredictOptions, ScoringSettings, check_prediction_invariants
from src.pipeline import list_trip_ids, load_model_bundle, load_prediction_input, predict_trip
from src.evaluation.service import evaluate_completed_prediction


def run(settings, output):
    if output.exists():
        raise FileExistsError('Use a new immutable diagnostic evidence directory')
    output.mkdir(parents=True)
    start = time.perf_counter(); bundle = load_model_bundle(settings)
    load_ms = (time.perf_counter()-start)*1000
    if bundle.info.model_kind != 'diagnostic':
        raise ValueError('This check is solely for M1 diagnostic mode')
    rows = []
    original_open = Path.open
    def guarded_open(path, *args, **kwargs):
        if path.suffix == '.route':
            raise AssertionError('Diagnostic prediction attempted reference access')
        return original_open(path, *args, **kwargs)
    for tid in list_trip_ids('development', settings):
        with patch.object(Path, 'open', guarded_open):
            result = predict_trip(load_prediction_input(tid, 'development', settings), bundle, PredictOptions())
            evaluation = evaluate_completed_prediction(result, ScoringSettings(settings, 'development'))
        violations = check_prediction_invariants(result)
        if violations:
            raise AssertionError(violations)
        assert evaluation.status == 'unavailable'
        assert result.model_kind == 'diagnostic'
        signature = [(o.index, o.status, o.arc_id, o.segment_id) for o in result.observations]
        rows.append(dict(trip_id=tid, observation_count=result.observation_count,
                         statuses=dict(Counter(o.status for o in result.observations)),
                         route_pieces=len(result.route), network_context_segments=len(result.network_context),
                         warning_counts=dict(Counter(w.code for w in result.warnings)),
                         timings_ms=result.timings_ms, scoring_status=evaluation.status,
                         signature_sha256=hashlib.sha256(json.dumps(signature).encode()).hexdigest()))
        print(json.dumps(rows[-1]), flush=True)
    # Actual CLI invocation, same selected-arc/status/segment signature as the core.
    cli_output = Path('data/processed') / f'{output.name}-cli.json'
    command = [sys.executable, '-m', 'src.pipeline', '--data-root', str(settings.data_root),
               '--bundle-root', str(settings.bundle_root), '--trip', rows[0]['trip_id'], '--output', str(cli_output)]
    subprocess.run(command, check=True, capture_output=True, text=True)
    cli = json.loads(cli_output.read_text())
    signature = [(o['index'], o['status'], o['arc_id'], o['segment_id']) for o in cli['observations']]
    assert hashlib.sha256(json.dumps(signature).encode()).hexdigest() == rows[0]['signature_sha256']
    report = dict(schema_version=1, run_id=output.name,
                  source_git_sha=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
                  model_kind='diagnostic', trained_models_evaluated=0, benchmark_metrics_available=False,
                  startup_load_ms=load_ms, manifest_sha256=bundle.info.manifest_sha256,
                  checks=dict(contract_invariants='passed for all listed development trips',
                              reference_guard='Path.open .route access rejected during prediction/scoring',
                              cli_core_signature_parity='passed on first listed trip',
                              reserved_evaluator='not provisioned, not inspected',
                              actual_api_ui_lan='not tested by this command'), trips=rows)
    (output/'summary.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root', type=Path, required=True)
    parser.add_argument('--bundle-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(PipelineSettings(args.data_root, args.bundle_root), args.output)


if __name__ == '__main__':
    main()
