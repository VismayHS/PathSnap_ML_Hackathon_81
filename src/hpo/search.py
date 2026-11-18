"""Genuine seeded TPE Bayesian optimization on fixed training-trip group folds."""
import argparse
import importlib.metadata
import json
from pathlib import Path
import subprocess
import time
import joblib
import numpy as np
import optuna
from threadpoolctl import threadpool_limits
from src.models.experiments import load_cache,fit_model,evaluate_ids,fit_sample_evaluation,metric_records
from src.models.estimators import CONFIGS
from src.models.provenance import cache_identity,hardware
from src.evaluation.metrics import aggregate

NAME='hist_gradient_boosting'


def run(cache,output,n_trials,threads,complete_recorded_trial=False):
    if output.exists() and not complete_recorded_trial:raise FileExistsError('Use a new immutable HPO run directory, or explicitly complete its recorded interrupted final trial')
    index,sampling,trips=load_cache(cache)
    if not complete_recorded_trial:output.mkdir(parents=True)
    meta=dict(run_id=output.name,source_git_sha=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),identity=cache_identity(index,sampling,trips),model_name=NAME,seed=81,folds=index['folds'],hardware=hardware(threads),optuna_version=importlib.metadata.version('optuna'),sampler='TPESampler',n_startup_trials=4,n_trials=n_trials,objective='mean held-out-trip road-class Macro F1 on fixed five training-trip folds; student test never enters objective',sampling_policy='deterministic <=400 scorable fit observations per train trip; all validation observations',search_space={'max_iter':[60,180],'max_leaf_nodes':[7,31],'min_samples_leaf':[15,80],'learning_rate':[.03,.2,'log'],'l2_regularization':[.01,10.,'log']})
    storage='sqlite:///'+(output/'study.sqlite3').resolve().as_posix()
    if complete_recorded_trial:
        original=json.loads((output/'metadata.json').read_text())
        if original['identity']!=meta['identity'] or original['folds']!=meta['folds']:raise ValueError('Resume input/fold mismatch')
        study=optuna.load_study(study_name=output.name,storage=storage)
        pending=[t for t in study.trials if t.state==optuna.trial.TrialState.RUNNING]
        if len(study.trials)!=n_trials or len(pending)!=1 or pending[0].number!=n_trials-1 or any(t.state!=optuna.trial.TrialState.COMPLETE for t in study.trials[:-1]):raise ValueError('Recovery supports only a fully recorded final interrupted trial; do not silently reset sampler history')
        if set(pending[0].params)!=set(meta['search_space']):raise ValueError('Incomplete pending parameters')
        recovery=dict(original_source_git_sha=original['source_git_sha'],recovery_source_git_sha=meta['source_git_sha'],recorded_trial=pending[0].number,recorded_params=pending[0].params,reason='Original process ended with143; rerun its already sampled final parameters without adding/resampling trials')
        if (output/'recovery.json').exists():raise FileExistsError('Recovery already attempted; preserve evidence for inspection')
        (output/'recovery.json').write_text(json.dumps(recovery,indent=2)+'\n');meta=original
    else:
        (output/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
        study=optuna.create_study(study_name=output.name,storage=storage,direction='maximize',sampler=optuna.samplers.TPESampler(seed=81,n_startup_trials=4))
    started=time.perf_counter()
    def objective(trial):
        params=dict(max_iter=trial.suggest_int('max_iter',60,180),max_leaf_nodes=trial.suggest_int('max_leaf_nodes',7,31),min_samples_leaf=trial.suggest_int('min_samples_leaf',15,80),learning_rate=trial.suggest_float('learning_rate',.03,.2,log=True),l2_regularization=trial.suggest_float('l2_regularization',.01,10.,log=True))
        tick=time.perf_counter();folds=[];validation=[]
        try:
            for fold in index['folds']:
                model,fitting=fit_model(NAME,trips,fold['train'],sampling,params)
                rows=evaluate_ids(model,'train',fold['validation'],trips,with_continuity=False)
                validation+=rows;folds.append(dict(fold=fold['fold'],fit=fitting,aggregate=aggregate(rows),trips=rows))
            result=dict(number=trial.number,status='complete',params=params,folds=folds,cv=aggregate(validation),elapsed_s=time.perf_counter()-tick)
            trial.set_user_attr('elapsed_s',result['elapsed_s']);trial.set_user_attr('fold_macro_f1',[f['aggregate']['macro_f1'] for f in folds])
            (output/f'trial-{trial.number:03d}.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
            print(json.dumps({'trial':trial.number,'cv_macro_f1':result['cv']['macro_f1'],'elapsed_s':result['elapsed_s']}),flush=True)
            return result['cv']['macro_f1']
        except Exception as exc:
            (output/f'trial-{trial.number:03d}-failed.json').write_text(json.dumps(dict(number=trial.number,status='failed',params=params,error=repr(exc),elapsed_s=time.perf_counter()-tick),indent=2)+'\n');raise
    if complete_recorded_trial:
        frozen=pending[0];value=objective(optuna.trial.FixedTrial(frozen.params,number=frozen.number));study.tell(frozen.number,value)
    else:study.optimize(objective,n_trials=n_trials,catch=(ValueError,RuntimeError))
    trials=[dict(number=t.number,state=t.state.name,value=t.value,params=t.params,user_attrs=t.user_attrs) for t in study.trials]
    (output/'trials.json').write_text(json.dumps(trials,indent=2,allow_nan=False)+'\n')
    if not any(t.state==optuna.trial.TrialState.COMPLETE for t in study.trials):raise RuntimeError('No successful tuning trials')
    best=json.loads((output/f'trial-{study.best_trial.number:03d}.json').read_text())
    model,fitting=fit_model(NAME,trips,sorted(sampling),sampling,study.best_params)
    testing=evaluate_ids(model,'student_test',index['student_test_ids'],trips)
    training=fit_sample_evaluation(model,sorted(sampling),trips,sampling)
    joblib.dump(model,output/'best-classifier.joblib',compress=3)
    summary=dict(**meta,best_trial=study.best_trial.number,best_params=study.best_params,configuration={**CONFIGS[NAME],**study.best_params},cv=best['cv'],cv_macro_f1_std=float(np.std([f['aggregate']['macro_f1'] for f in best['folds']])),refit=fitting,fit_sample=aggregate(training),fit_sample_scope='sampled fit observations only',student_test=aggregate(testing),student_per_trip=testing,elapsed_s=time.perf_counter()-started,completed_trial_compute_s=sum(json.loads((output/f'trial-{t.number:03d}.json').read_text())['elapsed_s'] for t in study.trials if t.state==optuna.trial.TrialState.COMPLETE),timing_note='elapsed_s is this invocation including final refit; interrupted partial-trial cost is unavailable; see recovery.json if present',recovery=recovery if complete_recorded_trial else None,trials=trials,status='complete',model_asset='best-classifier.joblib')
    (output/'summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
    with (output/'records.jsonl').open('w') as stream:
        for f in best['folds']:
            for r in metric_records(f['trips'],meta,'train_cv',f['fold'],NAME,'tuned'):stream.write(json.dumps(r,allow_nan=False)+'\n')
        for r in metric_records(testing,meta,'student_test',None,NAME,'tuned'):stream.write(json.dumps(r,allow_nan=False)+'\n')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cache',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--complete-recorded-trial',action='store_true');p.add_argument('--trials',type=int,default=12);p.add_argument('--threads',type=int,default=4);a=p.parse_args()
    if a.trials<5:p.error('At least five trials required to include model-based TPE after four startup trials')
    if not 1<=a.threads<=8:p.error('Use1–8 threads under the shared CPU budget')
    with threadpool_limits(limits=a.threads):run(a.cache,a.output,a.trials,a.threads,a.complete_recorded_trial)

if __name__=='__main__':main()
