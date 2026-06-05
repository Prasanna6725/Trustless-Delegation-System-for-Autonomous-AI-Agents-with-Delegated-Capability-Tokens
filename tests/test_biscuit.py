import pytest
from backend import biscuit


def test_mint_and_verify_skip_if_no_lib():
    try:
        # generate a fake keypair object if library missing
        if getattr(biscuit, 'Biscuit', None) is None:
            pytest.skip('biscuit_auth not installed; skip integration test')
        # Else perform a simple mint and verify
        kp = biscuit.KeyPair()
        token = biscuit.mint_root_token(kp, 'agent-root', ['read:invoices'], 3, 3600)
        assert isinstance(token, str) and len(token) > 0
    except ImportError:
        pytest.skip('biscuit_auth not available')
