"""Run the actual trained facade twice per development trip and export Folium inputs."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time
import joblib
import numpy as np
from threadpoolctl import threadpool_limits
from src.contracts import PipelineSettings,PredictOptions,ScoringSettings,check_prediction_invariants
from src.pipeline import load_model_bundle,load_prediction_input,predict_trip,list_trip_ids
from src.models.export import export_bundle
from src.evaluation.service import evaluate_completed_prediction
from src.evaluation.reference import read_reference


def reference_pieces(raw,reference):
    """Turn the true route (a list of arc IDs) into map lines for the Folium maps.

    Consecutive arcs that join end-to-start are merged into one line of coordinates;
    wherever the true route jumps to an unconnected arc, a new line is started.
    Used only for the development maps, never for prediction.
    """
    pieces=[];current=[];previous=None
    for arc in reference:
        u,v=raw.arcs[arc];coords=raw.nodes[[u,v]].tolist()
        if previous is None or previous==u:
            current.extend(coords if not current else coords[1:])
        else:
            pieces.append(current);current=coords
        previous=v
    if current:pieces.append(current)
    return pieces


def run(data_root,baseline_path,hpo_path,bundle_output,output):
    """The classifier-only vs classifier + HMM experiment on the 10 student-test trips.

    1. Picks the HGB classifier: the tuned one if tuning improved CV Macro F1, else the untuned one.
    2. Exports it, with the decoder settings, as the final model bundle (artifacts/hgb-hmm-v1).
    3. For every student-test trip, predicts twice through the real pipeline: once with
       the classifier alone and once with HMM/Viterbi, then scores both on the server side.
    4. Saves per-trip records, map data for Folium, and summary.json with the pooled
       results (accuracy, Macro F1, continuity, route pieces, timings) for each decoder.
    """
    if output.exists():raise FileExistsError('Use fresh immutable comparison output')
    baseline=json.loads(baseline_path.read_text());hpo=json.loads(hpo_path.read_text())
    base=next(r for r in baseline['results'] if r['model_name']=='hist_gradient_boosting')
    tuned=hpo['cv']['macro_f1']>base['cv']['macro_f1']
    asset=hpo_path.parent/'best-classifier.joblib' if tuned else baseline_path.parent/'models/hist_gradient_boosting.joblib'
    estimator=joblib.load(asset);source=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    chosen_config=hpo['configuration'] if tuned else base['configuration']
    manifest=export_bundle(bundle_output,estimator,'hist_gradient_boosting',output.name,baseline['data_fingerprint'],config={'training_configuration':chosen_config,'decoder_policy':'fixed-default-v1'})
    manifest['training_provenance']=dict(selected_variant='tuned' if tuned else 'untuned',selection_metric='fixed training-group CV trip Macro F1',training_source_sha=hpo['source_git_sha'] if tuned else baseline['source_git_sha'],training_run=hpo['run_id'] if tuned else baseline['run_id'],training_configuration=hpo['configuration'] if tuned else base['configuration'],training_asset_sha256=hashlib.sha256(asset.read_bytes()).hexdigest(),untuned_cv_macro_f1=base['cv']['macro_f1'],tuned_cv_macro_f1=hpo['cv']['macro_f1'])
    (bundle_output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    settings=PipelineSettings(data_root,bundle_output);bundle=load_model_bundle(settings)
    output.mkdir(parents=True);visual=output/'visualisation';visual.mkdir();records=[]
    from jsonschema import Draft202012Validator
    schema=json.loads(Path('contracts/artifacts.schema.json').read_text());validator=Draft202012Validator({**schema,'$ref':'#/$defs/DevVisualisation'})
    for tid in list_trip_ids('development',settings):
        trip=load_prediction_input(tid,'development',settings);raw=trip.payload['raw'];predictions={};private=None
        for decoder in ['classifier_only','hmm_viterbi']:
            started=time.perf_counter();result=predict_trip(trip,bundle,PredictOptions(decoder=decoder))
            problems=check_prediction_invariants(result)
            if problems:raise ValueError(problems)
            scored=evaluate_completed_prediction(result,ScoringSettings(settings,'development'))
            if scored.status!='scored':raise ValueError('Real development scorer unexpectedly unavailable')
            metrics={m.name:m.value for m in scored.metrics};counts={m.name:dict(numerator=m.numerator,denominator=m.denominator,policy=m.denominator_policy) for m in scored.metrics}
            records.append(dict(trip_id=tid,decoder=decoder,metrics=metrics,counts=counts,timings_ms=result.timings_ms,scoring_ms=scored.elapsed_ms,wall_s=time.perf_counter()-started,route_pieces=len(result.route),warnings=[dict(code=w.code,message=w.message) for w in result.warnings]))
            predictions[decoder]=dict(pieces=[list(p.coordinates) for p in result.route],observations=[[o.index,o.arc_id,o.status] for o in result.observations]);private=result.scorer_evidence
            print(json.dumps(dict(trip_id=tid,decoder=decoder,top1_accuracy=metrics['top1_accuracy'],macro_f1=metrics['macro_f1'],route_continuity=metrics['route_continuity'],wall_s=records[-1]['wall_s'])),flush=True)
        # Reference access is development-only and happens after both prediction calls.
        reference=read_reference(data_root/'student_test'/tid,len(raw.arcs))
        candidate_ids=sorted({int(a) for c in private['candidates'] for a in c.arc_ids})
        vis=dict(schema='pathsnap-dev-vis/1',partition='student_test',trip_id=tid,run_id=output.name,source_git_sha=source,model_version=bundle.info.model_version,gps=[[int(i),float(row[0]),float(row[1]),float(row[2]) if np.isfinite(row[2]) else None] for i,row in enumerate(raw.track) if raw.valid[i]],network=[dict(arc_id=int(a),coordinates=raw.nodes[raw.arcs[a]].tolist()) for a in candidate_ids],reference=dict(arc_ids=reference.tolist(),pieces=reference_pieces(raw,reference)),predictions=predictions)
        validator.validate(vis);(visual/f'{tid}.json').write_text(json.dumps(vis,allow_nan=False)+'\n')
        (output/f'{tid}.json').write_text(json.dumps(records[-2:],indent=2,allow_nan=False)+'\n')
    aggregates={}
    for decoder in ['classifier_only','hmm_viterbi']:
        rows=[r for r in records if r['decoder']==decoder];metrics={}
        for name in rows[0]['metrics']:
            valid=[r for r in rows if r['metrics'][name] is not None]
            if name in ['top1_accuracy','candidate_miss_rate','route_continuity','scored_match_fraction_original']:
                denominator=sum(r['counts'][name]['denominator'] for r in valid);value=sum(r['counts'][name]['numerator'] for r in valid)/denominator if denominator else None
            elif name=='log_loss':
                denominator=sum(r['counts'][name]['denominator'] for r in valid);value=sum(r['metrics'][name]*r['counts'][name]['denominator'] for r in valid)/denominator if denominator else None
            elif name.endswith('observations') or name in ['candidate_covered','candidate_misses']:value=sum(r['metrics'][name] for r in valid)
            else:value=float(np.mean([r['metrics'][name] for r in valid])) if valid else None
            metrics[name]=value
        aggregates[decoder]=dict(metrics=metrics,inference_total_ms=sum(r['timings_ms']['predict_total'] for r in rows),decode_ms=sum(r['timings_ms']['decode'] for r in rows),route_pieces=sum(r['route_pieces'] for r in rows))
    summary=dict(run_id=output.name,source_git_sha=source,partition='student_test',model_version=bundle.info.model_version,selected_variant='tuned' if tuned else 'untuned',training_provenance=manifest['training_provenance'],decoder_config=manifest['decoder_config'],decoder_parameters_policy='Fixed a priori; no student-test tuning',aggregates=aggregates,trips=records,visualisation='visualisation',bundle_manifest_sha256=hashlib.sha256((bundle_output/'manifest.json').read_bytes()).hexdigest())
    (output/'summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')


def main():
    """Command-line entry point: read the paths and run the comparison with 4 threads."""
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--data-root',type=Path,required=True);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--hpo',type=Path,required=True);p.add_argument('--bundle-output',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    with threadpool_limits(limits=4):run(a.data_root,a.baseline,a.hpo,a.bundle_output,a.output)

if __name__=='__main__':main()
