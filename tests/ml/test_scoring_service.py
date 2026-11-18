from dataclasses import replace
from src.contracts import ScoringSettings,PredictOptions
from src.pipeline import load_prediction_input,load_model_bundle,predict_trip
from src.evaluation.service import evaluate_completed_prediction
from test_pipeline import fixture_settings


def test_posthoc_reference_changes_scoring_without_changing_prediction(tmp_path):
    settings=fixture_settings(tmp_path)
    result=predict_trip(load_prediction_input('00000007','development',settings),load_model_bundle(settings),PredictOptions())
    scoring=ScoringSettings(settings,'development')
    assert evaluate_completed_prediction(result,scoring).status=='unavailable'
    trained=replace(result,model_kind='trained')
    assert evaluate_completed_prediction(trained,scoring).status=='unavailable'
    path=settings.data_root/'student_test'/'00000007'/'00000007.route';path.write_text('0\n')
    evaluated=evaluate_completed_prediction(trained,scoring)
    assert evaluated.status=='scored'
    values={m.name:m for m in evaluated.metrics}
    assert values['original_observations'].value==4
    assert values['scorable_observations'].value==3
    assert values['top1_accuracy'].value==1
    assert 'arc_ids' not in repr(evaluated)
    assert evaluate_completed_prediction(trained,replace(scoring,mode='evaluator')).status=='unavailable'
    path.unlink();path.symlink_to(tmp_path/'unrelated.route')
    assert evaluate_completed_prediction(trained,scoring).status=='unavailable'
