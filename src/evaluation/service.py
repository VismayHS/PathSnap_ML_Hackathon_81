"""Post-prediction aggregate scoring; reference access never enters inference."""
import time
import numpy as np
from src.contracts import EvaluationSummary,MetricValue,validate_trip_id_syntax
from src.evaluation.alignment import POLICY_ID,align_reference
from src.evaluation.reference import read_reference
from src.evaluation.metrics import observation_metrics,continuity


def evaluate_completed_prediction(prediction, scoring_settings):
    started=time.perf_counter()
    def unavailable(reason):
        return EvaluationSummary('unavailable',POLICY_ID,'provisional',unavailable_reason=reason,elapsed_ms=(time.perf_counter()-started)*1000)
    if prediction.model_kind=='diagnostic':return unavailable('Diagnostic output is for integration; no trained-model benchmark is available')
    if scoring_settings.policy_id!=POLICY_ID or scoring_settings.mode!=prediction.mode:
        return unavailable('Scoring policy or data mode does not match the completed prediction')
    if not prediction.scorer_evidence:return unavailable('Private candidate-distribution evidence is unavailable')
    try:
        from src.pipeline import partition_root
        validate_trip_id_syntax(prediction.trip_id)
        root=partition_root(prediction.mode,scoring_settings.settings)
        directory=root/prediction.trip_id;path=directory/f'{prediction.trip_id}.route'
        if directory.is_symlink() or path.is_symlink() or directory.resolve().parent!=root or path.resolve().parent!=directory.resolve():
            return unavailable('Reference access is unavailable for this trip')
        e=prediction.scorer_evidence;raw=e['raw'];geometry=e['geometry'];candidates=e['candidates']
        reference=read_reference(directory,len(raw.arcs))
        aligned=align_reference(raw,geometry,reference)
        sizes=np.array([len(c.arc_ids) for c in candidates]);row_observation=np.repeat(np.arange(len(sizes)),sizes)
        arcs=np.concatenate([c.arc_ids for c in candidates]);probabilities=np.concatenate(e['probabilities'])
        selected=np.array([o.arc_id if o.arc_id is not None else -1 for o in prediction.observations],dtype=int)
        result=observation_metrics(aligned.arc_ids,aligned.scorable,selected,arcs,row_observation,probabilities)
        offsets=np.r_[0,np.cumsum(sizes)];selected_rows=np.full(len(sizes),-1,dtype=int)
        for i,c in enumerate(candidates):
            if selected[i]>=0:selected_rows[i]=offsets[i]+int(np.flatnonzero(c.arc_ids==selected[i])[0])
        c=continuity(dict(arcs=raw.arcs,lengths=geometry.length,track=raw.track,valid=raw.valid,fractions=np.concatenate([c.fractions for c in candidates])),selected,selected_rows)
        result['values']['route_continuity']=c['value'];counts=result['counts'];metrics=[]
        for name,value in result['values'].items():
            denominator=counts['scorable_observations'];numerator=None;policy='All provisional scorable observations, including candidate misses and unmatched predictions'
            if name=='top1_accuracy':numerator=counts['correct']
            elif name=='candidate_miss_rate':numerator=counts['candidate_misses']
            elif name in ('macro_f1','precision_macro','recall_macro'):
                denominator=counts['road_classes'];policy='Trip-local road classes in truth union matched predictions; unmatched predictions contribute false negatives'
            elif name=='log_loss':
                denominator=counts['candidate_covered'];policy='Scorable observations whose label arc occurs in the candidate set; normalized classifier relevance, not calibrated probability'
            elif name=='sequence_arc_similarity':
                denominator=counts['sequence_length'];policy='One minus normalized Levenshtein distance of compressed scorable observed-arc sequences; not full route accuracy'
            elif name=='scored_match_fraction_original':denominator=counts['original_observations'];numerator=counts['correct'];policy='All original observation rows, including unscorable rows'
            elif name=='route_continuity':denominator=c['denominator'];numerator=c['numerator'];policy='All consecutive valid observation pairs with 0 < time delta <=30s; unmatched or physically unreachable pairs fail'
            metrics.append(MetricValue(name,value,'nats' if name=='log_loss' else 'fraction',numerator,denominator,policy,result['unavailable_reasons'].get(name) or ('no_eligible_observations' if value is None else None)))
        for name in ['scorable_observations','unscorable_observations','original_observations','candidate_covered','candidate_misses']:
            metrics.append(MetricValue(name,float(counts[name]),'count',counts[name],None,'Count under provisional alignment; original row indices preserved'))
        return EvaluationSummary('scored',POLICY_ID,'provisional',tuple(metrics),elapsed_ms=(time.perf_counter()-started)*1000)
    except (OSError,ValueError,IndexError,KeyError):
        return unavailable('Reference or scoring evidence is missing or invalid; prediction remains available')
