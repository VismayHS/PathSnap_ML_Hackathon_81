"""Compare untuned/tuned HGB candidate scoring on one host with identical threads."""
import argparse
import json
from pathlib import Path
import subprocess
import time
import joblib
import numpy as np
from threadpoolctl import threadpool_limits
from src.evaluation.metrics import score_estimator
from src.models.experiments import load_cache
from src.models.provenance import hardware


def run(cache,baseline,hpo,output):
    if output.exists():raise FileExistsError('Use new profiling output')
    index,sampling,trips=load_cache(cache);output.mkdir(parents=True);results=[]
    for name,asset in [('untuned',baseline.parent/'models/hist_gradient_boosting.joblib'),('tuned',hpo.parent/'best-classifier.joblib')]:
        model=joblib.load(asset);times=[]
        for repeat in range(4):
            elapsed=sum(score_estimator(model,trips[('student_test',tid)],with_continuity=False)['candidate_scoring_ms'] for tid in index['student_test_ids'])
            if repeat:times.append(elapsed)
        results.append(dict(variant=name,repeats_ms=times,median_ms=float(np.median(times))))
    (output/'summary.json').write_text(json.dumps(dict(source_git_sha=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),hardware=hardware(4),partition='student_test',observations=sum(len(trips[('student_test',tid)]['labels']) for tid in index['student_test_ids']),boundary='Saved preprocessing+model relevance+observation normalization/selection; excludes cached feature/candidate construction, graph decoding and separately computed reference metrics; one warmup then3 measured passes each',results=results),indent=2)+'\n')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for arg in ['cache','baseline','hpo','output']:p.add_argument('--'+arg,type=Path,required=True)
    a=p.parse_args()
    with threadpool_limits(limits=4):run(a.cache,a.baseline,a.hpo,a.output)
if __name__=='__main__':main()
