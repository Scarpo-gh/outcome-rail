from decimal import Decimal
from types import SimpleNamespace

import pytest

from erc8183_execution import (
    EXECUTION_CONFIRMATION_TOKEN,
    ExecutionGuardError,
    build_execution_steps,
    execute_step,
)
from scripts.arc_erc8183_dry_run import build_erc8183_preflight
from outcomerail_engine import analyze_execution
from policy import ExecutionPolicy
from polymarket_client import normalize_book
from receipt import build_execution_receipt


def _canonical_receipt_json() -> str:
    snapshot = normalize_book({
        "asset_id": "yes-token", "timestamp": "2026-07-18T12:00:00Z", "hash": "clob-book-hash",
        "bids": [{"price": "0.49", "size": "100"}], "asks": [{"price": "0.50", "size": "75"}],
    })
    report = analyze_execution(action="BUY", bids=snapshot.bids, asks=snapshot.asks, requested_size="50")
    return build_execution_receipt(
        snapshot=snapshot, report=report, action="BUY", requested_size="50",
        observed_at="2026-07-18T12:00:01Z", policy_id="visible-depth", policy_version="1.0.0",
        policy=ExecutionPolicy(policy_id="visible-depth", version="1.0.0", max_snapshot_age_seconds=30,
                               max_spread=Decimal("0.03"), max_price_gap=Decimal("0.02")),
        market_id="123", outcome="Yes",
    ).to_json()


def _state() -> dict[str, dict[str, str]]:
    return {
        "source": {"address": "0x1111111111111111111111111111111111111111"},
        "destination": {"address": "0x2222222222222222222222222222222222222222"},
    }


class FakeRequest:
    def __init__(self, payload):
        self.payload = payload


class FakeRequestType:
    @classmethod
    def from_dict(cls, payload):
        return FakeRequest(payload)


class FakeTransactionsApi:
    def __init__(self, client):
        self.client = client
        self.created = []
        self.polls = 0

    def create_developer_transaction_contract_execution(self, request):
        self.created.append(request.payload)
        return SimpleNamespace(data=SimpleNamespace(id="00000000-0000-4000-8000-000000000001"))

    def get_transaction(self, *, id):
        self.polls += 1
        return SimpleNamespace(data=SimpleNamespace(transaction=SimpleNamespace(state="COMPLETE", tx_hash="0xabc")))


def _plan():
    return build_erc8183_preflight(
        receipt_json=_canonical_receipt_json(), state=_state(), deadline=1_800_000_000
    )


def test_build_steps_constructs_documented_circle_request_fields_for_all_lifecycle_calls():
    plan = _plan()

    steps = build_execution_steps(plan, job_a_id=7, job_b_id=8)

    assert [step.name for step in steps] == [
        "create_job_a", "set_budget_a", "approve_a", "fund_a", "submit_a", "complete_a",
        "create_job_b", "set_budget_b", "approve_b", "fund_b", "claim_refund_b",
    ]
    by_name = {step.name: step for step in steps}
    assert by_name["create_job_a"].request_fields == {
        "blockchain": "ARC-TESTNET",
        "walletAddress": _state()["source"]["address"],
        "contractAddress": plan["reference_contract"],
        "abiFunctionSignature": "createJob(address,address,uint256,string,address)",
        "abiParameters": [_state()["destination"]["address"], _state()["source"]["address"], "1800000000", "OutcomeRail receipt-backed analysis job A", "0x0000000000000000000000000000000000000000"],
        "feeLevel": "MEDIUM",
    }
    assert by_name["set_budget_a"].request_fields["walletAddress"] == _state()["destination"]["address"]
    assert by_name["set_budget_a"].request_fields["abiFunctionSignature"] == "setBudget(uint256,uint256,bytes)"
    assert by_name["set_budget_a"].request_fields["abiParameters"] == [7, "5000000", "0x"]
    assert by_name["approve_a"].request_fields["contractAddress"] == plan["usdc_contract"]
    assert by_name["approve_a"].request_fields["abiFunctionSignature"] == "approve(address,uint256)"
    assert by_name["approve_a"].request_fields["abiParameters"] == [plan["reference_contract"], "5000000"]
    assert by_name["fund_a"].request_fields["abiParameters"] == [7, "0x"]
    assert by_name["submit_a"].request_fields["abiParameters"] == [7, plan["receipt_hash_bytes32"], "0x"]
    assert by_name["complete_a"].request_fields["abiParameters"] == [7, plan["reason_hash_bytes32"], "0x"]
    assert by_name["create_job_b"].request_fields["abiParameters"][3] == "OutcomeRail refund-path analysis job B"
    assert by_name["set_budget_b"].request_fields["abiParameters"] == [8, "5000000", "0x"]
    assert by_name["approve_b"].request_fields["abiParameters"] == [plan["reference_contract"], "5000000"]
    assert by_name["fund_b"].request_fields["abiParameters"] == [8, "0x"]
    assert by_name["claim_refund_b"].request_fields["abiFunctionSignature"] == "claimRefund(uint256)"
    assert by_name["claim_refund_b"].request_fields["abiParameters"] == [8]


def test_default_guard_blocks_client_factory_and_network_for_every_step_when_execute_is_absent():
    calls = []

    def forbidden_factory():
        calls.append("client")
        raise AssertionError("client factory must not run")

    for step in build_execution_steps(_plan(), job_a_id=7, job_b_id=8):
        with pytest.raises(ExecutionGuardError, match="--execute"):
            execute_step(step, execute=False, confirmation_token=EXECUTION_CONFIRMATION_TOKEN, client_factory=forbidden_factory)

    assert calls == []


def test_default_guard_blocks_client_factory_and_network_when_confirmation_is_absent():
    step = build_execution_steps(_plan(), job_a_id=7, job_b_id=8)[0]
    calls = []

    with pytest.raises(ExecutionGuardError, match="confirmation"):
        execute_step(step, execute=True, confirmation_token=None, client_factory=lambda: calls.append("client"))

    assert calls == []


def test_guarded_execution_constructs_sdk_request_and_polls_without_printing_secret(capsys):
    step = build_execution_steps(_plan(), job_a_id=7, job_b_id=8)[0]
    api = FakeTransactionsApi(client=object())
    sdk = SimpleNamespace(
        CreateContractExecutionTransactionForDeveloperRequest=FakeRequestType,
        TransactionsApi=lambda client: api,
    )

    result = execute_step(
        step,
        execute=True,
        confirmation_token=EXECUTION_CONFIRMATION_TOKEN,
        client_factory=lambda: (object(), sdk),
        poll_interval_seconds=0,
    )

    assert api.created[0]["idempotencyKey"] == step.idempotency_key
    assert api.created[0]["refId"] == step.ref_id
    assert api.created[0]["walletAddress"] == _state()["source"]["address"]
    assert result == {"transaction_id": "00000000-0000-4000-8000-000000000001", "state": "COMPLETE", "tx_hash": "0xabc"}
    assert "secret" not in capsys.readouterr().out.lower()
