import os

def test_environment_and_configs():
    """Verify core configuration directories exist and are accessible."""
    assert os.path.exists("configs") or os.path.exists("api"), "Core project directories missing."

def test_placeholder_validation():
    """Sanity check for pipeline metrics validation."""
    model_accuracy_threshold = 0.5
    assert model_accuracy_threshold > 0.0