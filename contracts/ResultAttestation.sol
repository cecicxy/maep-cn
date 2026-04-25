// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

contract ResultAttestation {
    struct Attestation {
        address provider;
        bytes32 resultHash;
        uint256 timestamp;
        bool disputed;
    }

    mapping(bytes32 => Attestation) public attestations;

    event ResultAttested(bytes32 indexed taskId, address provider, bytes32 resultHash);
    event ResultDisputed(bytes32 indexed taskId, address disputedBy);

    function attest(bytes32 taskId, bytes32 resultHash) external {
        require(attestations[taskId].timestamp == 0, "Already attested");
        attestations[taskId] = Attestation(msg.sender, resultHash, block.timestamp, false);
        emit ResultAttested(taskId, msg.sender, resultHash);
    }

    function dispute(bytes32 taskId) external {
        require(attestations[taskId].timestamp != 0, "No attestation");
        require(!attestations[taskId].disputed, "Already disputed");
        attestations[taskId].disputed = true;
        emit ResultDisputed(taskId, msg.sender);
    }

    function getAttestation(bytes32 taskId) external view returns (Attestation memory) {
        return attestations[taskId];
    }
}
