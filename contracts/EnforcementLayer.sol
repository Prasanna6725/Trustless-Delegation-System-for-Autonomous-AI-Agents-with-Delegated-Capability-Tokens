// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

interface ILineageRegistry {
    function isActive(address agent) external view returns (bool);
    function getCommittedProof(address agent) external view returns (bytes32);
}

interface ITrustScorer {
    function onSuccess(address agent) external;
    function onViolation(address agent) external;
}

// External Biscuit verifier interface (off-chain heavy lifting delegated to an on-chain verifier/oracle)
interface IBiscuitVerifier {
    function verifySignature(bytes calldata token, bytes calldata rootPubKey) external view returns (bool);
    function scopePermits(bytes calldata token, address target, bytes calldata data) external view returns (bool);
}

interface IDelegationManager {
    struct Action { address target; uint256 value; bytes data; }
    function redeemDelegation(bytes calldata delegation, Action calldata action) external returns (bytes memory);
}

contract EnforcementLayer is IDelegationManager {
    ILineageRegistry public lineage;
    ITrustScorer public scorer;
    IBiscuitVerifier public biscuitVerifier;

    error LineageInvalid();
    error TokenInvalid();
    error ScopeDenied();
    error ProofMissingOrMismatch();

    event DelegationRedeemed(address indexed agent, address indexed caller);

    constructor(address _lineage, address _scorer, address _biscuitVerifier) {
        lineage = ILineageRegistry(_lineage);
        scorer = ITrustScorer(_scorer);
        biscuitVerifier = IBiscuitVerifier(_biscuitVerifier);
    }

    // delegation ABI: (bytes token, address agent, bytes32 proofHash, bytes rootPubKey)
    function redeemDelegation(bytes calldata delegation, Action calldata action) external override returns (bytes memory) {
        (bytes memory token, address agent, bytes32 proofHash, bytes memory rootPubKey) = abi.decode(delegation, (bytes, address, bytes32, bytes));

        // 1) Lineage validity
        if (!lineage.isActive(agent)) revert LineageInvalid();

        // 2) Token signature verification
        if (!biscuitVerifier.verifySignature(token, rootPubKey)) revert TokenInvalid();

        // 3) Scope validation
        if (!biscuitVerifier.scopePermits(token, action.target, action.data)) revert ScopeDenied();

        // 4) TLSNotary attestation: check that agent previously committed the proof hash
        bytes32 committed = lineage.getCommittedProof(agent);
        if (committed == bytes32(0) || committed != proofHash) revert ProofMissingOrMismatch();

        // All checks passed. Emit event and notify scorer of success.
        emit DelegationRedeemed(agent, msg.sender);
        scorer.onSuccess(agent);

        return "";
    }
}
