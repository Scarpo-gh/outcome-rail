// SPDX-License-Identifier: MIT
pragma solidity ^0.8.30;

/// @title AnalysisJobEscrow
/// @notice Bounded test-USDC job lifecycle for OutcomeRail on Arc Testnet.
/// @dev Arc Testnet uses USDC as its native gas currency. `msg.value` is test-USDC.
contract AnalysisJobEscrow {
    enum JobStatus {
        None,
        Funded,
        Settled,
        Refunded
    }

    struct Job {
        address requester;
        address provider;
        bytes32 requestHash;
        uint256 amount;
        uint64 deadline;
        bytes32 receiptHash;
        JobStatus status;
    }

    error InvalidProvider();
    error InvalidAmount();
    error InvalidDeadline();
    error EmptyRequestHash();
    error UnknownJob();
    error Unauthorized();
    error InvalidStatus();
    error EmptyReceiptHash();
    error TransferFailed();

    event JobCreated(
        uint256 indexed jobId,
        address indexed requester,
        address indexed provider,
        bytes32 requestHash,
        uint256 amount,
        uint64 deadline
    );
    event JobSettled(uint256 indexed jobId, bytes32 indexed receiptHash, uint256 amount);
    event JobRefunded(uint256 indexed jobId, uint256 amount);

    uint256 public nextJobId;
    mapping(uint256 => Job) private jobs;

    function createJob(address provider, bytes32 requestHash, uint64 deadline) external payable returns (uint256 jobId) {
        if (provider == address(0)) revert InvalidProvider();
        if (requestHash == bytes32(0)) revert EmptyRequestHash();
        if (msg.value == 0) revert InvalidAmount();
        if (deadline <= block.timestamp) revert InvalidDeadline();

        jobId = nextJobId;
        nextJobId += 1;
        jobs[jobId] = Job({
            requester: msg.sender,
            provider: provider,
            requestHash: requestHash,
            amount: msg.value,
            deadline: deadline,
            receiptHash: bytes32(0),
            status: JobStatus.Funded
        });
        emit JobCreated(jobId, msg.sender, provider, requestHash, msg.value, deadline);
    }

    /// @notice Provider records the canonical receipt hash and receives the funded test-USDC.
    function settleJob(uint256 jobId, bytes32 receiptHash) external {
        Job storage job = _fundedJob(jobId);
        if (msg.sender != job.provider) revert Unauthorized();
        if (block.timestamp > job.deadline) revert InvalidDeadline();
        if (receiptHash == bytes32(0)) revert EmptyReceiptHash();

        uint256 amount = job.amount;
        job.receiptHash = receiptHash;
        job.status = JobStatus.Settled;
        _send(job.provider, amount);
        emit JobSettled(jobId, receiptHash, amount);
    }

    /// @notice Requester recovers test-USDC only when no settlement occurred before expiry.
    function refundExpiredJob(uint256 jobId) external {
        Job storage job = _fundedJob(jobId);
        if (msg.sender != job.requester) revert Unauthorized();
        if (block.timestamp <= job.deadline) revert InvalidDeadline();

        uint256 amount = job.amount;
        job.status = JobStatus.Refunded;
        _send(job.requester, amount);
        emit JobRefunded(jobId, amount);
    }

    function getJob(uint256 jobId) external view returns (Job memory) {
        return jobs[jobId];
    }

    function _fundedJob(uint256 jobId) private view returns (Job storage job) {
        job = jobs[jobId];
        if (job.status == JobStatus.None) revert UnknownJob();
        if (job.status != JobStatus.Funded) revert InvalidStatus();
    }

    function _send(address recipient, uint256 amount) private {
        (bool sent,) = recipient.call{value: amount}("");
        if (!sent) revert TransferFailed();
    }
}
