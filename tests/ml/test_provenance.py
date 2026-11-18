import numpy as np
from src.models.provenance import array_digest, digest_json


def test_cache_array_digest_is_endian_independent_and_content_sensitive():
    little = np.array([1.,2.,3.],dtype='<f8')
    big = little.astype('>f8')
    assert array_digest(little) == array_digest(big)
    assert array_digest(little) != array_digest(little+1)
    assert array_digest(little) != array_digest(little.reshape(1,3))
    assert digest_json({'b':2,'a':1}) == digest_json({'a':1,'b':2})


def test_returned_json_hash_survives_git_crlf_but_binary_is_exact(tmp_path):
    from src.models.provenance import file_digest
    a=tmp_path/'a.json';b=tmp_path/'b.json'
    a.write_bytes(b'{"x":1}\n');b.write_bytes(b'{"x":1}\r\n')
    assert file_digest(a)==file_digest(b)
    a=tmp_path/'a.joblib';b=tmp_path/'b.joblib'
    a.write_bytes(b'x\n');b.write_bytes(b'x\r\n')
    assert file_digest(a)!=file_digest(b)
