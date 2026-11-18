"""Isolated post-prediction scoring facade. Availability is honest at M1."""
from src.contracts import EvaluationSummary
from src.evaluation.alignment import POLICY_ID


def evaluate_completed_prediction(prediction, scoring_settings):
    reason = ('Diagnostic output is for integration; no trained-model benchmark is available'
              if prediction.model_kind == 'diagnostic' else
              'Provisional alignment scorer is not yet validated for production scoring')
    return EvaluationSummary('unavailable', POLICY_ID, 'provisional', unavailable_reason=reason)
