"""Portable training provenance: numeric cache identity, code identity and hardware."""
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import numpy as np


def digest_json(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def array_digest(array):
    array = np.asarray(array)
    if array.dtype.hasobject:
        raise ValueError('Object arrays cannot enter portable training caches')
    array = array.astype(array.dtype.newbyteorder('<'), copy=False)
    h = hashlib.sha256(json.dumps({'dtype':array.dtype.str,'shape':array.shape},sort_keys=True).encode())
    h.update(array.tobytes(order='C'))
    return h.hexdigest()


def cache_identity(index, sampling, trips):
    arrays = {f'{partition}/{tid}': {name:array_digest(values) for name,values in sorted(data.items())}
              for (partition,tid),data in sorted(trips.items())}
    return dict(data_fingerprint=index['data_fingerprint'], feature_version=index['feature_version'],
                feature_names=index['feature_names'], config_sha256=index['config_sha256'],
                split_sha256=digest_json(index['folds']), sampling_sha256=digest_json(sampling),
                cache_content_sha256=digest_json(arrays))


def raw_development_fingerprint(root):
    hashes = {}
    for partition in ['train','student_test']:
        for p in sorted((root/partition).iterdir()):
            if not p.is_dir():
                continue
            for suffix in ['track','nodes','arcs','route']:
                path = p/f'{p.name}.{suffix}'
                hashes[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return digest_json(hashes)


def revision_source_fingerprint(revision, compare_worktree=False):
    """Permit result-only commits after a kit revision; reject any changed scientific file."""
    if len(revision) != 40 or any(c not in '0123456789abcdef' for c in revision):
        raise ValueError('kit-source must be the complete common Git SHA')
    paths = subprocess.check_output(['git','ls-tree','-r','--name-only',revision,'--',
       'src/data_processing','src/features','src/evaluation','src/models','src/hmm','src/hpo',
       'src/__init__.py','src/pipeline.py','src/contracts.py','configs/ml','configs/hmm','contracts',
       'requirements.txt','requirements.lock.txt'],text=True).splitlines()
    if 'src/models/worker.py' not in paths or 'configs/ml/shared-inputs.json' not in paths:
        raise ValueError('The selected Git revision predates the distributed training kit')
    hashes = {}
    for path in paths:
        expected = subprocess.check_output(['git','show',f'{revision}:{path}']).replace(b'\r\n',b'\n')
        if compare_worktree and Path(path).read_bytes().replace(b'\r\n',b'\n') != expected:
            raise ValueError(f'Scientific source differs from kit revision: {path}')
        hashes[path] = hashlib.sha256(expected).hexdigest()
    return digest_json(hashes)


def hardware(threads):
    return dict(platform=platform.platform(), python=platform.python_version(), machine=platform.machine(),
                processor=platform.processor(), logical_cpus=os.cpu_count(), threads=threads,
                packages={p:importlib.metadata.version(p) for p in ['numpy','scipy','scikit-learn','pyproj','joblib']})


def verify_kit_source(revision):
    return revision_source_fingerprint(revision, compare_worktree=True)


def file_digest(path):
    data=Path(path).read_bytes()
    if Path(path).suffix in ('.json','.jsonl'):
        data=data.replace(b'\r\n',b'\n')
    return hashlib.sha256(data).hexdigest()
