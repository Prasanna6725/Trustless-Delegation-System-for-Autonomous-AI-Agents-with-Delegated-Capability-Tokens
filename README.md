# Trustless Delegation System for Autonomous AI Agents

Prototype repository implementing an end-to-end delegation system using off-chain Biscuit tokens and on-chain lineage & scoring.

This initial scaffold includes:
- Python off-chain Biscuit helper module (`backend/biscuit.py`)
- Solidity `LineageRegistry` contract (`contracts/LineageRegistry.sol`)
- Solidity `TrustScorer` contract (`contracts/TrustScorer.sol`)
- Docker compose and example env
- Tests scaffolding

Next steps:
- Implement EnforcementLayer contract and TLSNotary client
- Add deployment scripts and CI
