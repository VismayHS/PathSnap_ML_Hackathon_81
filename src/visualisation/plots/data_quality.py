"""Plot actual permitted-partition EDA and provisional target coverage."""
import argparse
import hashlib
import json
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def generate(eda,preparation,output):
    if output.exists():raise FileExistsError('Use a fresh figure directory')
    frame=pd.read_csv(eda,dtype={'trip_id':str});prep=json.loads(preparation.read_text());rows=prep['records'];output.mkdir(parents=True)
    fig,axes=plt.subplots(1,2,figsize=(10,4.5))
    for partition,color in [('train','#216e87'),('student_test','#a45a38')]:
        selected=frame[frame.partition==partition];axes[0].hist(selected.observations,bins=20,alpha=.65,label=partition,color=color)
        axes[1].scatter(selected.observations,selected.max_gap_s,label=partition,alpha=.7,color=color)
    axes[0].set(xlabel='Original observations per trip',ylabel='Trips',title='All 90 permitted trips');axes[1].set(xlabel='Original observations',ylabel='Maximum time gap (seconds; log scale)',yscale='log',title='Large gaps require decoder restarts');axes[0].legend();axes[1].legend();fig.tight_layout();fig.savefig(output/'trip-sizes-and-gaps.png',dpi=180);plt.close(fig)
    fig,ax=plt.subplots(figsize=(7,4.8));parts=['train','student_test'];unscorable=[sum(r['unscorable'] for r in rows if r['partition']==p) for p in parts];covered=[sum(r['covered'] for r in rows if r['partition']==p) for p in parts];miss=[sum(r['candidate_misses'] for r in rows if r['partition']==p) for p in parts];ax.bar(parts,covered,label='Scorable, reference candidate present');ax.bar(parts,miss,bottom=covered,label='Scorable candidate miss');ax.bar(parts,unscorable,bottom=[a+b for a,b in zip(covered,miss)],label='Unscorable (provisional alignment)');ax.set(ylabel='Original observations',title='All rows accounted for; unscorable rows are not hidden');ax.legend();fig.tight_layout();fig.savefig(output/'target-coverage.png',dpi=180);plt.close(fig)
    (output/'manifest.json').write_text(json.dumps(dict(inputs={p.as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in [eda,preparation]},figures={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in output.glob('*.png')}),indent=2)+'\n')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--eda',type=Path,required=True);p.add_argument('--preparation',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();generate(a.eda,a.preparation,a.output)
if __name__=='__main__':main()
