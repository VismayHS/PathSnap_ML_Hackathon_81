"""Reference access isolated from prediction; offline development and post-hoc scoring only."""
from pathlib import Path
import numpy as np
from src.data_processing.raw import table


def read_reference(directory: Path, arc_count: int) -> np.ndarray:
    """Never called by prediction modules. Preserve traversal occurrences, including repeats."""
    values = table(directory / f"{directory.name}.route", 1).ravel()
    if (not np.isfinite(values).all() or not np.equal(values, np.floor(values)).all()
            or (values < 0).any() or (values >= arc_count).any()):
        raise ValueError("Invalid reference arc IDs")
    return values.astype(np.int64)
