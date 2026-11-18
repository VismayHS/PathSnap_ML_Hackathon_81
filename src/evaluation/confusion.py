"""Development-only sparse observation confusion matrices with trip-local road IDs."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time
import joblib
import numpy as np
from threadpoolctl import threadpool_limits
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from src.models.experiments import load_cache


def sparse_confusion(labels,scorable,prediction):
    pairs=np.column_stack((labels[scorable],prediction[scorable]));unique,counts=np.unique(pairs,axis=0,return_counts=True)
    return dict(entries=[[int(a),int(b),int(n)] for (a,b),n in zip(unique,counts)],scorable_observations=int(scorable.sum()),correct=int((pairs[:,0]==pairs[:,1]).sum()))


def run(cache,baseline,hpo,decoder,output):
    if output.exists():raise FileExistsError('Use a new confusion evidence directory')
    index,sampling,trips=load_cache(cache);base=json.loads(baseline.read_text());h=json.loads(hpo.read_text());d=json.loads(decoder.read_text());output.mkdir(parents=True)
    variants=[(r['model_name'],baseline.parent/'models'/f'{r["model_name"]}.joblib',r['student_test']['top1_accuracy']) for r in base['results']]
    variants.append(('hist_gradient_boosting_tuned',hpo.parent/'best-classifier.joblib',h['student_test']['top1_accuracy']))
    all_results=[];start=time.perf_counter()
    def retain(name,rows,expected):
        accuracy=sum(r['correct'] for r in rows)/sum(r['scorable_observations'] for r in rows)
        if abs(accuracy-expected)>1e-12:raise ValueError('Confusion matrix accuracy differs from saved experiment')
        record=dict(name=name,partition='student_test',accuracy=accuracy,trips=rows)
        (output/f'{name}.json').write_text(json.dumps(record,indent=2)+'\n');all_results.append(record)
        representative=next(r for r in rows if r['trip_id']=='00000052');classes=sorted({v for a,b,n in representative['entries'] for v in [a,b]});positions={a:i for i,a in enumerate(classes)};matrix=np.zeros((len(classes),len(classes)),dtype=int)
        for a,b,n in representative['entries']:matrix[positions[a],positions[b]]=n
        fig,ax=plt.subplots(figsize=(9,7));im=ax.imshow(matrix,cmap='Blues',interpolation='nearest');ticks=np.arange(0,len(classes),10);ax.set(xticks=ticks,yticks=ticks,xlabel='Predicted trip-local arc class index',ylabel='Reference-derived trip-local arc class index',title=f'{name}: trip00000052; all scorable observations');fig.colorbar(im,ax=ax,label='Observations');fig.tight_layout();fig.savefig(output/f'{name}.png',dpi=180);plt.close(fig)
        (output/f'{name}-class-order.json').write_text(json.dumps(dict(trip_id='00000052',axis_index_to_arc_id=classes,unmatched_arc_id=-1),indent=2)+'\n')
    for name,asset,expected in variants:
        model=joblib.load(asset);rows=[]
        for tid in index['student_test_ids']:
            data=trips[('student_test',tid)];scores=model.predict_proba(data['X'])[:,list(model.classes_).index(1)];prediction=np.full(len(data['labels']),-1,dtype=int)
            for i,(lo,hi) in enumerate(zip(data['offsets'][:-1],data['offsets'][1:])):
                if hi>lo:prediction[i]=data['candidate_arc_ids'][lo+np.argmax(scores[lo:hi])]
            rows.append(dict(trip_id=tid,**sparse_confusion(data['labels'],data['scorable'],prediction)))
        retain(name,rows,expected);print(json.dumps(dict(model=name,accuracy=all_results[-1]['accuracy'])),flush=True)
    rows=[]
    for tid in index['student_test_ids']:
        data=trips[('student_test',tid)];vis=json.loads((decoder.parent/'visualisation'/f'{tid}.json').read_text());prediction=np.array([a if a is not None else -1 for i,a,status in vis['predictions']['hmm_viterbi']['observations']]);rows.append(dict(trip_id=tid,**sparse_confusion(data['labels'],data['scorable'],prediction)))
    retain('hist_gradient_boosting_tuned_hmm',rows,d['aggregates']['hmm_viterbi']['metrics']['top1_accuracy'])
    summary=dict(source_git_sha=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),data_fingerprint=index['data_fingerprint'],partition='student_test',policy='pathsnap-scoring-v0; sparse[true arc,predicted arc,count] pertrip; unmatched=-1; unscorable excluded and counted in primary experiments',inputs={p.as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in [baseline,hpo,decoder]},results=[dict(name=r['name'],accuracy=r['accuracy'],trips=len(r['trips'])) for r in all_results],elapsed_s=time.perf_counter()-start,figures='Complete matrix for trip00000052; axis order maps to original local arc IDs in class-order JSON. Arc classes are never pooled across trip networks.')
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for arg in ['cache','baseline','hpo','decoder','output']:p.add_argument('--'+arg,type=Path,required=True)
    a=p.parse_args()
    with threadpool_limits(limits=4):run(a.cache,a.baseline,a.hpo,a.decoder,a.output)
if __name__=='__main__':main()
