"""Generate scientific figures from saved measured baseline summaries."""
import argparse
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def generate(source, output):
    if output.exists(): raise FileExistsError('Use a new figure directory')
    data=json.loads(source.read_text());rows=data['results']
    if any(r['status']!='complete' for r in rows):raise ValueError('Incomplete model comparison')
    output.mkdir(parents=True)
    names=[r['model_name'].replace('_','\n') for r in rows];x=np.arange(len(rows))
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,ax=plt.subplots(figsize=(10,5));ax.bar(x,[r['cv']['macro_f1'] for r in rows],yerr=[r['cv_macro_f1_std'] for r in rows],capsize=5,color='#216e87')
    ax.set(xticks=x,xticklabels=names,ylabel='Mean held-out trip road-class Macro F1',ylim=(0,1),title='Five fixed trip-group folds; bars ± fold standard deviation')
    fig.tight_layout();fig.savefig(output/'training-cv-macro-f1.png',dpi=180);plt.close(fig)
    fig,ax=plt.subplots(figsize=(10,5));ax.bar(x-.18,[r['student_test']['top1_accuracy'] for r in rows],.36,label='Pooled observation accuracy');ax.bar(x+.18,[r['student_test']['macro_f1'] for r in rows],.36,label='Mean trip Macro F1')
    ax.set(xticks=x,xticklabels=names,ylim=(0,1),ylabel='Fraction',title='Ten student-testing trips; provisional alignment; candidate misses retained');ax.legend()
    fig.tight_layout();fig.savefig(output/'student-test-accuracy-f1.png',dpi=180);plt.close(fig)
    fig,ax=plt.subplots(figsize=(10,5));ax.bar(x,[r['student_test']['log_loss'] for r in rows],color='#a45a38')
    ax.set(xticks=x,xticklabels=names,ylabel='Conditional log loss (nats; lower is better)',title='Student test: only observations with the reference arc in candidates')
    fig.tight_layout();fig.savefig(output/'student-test-conditional-log-loss.png',dpi=180);plt.close(fig)
    manifest={'source':source.as_posix(),'input_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'experiment_source_sha':data['source_git_sha'],'figures':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in output.glob('*.png')},'note':'No training epoch/loss curve is invented for estimators without such history.'}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();generate(a.source,a.output)

if __name__=='__main__':main()
