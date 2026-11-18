"""Create reproducible shared-input fingerprints and balanced four-laptop task queues."""
import argparse
import json
import importlib.metadata
from pathlib import Path
from src.models.experiments import load_cache, fit_arrays
from src.models.estimators import CONFIGS
from src.models.provenance import cache_identity, digest_json


def build(cache, pilot_path, output, baseline_path=None):
    index, sampling, trips = load_cache(cache)
    identity = cache_identity(index,sampling,trips)
    pilot = json.loads(pilot_path.read_text())
    profiles = {r['model_name']:r for r in pilot['results'] if r['status']=='complete'}
    baseline=json.loads(baseline_path.read_text()) if baseline_path else None
    measured={r['model_name']:r for r in baseline['results']} if baseline else {}
    tasks = []
    for name in CONFIGS:
        p = profiles[name]; pilot_rows = p['fit']['fit_rows']
        validation_ids = p['pilot_validation_trips']
        pilot_query_rows = sum(len(trips[('train',tid)]['X']) for tid in validation_ids)
        for fold in index['folds']:
            fit_rows = len(fit_arrays(trips,fold['train'],sampling)[1])
            query_rows = sum(len(trips[('train',tid)]['X']) for tid in fold['validation'])
            estimate = p['fit']['fit_ms']*fit_rows/pilot_rows + p['validation']['candidate_scoring_ms']*query_rows/pilot_query_rows
            if name in measured:
                recorded=next(f for f in measured[name]['folds'] if f['fold']==fold['fold'])
                estimate=recorded['fit']['fit_ms']+sum(t['candidate_scoring_ms']+t['metric_elapsed_ms'] for t in recorded['trips'])
            tasks.append(dict(task_id=f'{name}-cv-{fold["fold"]}',model=name,kind='cv',fold=fold['fold'],estimated_work_ms=estimate))
        fit_rows = len(fit_arrays(trips,sorted(sampling),sampling)[1])
        query_rows = sum(len(trips[('student_test',tid)]['X']) for tid in index['student_test_ids'])+fit_rows
        estimate = p['fit']['fit_ms']*fit_rows/pilot_rows + p['validation']['candidate_scoring_ms']*query_rows/pilot_query_rows
        if name in measured:
            cv_cost=sum(f['fit']['fit_ms']+sum(t['candidate_scoring_ms']+t['metric_elapsed_ms'] for t in f['trips']) for f in measured[name]['folds'])
            estimate=max(1.,measured[name]['elapsed_s']*1000-cv_cost)
        tasks.append(dict(task_id=f'{name}-refit',model=name,kind='refit',fold=None,estimated_work_ms=estimate))
    loads = {f'laptop-{i}':0. for i in range(1,5)}
    for task in sorted(tasks,key=lambda t:(-t['estimated_work_ms'],t['task_id'])):
        owner = min(loads,key=lambda k:(loads[k],k));task['laptop']=owner;loads[owner]+=task['estimated_work_ms']
    manifest = dict(schema_version=1, identity=identity, tasks=sorted(tasks,key=lambda t:t['task_id']),
       queue_estimated_work_ms=loads, assignment_policy='Longest measured full-run task first across four equal reference-speed queues; actual hardware speed may differ' if baseline else 'Longest scaled pilot estimate first; not a promised runtime',
       pilot_source_sha=pilot['source_git_sha'], baseline_profile_source_sha=baseline['source_git_sha'] if baseline else None,
       cost_basis='measured complete local baseline task costs' if baseline else 'scaled pilot estimates',models=list(CONFIGS))
    output.mkdir(parents=True,exist_ok=True)
    (output/'scientific-packages.json').write_text(json.dumps({p:importlib.metadata.version(p) for p in ['numpy','scipy','scikit-learn','pyproj','joblib']},indent=2)+'\n')
    (output/'shared-inputs.json').write_text(json.dumps(identity,indent=2)+'\n')
    (output/'splits-v1.json').write_text(json.dumps(index['folds'],indent=2)+'\n')
    (output/'laptop-jobs-v1.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(dict(identity=identity,task_count=len(tasks),queue_estimated_work_ms=loads),indent=2))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache',type=Path,required=True)
    parser.add_argument('--pilot',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=Path('configs/ml'))
    parser.add_argument('--baseline-profile',type=Path)
    args=parser.parse_args();build(args.cache,args.pilot,args.output,args.baseline_profile)


if __name__=='__main__':main()
