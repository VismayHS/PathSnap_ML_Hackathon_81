import numpy as np
from src.models.experiments import fit_model


def test_actual_training_helper_fits_preprocessing_only_to_training_ids():
    def trip(values):
        return {'X':np.repeat(np.array(values,dtype=np.float32)[:,None],9,axis=1),
                'y':np.array([0,1]),'labels':np.array([1,2]),'row_observation':np.array([0,1])}
    data={('train','train-id'):trip([0,2]),('train','held-out-id'):trip([100,200])}
    model,record=fit_model('logistic_regression',data,['train-id'],{'train-id':[0,1],'held-out-id':[0,1]})
    assert np.all(model.named_steps['scaler'].mean_==1)
    assert np.all(model.named_steps['imputer'].statistics_==1)
    assert record['fit_rows']==2
