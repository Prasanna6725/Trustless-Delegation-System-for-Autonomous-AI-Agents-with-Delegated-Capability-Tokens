// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

contract LineageRegistry {
    uint8 public constant MAX_DEPTH = 8;

    struct Node {
        address parent;
        bool registered;
        bool revoked;
        uint8 depth;
    }

    mapping(address => Node) internal nodes;
    mapping(address => bytes32) internal committedProofs;

    event Registered(address indexed agent, address indexed parent, uint8 depth);
    event Revoked(address indexed agent, address indexed revokedBy);
    event ProofCommitted(address indexed agent, bytes32 proofHash);

    constructor(address root) {
        // register root
        nodes[root] = Node({parent: address(0), registered: true, revoked: false, depth: 0});
        emit Registered(root, address(0), 0);
    }

    function register(address agent, address parent) external {
        require(agent != address(0), "agent zero");
        require(parent != address(0), "parent zero");
        require(!nodes[agent].registered, "agent already registered");
        require(nodes[parent].registered, "parent not registered");
        uint8 parentDepth = nodes[parent].depth;
        require(parentDepth < MAX_DEPTH, "parent at max depth");
        uint8 newDepth = parentDepth + 1;
        require(newDepth <= MAX_DEPTH, "would exceed MAX_DEPTH");
        nodes[agent] = Node({parent: parent, registered: true, revoked: false, depth: newDepth});
        emit Registered(agent, parent, newDepth);
    }

    function revoke(address agent) external {
        require(nodes[agent].registered, "agent not registered");
        address caller = msg.sender;
        require(caller == agent || nodes[agent].parent == caller, "not authorized to revoke");
        nodes[agent].revoked = true;
        emit Revoked(agent, caller);
    }

    function commitProof(address agent, bytes32 proofHash) external {
        require(nodes[agent].registered, "agent not registered");
        require(msg.sender == agent, "only agent can commit proof");
        committedProofs[agent] = proofHash;
        emit ProofCommitted(agent, proofHash);
    }

    function getCommittedProof(address agent) external view returns (bytes32) {
        return committedProofs[agent];
    }

    function isActive(address agent) public view returns (bool) {
        if (!nodes[agent].registered) return false;
        address cur = agent;
        for (uint8 i = 0; i <= MAX_DEPTH; i++) {
            if (cur == address(0)) break;
            Node memory n = nodes[cur];
            if (n.revoked) return false;
            if (n.parent == address(0)) break;
            cur = n.parent;
        }
        return true;
    }

    function depthOf(address agent) public view returns (uint8) {
        require(nodes[agent].registered, "agent not registered");
        return nodes[agent].depth;
    }
}
