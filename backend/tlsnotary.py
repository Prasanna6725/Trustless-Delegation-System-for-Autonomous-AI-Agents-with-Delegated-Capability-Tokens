"""TLSNotary client helpers.

This module implements:
- init_tlsnotary_session(notary_url) -> session_id
- execute_notarized_request(session_id, target_url, method, headers, body) -> proof dict

The implementation assumes a simple HTTP JSON API exposed by a TLSNotary service.
For testing, the functions are written to be easily mockable.
"""
from __future__ import annotations
import requests
import hashlib
from typing import Optional


def init_tlsnotary_session(notary_url: str) -> str:
    """
    Initialize a TLSNotary session with the notary service.
    Returns a session_id string.
    """
    resp = requests.post(f"{notary_url.rstrip('/')}/init")
    resp.raise_for_status()
    data = resp.json()
    return data.get('session_id')


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def execute_notarized_request(
    session_id: str,
    target_url: str,
    method: str,
    headers: Optional[dict] = None,
    body: Optional[bytes] = None,
) -> dict:
    """
    Execute an HTTPS request via the TLSNotary notary.
    Returns a proof dict containing: url, method, status, body_hash, signature
    """
    headers = headers or {}
    payload = {
        'session_id': session_id,
        'url': target_url,
        'method': method,
        'headers': headers,
    }
    if body is not None:
        payload['body_hash'] = _sha256_hex(body)

    resp = requests.post(f"/notary/execute" , json=payload) if notary_local_check() else requests.post(f"{get_notary_base()}/execute", json=payload)
    resp.raise_for_status()
    proof = resp.json()
    # validate shape
    expected_keys = {'url', 'method', 'status', 'body_hash', 'signature'}
    if not expected_keys.issubset(set(proof.keys())):
        raise ValueError('invalid proof format from notary')
    return proof


def notary_local_check() -> bool:
    # placeholder for environment-specific routing; default False
    return False


def get_notary_base() -> str:
    # In real deployment this would be configurable; fallback to env or localhost
    return "http://localhost:9000/notary"
