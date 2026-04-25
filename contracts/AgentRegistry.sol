// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

contract AgentRegistry {
    struct AgentInfo {
        string capabilities;
        uint256 reputation;
        uint256 stake;
        bool active;
    }

    mapping(address => AgentInfo) public agents;
    uint256 public minStake;
    address public owner;

    event AgentRegistered(address indexed agent, string capabilities);
    event AgentDeregistered(address indexed agent);
    event ReputationUpdated(address indexed agent, uint256 newReputation);

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    constructor(uint256 _minStake) {
        minStake = _minStake;
        owner = msg.sender;
    }

    function register(string calldata capabilities) external payable {
        require(msg.value >= minStake, "Insufficient stake");
        require(!agents[msg.sender].active, "Already registered");
        agents[msg.sender] = AgentInfo(capabilities, 100, msg.value, true);
        emit AgentRegistered(msg.sender, capabilities);
    }

    function deregister() external {
        require(agents[msg.sender].active, "Not registered");
        uint256 stake = agents[msg.sender].stake;
        agents[msg.sender].active = false;
        agents[msg.sender].stake = 0;
        payable(msg.sender).transfer(stake);
        emit AgentDeregistered(msg.sender);
    }

    function updateReputation(address agent, uint256 newReputation) external onlyOwner {
        require(agents[agent].active, "Agent not active");
        agents[agent].reputation = newReputation;
        emit ReputationUpdated(agent, newReputation);
    }

    function getAgent(address agent) external view returns (AgentInfo memory) {
        return agents[agent];
    }
}
