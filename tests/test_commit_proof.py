import pytest
import os

from backend import commit_proof


def test_proof_hash_consistency():
    proof = {'url':'https://api','method':'GET','status':200,'body_hash':'abc','signature':'sig'}
    h = commit_proof._proof_hash_hex(proof)
    h2 = commit_proof._proof_hash_hex(proof)
    assert h == h2


def test_commit_proof_skip_without_provider():
    # This test only verifies that function raises a clear error when no provider
    proof = {'a':1}
    with pytest.raises(Exception):
        commit_proof.commit_proof_hash(proof, '0x0'*32, '0x0000000000000000000000000000000000000000', os.environ.get('WEB3_PROVIDER_URL',''))
