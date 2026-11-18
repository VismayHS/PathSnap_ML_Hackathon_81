"""Synthetic integrity fixtures only; these do not represent model experiments."""
import json
import pytest
from src.models.collect import collect
from src.models.provenance import digest_json,file_digest


def fixture(tmp_path,monkeypatch):
    monkeypatch.setattr('src.models.collect.revision_source_fingerprint',lambda revision:'code')
    task={'task_id':'example-cv-0','model':'example','kind':'cv','fold':0,'laptop':'laptop-1'}
    manifest={'identity':{'data':'expected'},'tasks':[task],'models':[]}
    path=tmp_path/'manifest.json';path.write_text(json.dumps(manifest))
    def run(name,source='a'*40,identity=None,job=False):
        root=tmp_path/name;root.mkdir()
        meta={'schema':'pathsnap-training-worker/1','source_git_sha':source,'identity':identity or manifest['identity'],
              'source_code_sha256':'code','task_manifest_sha256':digest_json(manifest)}
        (root/'metadata.json').write_text(json.dumps(meta))
        if job:
            result={'task':task,'status':'complete','source_git_sha':source,'source_code_sha256':'code','identity':manifest['identity']}
            (root/'job-example-cv-0.json').write_text(json.dumps(result))
        files={p.name:file_digest(p) for p in root.iterdir()}
        (root/'summary.json').write_text(json.dumps({'file_sha256':files}))
        return root
    return path,run


def test_refuses_wrong_source_or_input_fingerprint(tmp_path,monkeypatch):
    manifest,make=fixture(tmp_path,monkeypatch)
    with pytest.raises(ValueError,match='source/schema'):
        collect([make('wrong-source',source='b'*40)],tmp_path/'out','a'*40,manifest)
    with pytest.raises(ValueError,match='fingerprint|manifest'):
        collect([make('wrong-cache',identity={'data':'different'})],tmp_path/'out','a'*40,manifest)


def test_refuses_unsealed_extra_files_and_missing_tasks(tmp_path,monkeypatch):
    manifest,make=fixture(tmp_path,monkeypatch);root=make('extra')
    (root/'unexpected.json').write_text('{}')
    with pytest.raises(ValueError,match='unsealed'):
        collect([root],tmp_path/'out','a'*40,manifest)
    with pytest.raises(ValueError,match='Missing successful tasks'):
        collect([make('missing')],tmp_path/'out','a'*40,manifest)


def test_refuses_duplicate_successes_instead_of_best_score_selection(tmp_path,monkeypatch):
    manifest,make=fixture(tmp_path,monkeypatch)
    with pytest.raises(ValueError,match='Duplicate successful task'):
        collect([make('first',job=True),make('second',job=True)],tmp_path/'out','a'*40,manifest)
