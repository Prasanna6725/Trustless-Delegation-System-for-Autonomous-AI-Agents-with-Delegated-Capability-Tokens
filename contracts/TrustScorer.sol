// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

contract TrustScorer {
    address public enforcer;

    mapping(address => uint256) internal scores; // scaled by 1000

    uint256 public constant SCALE = 1000;
    uint256 public constant VIOLATION_SLASH = 500; // 0.5 points scaled

    event ScoreUpdated(address indexed agent, uint256 oldScore, uint256 newScore);

    modifier onlyEnforcer() {
        require(msg.sender == enforcer, "only enforcer");
        _;
    }

    constructor(address _enforcer) {
        enforcer = _enforcer;
    }

    function onSuccess(address agent) external onlyEnforcer {
        uint256 old = scores[agent];
        // logarithmic growth approximation: delta = SCALE * log2(old/ SCALE + 1)
        uint256 base = old / SCALE + 1;
        uint256 delta = _ilog2(base) * SCALE;
        if (delta == 0) {
            delta = 100; // small base increment
        }
        uint256 nw = old + delta;
        scores[agent] = nw;
        emit ScoreUpdated(agent, old, nw);
    }

    function onViolation(address agent) external onlyEnforcer {
        uint256 old = scores[agent];
        if (old <= VIOLATION_SLASH) {
            scores[agent] = 0;
        } else {
            scores[agent] = old - VIOLATION_SLASH;
        }
        emit ScoreUpdated(agent, old, scores[agent]);
    }

    function scoreOf(address agent) external view returns (uint256) {
        return scores[agent];
    }

    function maxDelegationDepth(address agent) external view returns (uint8) {
        uint256 s = scores[agent];
        if (s < 500 * SCALE) return 1;
        if (s < 1000 * SCALE) return 3;
        if (s < 2000 * SCALE) return 5;
        return 8;
    }

    function _ilog2(uint256 x) internal pure returns (uint256) {
        uint256 res = 0;
        while (x > 1) {
            x = x >> 1;
            res += 1;
        }
        return res;
    }
}
