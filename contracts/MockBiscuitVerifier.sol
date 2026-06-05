// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

contract MockBiscuitVerifier {
    function verifySignature(bytes calldata token, bytes calldata rootPubKey) external pure returns (bool) {
        // In tests we'll pass any token and rootPubKey; return true for non-empty
        return token.length > 0 && rootPubKey.length > 0;
    }

    function scopePermits(bytes calldata token, address target, bytes calldata data) external pure returns (bool) {
        // Allow everything in mock
        return true;
    }
}
