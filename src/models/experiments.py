"""Recorded training-only pilot and consistent five-model grouped experiments."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import time
import warnings
import joblib
import numpy as np
from threadpoolctl import threadpool_limits
from src.contracts import validate_trip_id_syntax
from src.models.estimators import CONFIGS, FAMILIES, OBJECTIVES, make_estimator
from src.evaluation.metrics import score_estimator, aggregate


def load_cache(cache):
    index = json.loads((cache/'index.json').read_text())
    sampling = json.loads((cache/'training-observation-sampling.json').read_text())
    trips = {}
    for record in index['records']:
        if record['partition'] not in ['train','student_test']:
            raise ValueError('Only permitted development partitions can enter training caches')
        validate_trip_id_syntax(record['trip_id'])
        path = cache/record['cache_path']
        expected = cache/record['partition']/f"{record['trip_id']}.npz"
        if path != expected or not path.resolve().is_relative_to(cache.resolve()):
            raise ValueError('Processed cache path escapes its registered trip')
        if hashlib.sha256(path.read_bytes()).hexdigest() != record['cache_sha256']:
            raise ValueError('Processed cache checksum mismatch')
        with np.load(path, allow_pickle=False) as data:
            trips[(record['partition'], record['trip_id'])] = {key: data[key] for key in data.files}
    return index, sampling, trips


def fit_arrays(trips, ids, sampling):
    X, y = [], []
    for tid in ids:
        data = trips[('train', tid)]
        keep = np.zeros(len(data['labels']), dtype=bool); keep[sampling[tid]] = True
        rows = keep[data['row_observation']]
        X.append(data['X'][rows]); y.append(data['y'][rows])
    return np.concatenate(X), np.concatenate(y)


def fit_model(name, trips, ids, sampling, params=None):
    X, y = fit_arrays(trips, ids, sampling)
    if len(np.unique(y)) != 2:
        raise ValueError('A candidate classifier requires both relevance classes')
    model = make_estimator(name, params)
    start = time.perf_counter()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always'); model.fit(X, y)
    return model, dict(fit_ms=(time.perf_counter()-start)*1000, fit_rows=len(y),
                      positive_rows=int(y.sum()), warnings=[str(w.message) for w in caught])


def evaluate_ids(model, partition, ids, trips, with_continuity=True):
    records = []
    for tid in ids:
        result = score_estimator(model, trips[(partition, tid)], with_continuity)
        result['trip_id'] = tid; records.append(result)
    return records


def fit_sample_evaluation(model, ids, trips, sampling):
    records = []
    for tid in ids:
        original = trips[('train', tid)]; data = dict(original)
        keep = np.zeros(len(data['labels']), bool); keep[sampling[tid]] = True
        rows = keep[data['row_observation']]
        for field in ['X', 'y', 'row_observation', 'candidate_arc_ids', 'fractions', 'distances']:
            data[field] = original[field][rows]
        data['offsets'] = np.r_[0, np.cumsum(np.bincount(data['row_observation'], minlength=len(keep))) ]
        data['scorable'] = original['scorable'] & keep
        result = score_estimator(model, data, with_continuity=False)
        result['trip_id'] = tid; records.append(result)
    return records


def metric_records(rows, meta, partition, fold, model_name, variant='untuned'):
    for row in rows:
        for name, value in row['values'].items():
            c = row['counts']
            denom = (c['candidate_covered'] if name == 'log_loss' else c.get('continuity_pairs')
                     if name == 'route_continuity' else c['road_classes'] if name in ['macro_f1','precision_macro','recall_macro']
                     else c['sequence_length'] if name == 'sequence_arc_similarity' else c['original_observations']
                     if name == 'scored_match_fraction_original' else c['scorable_observations'])
            yield dict(run_id=meta['run_id'], source_git_sha=meta['source_git_sha'],
                model_name=model_name, model_family=FAMILIES[model_name], variant=variant,
                decoder='classifier_only', partition=partition, fold=fold, trip_id=row['trip_id'],
                metric=name, value=value, denominator=denom, policy_id='pathsnap-scoring-v0',
                unavailable_reason=row['unavailable_reasons'].get(name) if value is None else None)


def run(cache, output, pilot=False):
    if output.exists():
        raise FileExistsError('Use a fresh experiment run directory')
    index, sampling, trips = load_cache(cache)
    output.mkdir(parents=True)
    meta = dict(run_id=output.name, source_git_sha=subprocess.check_output(['git','rev-parse','HEAD'], text=True).strip(),
        data_fingerprint=index['data_fingerprint'], config=index['config'],
        preparation_source_sha=index['source_git_sha'], config_sha256=index['config_sha256'],
        seed=index['config']['seed'], feature_names=index['feature_names'], folds=index['folds'],
        candidate_policy=index['config']['candidate_policy'], pilot=pilot,
        dependencies={p: importlib.metadata.version(p) for p in ['numpy','scipy','scikit-learn','joblib']},
        metric_policy='pathsnap-scoring-v0; observation accuracy pooled across scorable rows, Macro F1 arithmetic mean of trip-local road-class Macro F1; candidate misses retained; log loss conditional on covered observations',
        timing_policy='candidate_scoring_ms includes saved preprocessing, model scores and per-observation normalization/selection; excludes cached feature preparation and reference metrics',
        training_scope='at most 400 scorable observations per training trip; validation/student testing unsampled')
    (output/'metadata.json').write_text(json.dumps(meta, indent=2)+'\n')
    summaries = []; started = time.perf_counter()
    with (output/'records.jsonl').open('w') as stream:
        for name in CONFIGS:
            begin = time.perf_counter()
            try:
                if pilot:
                    fold = index['folds'][0]
                    fit_ids = fold['train'][:index['config']['pilot']['train_trips']]
                    valid_ids = fold['validation'][:index['config']['pilot']['validation_trips']]
                    model, fitting = fit_model(name, trips, fit_ids, sampling)
                    records = evaluate_ids(model, 'train', valid_ids, trips, with_continuity=False)
                    summary = dict(model_name=name, family=FAMILIES[name], objective=OBJECTIVES[name],
                        configuration=CONFIGS[name], pilot_train_trips=fit_ids, pilot_validation_trips=valid_ids,
                        fit=fitting, validation=aggregate(records), per_trip=records, status='complete',
                        elapsed_s=time.perf_counter()-begin)
                else:
                    folds, validation = [], []
                    for fold in index['folds']:
                        model, fitting = fit_model(name, trips, fold['train'], sampling)
                        rows = evaluate_ids(model, 'train', fold['validation'], trips)
                        validation += rows
                        folds.append(dict(fold=fold['fold'], fit=fitting, aggregate=aggregate(rows), trips=rows))
                        for row in metric_records(rows, meta, 'train_cv', fold['fold'], name):
                            stream.write(json.dumps(row, allow_nan=False)+'\n')
                        stream.flush()
                        print(json.dumps({'model':name,'fold':fold['fold'],'macro_f1':folds[-1]['aggregate']['macro_f1'],**fitting}),flush=True)
                    ids = sorted(sampling)
                    model, fitting = fit_model(name, trips, ids, sampling)
                    training = fit_sample_evaluation(model, ids, trips, sampling)
                    testing = evaluate_ids(model, 'student_test', index['student_test_ids'], trips)
                    destination = output/'models'; destination.mkdir(exist_ok=True)
                    joblib.dump(model, destination/f'{name}.joblib', compress=3)
                    for row in metric_records(testing, meta, 'student_test', None, name):
                        stream.write(json.dumps(row, allow_nan=False)+'\n')
                    stream.flush()
                    summary = dict(model_name=name, family=FAMILIES[name], objective=OBJECTIVES[name],
                        configuration=CONFIGS[name], folds=folds, cv=aggregate(validation),
                        cv_macro_f1_std=float(np.std([f['aggregate']['macro_f1'] for f in folds])),
                        refit=fitting, fit_sample=aggregate(training), fit_sample_scope='only sampled fit observations, not all original rows',
                        student_test=aggregate(testing), student_per_trip=testing, status='complete',
                        elapsed_s=time.perf_counter()-begin)
                summaries.append(summary)
                (output/f'{name}.json').write_text(json.dumps(summary, indent=2, allow_nan=False)+'\n')
                print(json.dumps({'model':name,'status':'complete','elapsed_s':summary['elapsed_s'],
                                  'pilot':pilot,'headline':summary.get('cv',summary.get('validation'))}),flush=True)
            except Exception as exc:
                failure=dict(model_name=name,status='failed',error=repr(exc),elapsed_s=time.perf_counter()-begin)
                summaries.append(failure);(output/f'{name}.failure.json').write_text(json.dumps(failure,indent=2)+'\n')
                print(json.dumps(failure),flush=True)
    result = dict(**meta, results=summaries, elapsed_s=time.perf_counter()-started)
    if not pilot and all(r['status']=='complete' for r in summaries):
        result['cv_f1_leader'] = max(summaries,key=lambda r:r['cv']['macro_f1'])['model_name']
    (output/'summary.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    if any(r['status'] != 'complete' for r in summaries):
        raise SystemExit('One or more model attempts failed; preserved failure records must be reviewed')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--pilot', action='store_true')
    args = parser.parse_args()
    with threadpool_limits(limits=2):
        run(args.cache, args.output, args.pilot)


if __name__ == '__main__':
    main()
