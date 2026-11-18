"""Validate complete independent worker results before scientific aggregation."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from src.models.provenance import digest_json, revision_source_fingerprint, file_digest
from src.evaluation.metrics import aggregate


def collect(runs,output,kit_source,manifest_path):
    if output.exists():raise FileExistsError('Use a new aggregate output directory')
    manifest=json.loads(manifest_path.read_text());expected=manifest['identity']
    required={t['task_id']:t for t in manifest['tasks']};found={};failures=[]
    code_hash=revision_source_fingerprint(kit_source)
    for run in runs:
        meta=json.loads((run/'metadata.json').read_text());summary=json.loads((run/'summary.json').read_text())
        if meta['schema']!='pathsnap-training-worker/1' or meta['source_git_sha']!=kit_source:
            raise ValueError('Mismatched kit source/schema')
        if meta['identity']!=expected or meta['task_manifest_sha256']!=digest_json(manifest):
            raise ValueError('Mismatched source/input/split/cache/config manifest')
        if meta['source_code_sha256']!=code_hash:raise ValueError('Scientific code differs between workers')
        actual_files={p.relative_to(run).as_posix() for p in run.rglob('*') if p.is_file() and p.name!='summary.json'}
        if actual_files != set(summary['file_sha256']):
            raise ValueError('Returned run has missing or unsealed extra files')
        for name,checksum in summary['file_sha256'].items():
            path=(run/name).resolve()
            if not path.is_relative_to(run.resolve()) or file_digest(path)!=checksum:
                raise ValueError('Returned file checksum/path invalid')
        for path in sorted(run.glob('job-*.json')):
            result=json.loads(path.read_text());task=result['task'];tid=task['task_id']
            if tid not in required or task!=required[tid]:raise ValueError('Unknown or modified task')
            if result['source_git_sha']!=kit_source or result['identity']!=expected or result['source_code_sha256']!=code_hash:
                raise ValueError('Task provenance mismatch')
            if result['status']!='complete':failures.append(dict(path=str(path),error=result.get('error')));continue
            if tid in found:raise ValueError(f'Duplicate successful task {tid}; choose canonical runs explicitly, never select the highest score')
            if 'model_asset' in result:
                asset=result['model_asset'];p=(run/asset['path']).resolve()
                if not p.is_relative_to(run.resolve()) or p.stat().st_size!=asset['bytes'] or hashlib.sha256(p.read_bytes()).hexdigest()!=asset['sha256']:
                    raise ValueError('Returned model checksum/path invalid')
            found[tid]=dict(result,return_directory=str(run))
    missing=sorted(set(required)-set(found))
    if missing:raise ValueError('Missing successful tasks: '+', '.join(missing))
    models=[]
    for name in manifest['models']:
        folds=[found[f'{name}-cv-{i}'] for i in range(5)]
        validation=[trip for fold in folds for trip in fold['trips']]
        if len({t['trip_id'] for t in validation})!=80 or len(validation)!=80:
            raise ValueError('Held-out trip coverage is not exactly the common80-trip split')
        refit=found[f'{name}-refit']
        models.append(dict(model_name=name,cv=aggregate(validation),
             cv_macro_f1_std=float(np.std([f['aggregate']['macro_f1'] for f in folds])),
             student_test=refit['student_test'],fit_sample=refit['fit_sample'],
             model_asset=refit['model_asset'],model_return_directory=f"results/experiments/{refit['run_id']}",configuration=refit['model_config'],cv_per_trip=validation,student_per_trip=refit['student_per_trip'],
             cv_tasks=[f['run_id'] for f in folds],refit_run=refit['run_id']))
    output.mkdir(parents=True)
    report=dict(schema='pathsnap-collected-baselines/1',source_git_sha=kit_source,identity=expected,
       source_code_sha256=code_hash,models=models,task_count=len(found),failure_history=failures,
       timing_policy='Different hardware/threads: raw worker times cannot rank algorithm speed; profile returned models on a common machine',
       cv_f1_leader=max(models,key=lambda m:m['cv']['macro_f1'])['model_name'])
    (output/'comparison.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'models':len(models),'verified_tasks':len(found),'cv_f1_leader':report['cv_f1_leader']},indent=2))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runs',type=Path,nargs='+',required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--kit-source',required=True)
    parser.add_argument('--manifest',type=Path,default=Path('configs/ml/laptop-jobs-v1.json'))
    args=parser.parse_args();collect(args.runs,args.output,args.kit_source,args.manifest)


if __name__=='__main__':main()
