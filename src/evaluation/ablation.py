"""Fixed-parameter HGB feature-block ablation on identical development splits."""
import argparse
import json
from pathlib import Path
import subprocess
import time
import warnings
import joblib
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from threadpoolctl import threadpool_limits
from src.models.experiments import load_cache,fit_arrays,evaluate_ids,metric_records
from src.models.estimators import make_estimator
from src.models.provenance import cache_identity,hardware
from src.evaluation.metrics import aggregate

BLOCKS={'distance_only':[0,1,8],'distance_heading':[0,1,2,3,8]}


def run(cache,hpo_path,output):
    if output.exists():raise FileExistsError('Use a fresh ablation directory')
    index,sampling,trips=load_cache(cache);h=json.loads(hpo_path.read_text());output.mkdir(parents=True)
    meta=dict(run_id=output.name,source_git_sha=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),identity=cache_identity(index,sampling,trips),hardware=hardware(4),config=h['configuration'],folds=index['folds'],selection_policy='Descriptive fixed-parameter feature ablation; no retuning or model/decoder selection from these results. Parameters were tuned for full features, so comparison favors that reference configuration.',model_name='hist_gradient_boosting',full_feature_source=hpo_path.as_posix())
    (output/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n');results=[];start=time.perf_counter()
    def fit(columns,ids):
        X,y=fit_arrays(trips,ids,sampling)
        model=Pipeline([('feature_subset',ColumnTransformer([('selected','passthrough',columns)],remainder='drop')),('relevance',make_estimator('hist_gradient_boosting',h['best_params']))])
        tick=time.perf_counter()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always');model.fit(X,y)
        return model,dict(fit_ms=(time.perf_counter()-tick)*1000,fit_rows=len(y),warnings=[str(w.message) for w in caught])
    with (output/'records.jsonl').open('w') as stream:
        for name,columns in BLOCKS.items():
            tick=time.perf_counter();folds=[];validation=[]
            for fold in index['folds']:
                model,fitting=fit(columns,fold['train']);rows=evaluate_ids(model,'train',fold['validation'],trips,with_continuity=False);validation+=rows;folds.append(dict(fold=fold['fold'],fit=fitting,aggregate=aggregate(rows),trips=rows))
                for r in metric_records(rows,meta,'train_cv',fold['fold'],'hist_gradient_boosting','tuned'):
                    r['feature_variant']=name;stream.write(json.dumps(r,allow_nan=False)+'\n')
            model,fitting=fit(columns,sorted(sampling));testing=evaluate_ids(model,'student_test',index['student_test_ids'],trips);joblib.dump(model,output/f'{name}.joblib',compress=3)
            result=dict(feature_variant=name,feature_names=[index['feature_names'][i] for i in columns],columns=columns,cv=aggregate(validation),folds=folds,student_test=aggregate(testing),student_per_trip=testing,refit=fitting,elapsed_s=time.perf_counter()-tick,status='complete')
            for r in metric_records(testing,meta,'student_test',None,'hist_gradient_boosting','tuned'):
                r['feature_variant']=name;stream.write(json.dumps(r,allow_nan=False)+'\n')
            stream.flush();results.append(result);(output/f'{name}.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print(json.dumps(dict(feature_variant=name,cv_macro_f1=result['cv']['macro_f1'],student_accuracy=result['student_test']['top1_accuracy'],elapsed_s=result['elapsed_s'])),flush=True)
    results.append(dict(feature_variant='full_features',feature_names=index['feature_names'],cv=h['cv'],student_test=h['student_test'],status='complete',source=hpo_path.as_posix()))
    summary=dict(**meta,results=results,elapsed_s=time.perf_counter()-start,status='complete');(output/'summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(8,4.5));x=np.arange(len(results));ax.bar(x-.18,[r['cv']['macro_f1'] for r in results],.36,label='Training group-CV Macro F1');ax.bar(x+.18,[r['student_test']['macro_f1'] for r in results],.36,label='Student trip Macro F1');ax.set(xticks=x,xticklabels=['Distance block','+ heading','Full features'],ylim=(0,1),ylabel='Macro F1',title='Same HGB parameters, folds, candidates and fit sampling');ax.legend();fig.tight_layout();fig.savefig(output/'feature-ablation.png',dpi=180);plt.close(fig)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for arg in ['cache','hpo','output']:p.add_argument('--'+arg,type=Path,required=True)
    a=p.parse_args()
    with threadpool_limits(limits=4):run(a.cache,a.hpo,a.output)
if __name__=='__main__':main()
