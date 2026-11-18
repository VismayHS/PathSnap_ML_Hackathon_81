"""Run assigned, independent baseline fold/refit jobs on a human team laptop."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time
import joblib
from threadpoolctl import threadpool_limits
from src.models.estimators import CONFIGS,FAMILIES,OBJECTIVES
from src.models.experiments import load_cache,fit_model,evaluate_ids,fit_sample_evaluation,metric_records
from src.models.provenance import cache_identity,verify_kit_source,hardware,digest_json,file_digest
from src.evaluation.metrics import aggregate


def run(cache,output,laptop,kit_source,threads,manifest_path,only=None,verify_only=False):
    code_hash=verify_kit_source(kit_source)
    manifest=json.loads(manifest_path.read_text())
    expected=json.loads(Path('configs/ml/shared-inputs.json').read_text())
    index,sampling,trips=load_cache(cache)
    identity=cache_identity(index,sampling,trips)
    if identity != expected or identity != manifest['identity']:
        raise ValueError('Input/source/cache/split fingerprint mismatch; do not edit expected hashes. Use the common verified cache.')
    environment=hardware(threads)
    expected_packages=json.loads(Path('configs/ml/scientific-packages.json').read_text())
    if environment['packages'] != expected_packages or environment['python'].split('.')[:2] != ['3','12']:
        raise ValueError('Use CPython 3.12 and the exact requirements.lock.txt scientific package versions')
    print(json.dumps({'verified':True,'identity':identity,'source_code_sha256':code_hash,'hardware':environment}),flush=True)
    if verify_only:return
    if output.exists():raise FileExistsError('Use a new, unique run directory; existing evidence is immutable')
    if not output.name.startswith(laptop+'-'):raise ValueError('Run directory must start with your laptop-N identifier')
    known={t['task_id']:t for t in manifest['tasks']}
    if only:
        if set(only)-set(known):raise ValueError('Unknown task ID')
        tasks=[known[t] for t in only]
    else:tasks=[t for t in manifest['tasks'] if t['laptop']==laptop]
    if not tasks:raise ValueError('No assigned tasks')
    output.mkdir(parents=True)
    meta=dict(schema='pathsnap-training-worker/1',run_id=output.name,source_git_sha=kit_source,
        execution_git_sha=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        source_code_sha256=code_hash,identity=identity,hardware=environment,laptop=laptop,
        model_configs=CONFIGS,model_objectives=OBJECTIVES,preparation_source_sha=index['source_git_sha'],
        task_manifest_sha256=digest_json(manifest),metric_policy_id='pathsnap-scoring-v0',
        timing_policy='candidate scoring excludes cached preparation and metric calculation; compare hosts separately')
    (output/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    finished=[];started=time.perf_counter()
    with (output/'records.jsonl').open('w') as stream:
        for task in tasks:
            tick=time.perf_counter();name=task['model']
            try:
                params={'n_jobs':threads} if 'n_jobs' in CONFIGS[name] else {}
                if task['kind']=='cv':
                    fold=next(f for f in index['folds'] if f['fold']==task['fold'])
                    model,fitting=fit_model(name,trips,fold['train'],sampling,params)
                    rows=evaluate_ids(model,'train',fold['validation'],trips)
                    result=dict(fit=fitting,aggregate=aggregate(rows),trips=rows,partition='train_cv')
                    records=list(metric_records(rows,meta,'train_cv',task['fold'],name))
                elif task['kind']=='refit':
                    ids=sorted(sampling);model,fitting=fit_model(name,trips,ids,sampling,params)
                    rows=evaluate_ids(model,'student_test',index['student_test_ids'],trips)
                    fit_rows=fit_sample_evaluation(model,ids,trips,sampling)
                    models=output/'models';models.mkdir(exist_ok=True)
                    asset=models/f'{task["task_id"]}.joblib';joblib.dump(model,asset,compress=3)
                    result=dict(fit=fitting,student_test=aggregate(rows),student_per_trip=rows,
                        fit_sample=aggregate(fit_rows),fit_sample_scope='sampled fit observations only',
                        model_asset={'path':asset.relative_to(output).as_posix(),'sha256':hashlib.sha256(asset.read_bytes()).hexdigest(),'bytes':asset.stat().st_size})
                    records=list(metric_records(rows,meta,'student_test',None,name))
                else:raise ValueError('Unsupported task kind')
                result.update(schema='pathsnap-training-task/1',task=task,status='complete',
                    source_git_sha=kit_source,source_code_sha256=code_hash,identity=identity,
                    model_config=CONFIGS[name],runtime_overrides=params,run_id=output.name,
                    laptop=laptop,hardware=environment,elapsed_s=time.perf_counter()-tick)
                for record in records:stream.write(json.dumps(record,allow_nan=False)+'\n')
                stream.flush()
            except Exception as exc:
                result=dict(schema='pathsnap-training-task/1',task=task,status='failed',error=repr(exc),
                    source_git_sha=kit_source,source_code_sha256=code_hash,identity=identity,
                    run_id=output.name,laptop=laptop,hardware=environment,elapsed_s=time.perf_counter()-tick)
            (output/f'job-{task["task_id"]}.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
            finished.append({'task_id':task['task_id'],'status':result['status']})
            print(json.dumps({'task_id':task['task_id'],'status':result['status'],'elapsed_s':result['elapsed_s']}),flush=True)
    summary=dict(**meta,completed_tasks=finished,elapsed_s=time.perf_counter()-started,
                 status='complete' if all(t['status']=='complete' for t in finished) else 'failed')
    files={p.relative_to(output).as_posix():file_digest(p)
           for p in sorted(output.rglob('*')) if p.is_file()}
    summary['file_sha256']=files
    summary['file_hash_policy']='JSON/JSONL canonical LF; binary assets exact bytes'
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    if summary['status']!='complete':raise SystemExit('Some tasks failed; preserve evidence and retry only those IDs in a new run')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=Path('results/experiments/verify-only'))
    parser.add_argument('--laptop',choices=[f'laptop-{i}' for i in range(1,5)],required=True)
    parser.add_argument('--kit-source',required=True)
    parser.add_argument('--threads',type=int,default=2)
    parser.add_argument('--manifest',type=Path,default=Path('configs/ml/laptop-jobs-v1.json'))
    parser.add_argument('--only',nargs='+',help='Coordinator-approved task IDs, including reassigned/retried work')
    parser.add_argument('--verify-only',action='store_true')
    args=parser.parse_args()
    if not 1<=args.threads<=64:parser.error('threads must be between1 and64; do not exceed your machine capacity')
    with threadpool_limits(limits=args.threads):
        run(args.cache,args.output,args.laptop,args.kit_source,args.threads,args.manifest,args.only,args.verify_only)


if __name__=='__main__':main()
