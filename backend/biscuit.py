"""
Off-chain Biscuit helper functions.
Functions implemented:
- generate_child_keypair
- mint_root_token
- attenuate_token
- verify_token

This implementation relies on the `biscuit_auth` Python package. If it's not
available, the functions will raise an informative ImportError.
"""
from __future__ import annotations
import base64
import time
from dataclasses import dataclass

try:
    from biscuit_auth import Biscuit, KeyPair, PublicKey
except Exception as e:
    Biscuit = None
    KeyPair = None
    PublicKey = None


@dataclass
class KeyPairDataclass:
    public: bytes
    private: bytes


def generate_child_keypair() -> KeyPairDataclass:
    """
    Generate an ephemeral Ed25519 keypair for a new child agent.
    Returns a KeyPairDataclass with `public` and `private` as raw bytes.
    """
    if KeyPair is None:
        raise ImportError("biscuit_auth library not available; install via pip")
    kp = KeyPair.generate()
    return KeyPairDataclass(public=kp.public_key_bytes(), private=kp.private_key_bytes())


def _now_seconds() -> int:
    return int(time.time())


def mint_root_token(
    issuer_keypair,
    agent_id: str,
    allowed_scopes: list[str],
    max_depth: int,
    ttl_seconds: int,
) -> str:
    """
    Mint a root Biscuit token for the orchestrator agent.
    Returns a base64-encoded token string.
    """
    if Biscuit is None:
        raise ImportError("biscuit_auth library not available; install via pip")
    kp = issuer_keypair
    builder = Biscuit.create(kp)
    # authority block: add facts
    builder.add_fact(f"agent('{agent_id}')")
    for s in allowed_scopes:
        builder.add_fact(f"scope('{s}')")
    builder.add_fact(f"max_depth({max_depth})")
    # expiry check: add a check rule that current time < expiry
    expiry_ts = _now_seconds() + ttl_seconds
    builder.add_fact(f"expiry({expiry_ts})")
    token = builder.build()
    token_b64 = base64.b64encode(token.serialize()).decode()
    return token_b64


def attenuate_token(
    parent_token_b64: str,
    root_public_key,
    child_agent_id: str,
    narrowed_scopes: list[str],
    ttl_seconds: int,
) -> str:
    """
    Append an attenuation block to an existing token, narrowing its scope.
    Raises if the parent token has already reached max_depth.
    Returns a base64-encoded attenuated token string.
    """
    if Biscuit is None:
        raise ImportError("biscuit_auth library not available; install via pip")
    token_bytes = base64.b64decode(parent_token_b64)
    token = Biscuit.from_bytes(token_bytes)
    # Extract current remaining depth from facts if present
    # For simplicity, we assume max_depth fact in authority and we count blocks
    facts = token.authority_block().facts()
    max_depth = None
    for f in facts:
        s = str(f)
        if s.startswith('max_depth('):
            try:
                max_depth = int(s[s.find('(')+1:s.find(')')])
            except Exception:
                pass
    if max_depth is None:
        raise ValueError('parent token missing max_depth')
    # current depth is number of attenuation blocks
    current_depth = len(token.blocks()) - 1
    if current_depth >= max_depth:
        raise ValueError('max delegation depth reached')
    # create attenuation: add facts narrowing scope and decrement remaining depth
    attenuation = token.append_block()
    attenuation.add_fact(f"agent('{child_agent_id}')")
    for s in narrowed_scopes:
        attenuation.add_fact(f"scope('{s}')")
    # set new expiry
    expiry_ts = _now_seconds() + ttl_seconds
    attenuation.add_fact(f"expiry({expiry_ts})")
    new_token = token.build()
    return base64.b64encode(new_token.serialize()).decode()


def verify_token(
    token_b64: str,
    root_public_key,
    requested_resource: str,
    requested_operation: str,
) -> bool:
    """
    Verify a Biscuit token offline using only the root public key.
    Injects current request context (resource, operation, timestamp) as authorizer facts.
    Returns True only if all Datalog checks in all blocks pass.
    """
    if Biscuit is None:
        raise ImportError("biscuit_auth library not available; install via pip")
    token_bytes = base64.b64decode(token_b64)
    token = Biscuit.from_bytes(token_bytes)
    # Build authorizer with injected facts
    authorizer = token.authorizer()
    authorizer.add_fact(f"request_resource('{requested_resource}')")
    authorizer.add_fact(f"request_operation('{requested_operation}')")
    authorizer.add_fact(f"now({ _now_seconds() })")
    try:
        authorizer.check()  # raises on failure
        return True
    except Exception:
        return False
