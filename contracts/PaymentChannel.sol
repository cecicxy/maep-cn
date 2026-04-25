// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

contract PaymentChannel {
    struct Task {
        address requester;
        address provider;
        uint256 amount;
        uint256 deadline;
        bool settled;
    }

    mapping(bytes32 => Task) public tasks;
    address public auditor;

    event PaymentLocked(bytes32 indexed taskId, address requester, address provider, uint256 amount);
    event PaymentReleased(bytes32 indexed taskId, address provider, uint256 amount);
    event PaymentRefunded(bytes32 indexed taskId, address requester, uint256 amount);

    constructor(address _auditor) {
        auditor = _auditor;
    }

    function lock(bytes32 taskId, address provider, uint256 deadline) external payable {
        require(tasks[taskId].amount == 0, "Task already exists");
        require(msg.value > 0, "No payment");
        require(deadline > block.timestamp, "Deadline in past");
        tasks[taskId] = Task(msg.sender, provider, msg.value, deadline, false);
        emit PaymentLocked(taskId, msg.sender, provider, msg.value);
    }

    function release(bytes32 taskId) external {
        Task storage t = tasks[taskId];
        require(msg.sender == t.requester, "Not requester");
        require(!t.settled, "Already settled");
        t.settled = true;
        emit PaymentReleased(taskId, t.provider, t.amount);
        (bool success, ) = payable(t.provider).call{value: t.amount}("");
        require(success, "Transfer failed");
    }

    function refund(bytes32 taskId) external {
        Task storage t = tasks[taskId];
        require(msg.sender == t.requester, "Not requester");
        require(!t.settled, "Already settled");
        require(block.timestamp > t.deadline, "Deadline not passed");
        t.settled = true;
        emit PaymentRefunded(taskId, t.requester, t.amount);
        (bool success, ) = payable(t.requester).call{value: t.amount}("");
        require(success, "Transfer failed");
    }

    function forceRelease(bytes32 taskId) external {
        require(msg.sender == auditor, "Not auditor");
        Task storage t = tasks[taskId];
        require(!t.settled, "Already settled");
        t.settled = true;
        emit PaymentReleased(taskId, t.provider, t.amount);
        (bool success, ) = payable(t.provider).call{value: t.amount}("");
        require(success, "Transfer failed");
    }

    function getTask(bytes32 taskId) external view returns (Task memory) {
        return tasks[taskId];
    }
}
