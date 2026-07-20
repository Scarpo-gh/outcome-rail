// SPDX-License-Identifier: MIT
pragma solidity ^0.8.30;

import "../AnalysisJobEscrow.sol";

interface Vm {
    function deal(address account, uint256 newBalance) external;
    function prank(address msgSender) external;
    function warp(uint256 newTimestamp) external;
}

contract AnalysisJobEscrowTest {
    Vm private constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));

    AnalysisJobEscrow private escrow;
    address private constant REQUESTER = address(0xA11CE);
    address private constant PROVIDER = address(0xB0B);
    uint256 private constant AMOUNT = 1 ether;

    function setUp() public {
        escrow = new AnalysisJobEscrow();
        vm.deal(REQUESTER, 10 ether);
        vm.warp(1_000_000);
    }

    function testCreateJobBindsCanonicalRequestHash() public {
        bytes32 requestHash = keccak256("market/outcome/action/size/policy");
        uint64 deadline = uint64(block.timestamp + 5 minutes);

        vm.prank(REQUESTER);
        (bool ok,) = address(escrow).call{value: AMOUNT}(
            abi.encodeWithSignature("createJob(address,bytes32,uint64)", PROVIDER, requestHash, deadline)
        );

        _assertTrue(ok, "createJob must bind a canonical request hash at funding time");
        AnalysisJobEscrow.Job memory job = escrow.getJob(0);
        _assertEq(job.requestHash, requestHash, "stored request hash must match funded request");
    }

    function testCreateJobRejectsEmptyRequestHash() public {
        uint64 deadline = uint64(block.timestamp + 5 minutes);

        vm.prank(REQUESTER);
        (bool ok,) = address(escrow).call{value: AMOUNT}(
            abi.encodeWithSignature("createJob(address,bytes32,uint64)", PROVIDER, bytes32(0), deadline)
        );

        _assertTrue(!ok, "createJob must reject an empty request hash");
    }

    function testProviderSettlesFundedJobWithReceiptHash() public {
        bytes32 requestHash = keccak256("canonical-request");
        bytes32 receiptHash = keccak256("outcomerail-canonical-receipt");
        uint64 deadline = uint64(block.timestamp + 5 minutes);

        vm.prank(REQUESTER);
        escrow.createJob{value: AMOUNT}(PROVIDER, requestHash, deadline);

        uint256 providerBalanceBefore = PROVIDER.balance;
        vm.prank(PROVIDER);
        escrow.settleJob(0, receiptHash);

        AnalysisJobEscrow.Job memory job = escrow.getJob(0);
        _assertEq(job.receiptHash, receiptHash, "settlement must preserve the canonical receipt hash");
        _assertEq(uint256(job.status), uint256(AnalysisJobEscrow.JobStatus.Settled), "job must be settled");
        _assertEq(PROVIDER.balance, providerBalanceBefore + AMOUNT, "provider must receive escrowed funds");
    }

    function testRequesterRefundsOnlyAfterDeadline() public {
        bytes32 requestHash = keccak256("refund-request");
        uint64 deadline = uint64(block.timestamp + 5 minutes);

        vm.prank(REQUESTER);
        escrow.createJob{value: AMOUNT}(PROVIDER, requestHash, deadline);

        uint256 requesterBalanceBefore = REQUESTER.balance;
        vm.warp(uint256(deadline) + 1);
        vm.prank(REQUESTER);
        escrow.refundExpiredJob(0);

        AnalysisJobEscrow.Job memory job = escrow.getJob(0);
        _assertEq(uint256(job.status), uint256(AnalysisJobEscrow.JobStatus.Refunded), "expired job must be refunded");
        _assertEq(REQUESTER.balance, requesterBalanceBefore + AMOUNT, "requester must recover escrowed funds");
    }

    function _assertEq(bytes32 actual, bytes32 expected, string memory message) private pure {
        if (actual != expected) revert(message);
    }

    function _assertEq(uint256 actual, uint256 expected, string memory message) private pure {
        if (actual != expected) revert(message);
    }

    function _assertTrue(bool condition, string memory message) private pure {
        if (!condition) revert(message);
    }
}
