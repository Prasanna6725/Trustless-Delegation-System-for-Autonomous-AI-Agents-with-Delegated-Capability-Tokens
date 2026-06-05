"""Helpers to commit a TLSNotary proof hash on-chain.

Functions:
- commit_proof_hash(proof: dict, agent_private_key_hex: str, registry_address: str, web3_provider: str) -> tx_hash

This function computes the proof hash, builds and sends a transaction to the
LineageRegistry.contract's `commitProof(address agent, bytes32 proofHash)` method.
It requires the `web3` Python package and the registry ABI (included locally).
"""
from __future__ import annotations
import hashlib
import json
from web3 import Web3
from eth_account import Account

# Minimal ABI for LineageRegistry commitProof
_REGISTRY_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "agent", "type": "address"},
            {"internalType": "bytes32", "name": "proofHash", "type": "bytes32"}
        ],
        "name": "commitProof",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]


def _proof_hash_hex(proof: dict) -> str:
    # canonicalize proof dict into bytes and hash
    s = json.dumps(proof, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(s.encode()).hexdigest()


def commit_proof_hash(proof: dict, agent_private_key_hex: str, registry_address: str, web3_provider: str) -> str:
    """
    Compute proof hash and commit it on-chain. Returns transaction hash string.
    """
    w3 = Web3(Web3.HTTPProvider(web3_provider))
    acct = Account.from_key(agent_private_key_hex)
    agent_addr = acct.address

    proof_hash_hex = _proof_hash_hex(proof)
    proof_hash_bytes32 = Web3.toBytes(hexstr=proof_hash_hex)

    registry = w3.eth.contract(address=Web3.to_checksum_address(registry_address), abi=_REGISTRY_ABI)

    nonce = w3.eth.get_transaction_count(agent_addr)
    txn = registry.functions.commitProof(agent_addr, proof_hash_bytes32).build_transaction({
        'from': agent_addr,
        'nonce': nonce,
        'gas': 200000,
        'gasPrice': w3.eth.gas_price,
    })

    signed = acct.sign_transaction(txn)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    return w3.to_hex(tx_hash)
