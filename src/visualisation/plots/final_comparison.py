"""Plot actual Bayesian trial history and classifier/HMM comparison."""
import argparse
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def generate(hpo_path,decoder_path,output):
    if output.exists():raise FileExistsError('Use a new figure directory')
    hpo=json.loads(hpo_path.read_text());decoder=json.loads(decoder_path.read_text());output.mkdir(parents=True)
    trials=[t for t in hpo['trials'] if t['state']=='COMPLETE'];x=[t['number'] for t in trials];y=[t['value'] for t in trials]
    fig,ax=plt.subplots(figsize=(9,4.5));ax.scatter(x,y,label='Complete trial');ax.plot(x,np.maximum.accumulate(y),label='Best so far');ax.axvline(3.5,color='#888',linestyle='--',label='TPE begins after four startup trials');ax.set(xlabel='Trial number (zero based)',ylabel='Fixed training-group CV trip Macro F1',title='Actual seeded Bayesian optimization history');ax.legend();fig.tight_layout();fig.savefig(output/'bayesian-trials.png',dpi=180);plt.close(fig)
    provenance=decoder['training_provenance'];fig,ax=plt.subplots(figsize=(6,4.5));ax.bar(['Untuned','Tuned'],[provenance['untuned_cv_macro_f1'],provenance['tuned_cv_macro_f1']],color=['#777','#216e87']);ax.set(ylabel='Training CV trip Macro F1',ylim=(0,1),title='Identical folds, features and sampling');fig.tight_layout();fig.savefig(output/'tuned-untuned.png',dpi=180);plt.close(fig)
    variants=['classifier_only','hmm_viterbi'];names=['top1_accuracy','macro_f1','route_continuity','sequence_arc_similarity'];x=np.arange(len(names));fig,ax=plt.subplots(figsize=(10,4.8))
    for i,v in enumerate(variants):ax.bar(x+(i-.5)*.36,[decoder['aggregates'][v]['metrics'][n] for n in names],.36,label=v)
    ax.set(xticks=x,xticklabels=['Pooled accuracy','Mean trip Macro F1','Legal continuity','Observed-arc similarity'],ylim=(0,1),ylabel='Fraction',title='Ten student-testing trips; fixed graph decoder; provisional reference alignment');ax.legend();fig.tight_layout();fig.savefig(output/'classifier-hmm.png',dpi=180);plt.close(fig)
    manifest=dict(inputs={p.as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in [hpo_path,decoder_path]},figures={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in output.glob('*.png')},notes='Sequence score compares compressed observed-arc runs, not reconstructed full route; normalized relevance is not calibrated probability.')
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--hpo',type=Path,required=True);p.add_argument('--decoder',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();generate(a.hpo,a.decoder,a.output)
if __name__=='__main__':main()
