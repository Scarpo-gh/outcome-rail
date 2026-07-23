"""Fail-closed Circle Developer-Controlled Wallet ERC-8183 execution adapter.

The public receipt preflight remains separate from this adapter.  Nothing in this
module imports Circle or dotenv at import time.  A Circle client is created only
after an explicit ``--execute`` flag *and* the exact confirmation token pass.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import time
from typing import Any, Callable
from uuid import uuid4

from scripts.arc_erc8183_dry_run import (
    BUDGET_BASE_UNITS,
    CHAIN,
    EXECUTION_CONFIRMATION_TOKEN,
    REFERENCE_CONTRACT,
    USDC_CONTRACT,
    ZERO_ADDRESS,
)

FEE_LEVEL = "MEDIUM"
POLL_INTERVAL_SECONDS = 2
MAX_POLLS = 30


class ExecutionGuardError(PermissionError):
    """Execution was not deliberately authorized; no client or network is used."""


class TransactionFailedError(RuntimeError):
    """Circle reported a terminal transaction failure without exposing request data."""


@dataclass(frozen=True)
class ExecutionStep:
    """One Circle contract-execution request, with only public request fields."""

    name: str
    request_fields: dict[str, Any]
    idempotency_key: str
    ref_id: str


def require_execution_authorization(*, execute: bool, confirmation_token: str | None) -> None:
    """Reject before importing dotenv/SDK, constructing a client, or polling a network."""
    if execute is not True:
        raise ExecutionGuardError("execution requires the explicit --execute flag")
    if confirmation_token != EXECUTION_CONFIRMATION_TOKEN:
        raise ExecutionGuardError("execution requires literal confirmation token ERC8183_EXECUTION_CONFIRMED")


def _step(name: str, *, wallet_address: str, contract_address: str, signature: str, parameters: list[Any]) -> ExecutionStep:
    return ExecutionStep(
        name=name,
        request_fields={
            "blockchain": CHAIN,
            "walletAddress": wallet_address,
            "contractAddress": contract_address,
            "abiFunctionSignature": signature,
            "abiParameters": parameters,
            "feeLevel": FEE_LEVEL,
        },
        idempotency_key=str(uuid4()),
        ref_id=f"outcomerail:erc8183:{name}",
    )


def build_execution_steps(plan: dict[str, Any], *, job_a_id: int, job_b_id: int) -> list[ExecutionStep]:
    """Translate an already verified public preflight plan into individual calls.

    This is pure request construction: it does not require a Circle installation,
    credentials, a client, RPC access, or an entity-secret ciphertext.  The SDK
    fills a fresh per-request ciphertext after the execution guard allows it.
    """
    if plan.get("mode") != "DRY_RUN_NO_BROADCAST":
        raise ValueError("only an OutcomeRail dry-run preflight plan may be executed")
    if not isinstance(job_a_id, int) or job_a_id < 0 or not isinstance(job_b_id, int) or job_b_id < 0:
        raise ValueError("job IDs must be non-negative integers")
    client = plan["client"]
    provider = plan["provider"]
    evaluator = plan["evaluator"]
    deadline = str(plan["deadline"])
    budget = str(plan["budget_base_units"])
    receipt_hash = plan["receipt_hash_bytes32"]
    reason_hash = plan["reason_hash_bytes32"]

    return [
        _step("create_job_a", wallet_address=client, contract_address=REFERENCE_CONTRACT,
              signature="createJob(address,address,uint256,string,address)",
              parameters=[provider, evaluator, deadline, "OutcomeRail receipt-backed analysis job A", ZERO_ADDRESS]),
        _step("set_budget_a", wallet_address=provider, contract_address=REFERENCE_CONTRACT,
              signature="setBudget(uint256,uint256,bytes)", parameters=[job_a_id, budget, "0x"]),
        _step("approve_a", wallet_address=client, contract_address=USDC_CONTRACT,
              signature="approve(address,uint256)", parameters=[REFERENCE_CONTRACT, budget]),
        _step("fund_a", wallet_address=client, contract_address=REFERENCE_CONTRACT,
              signature="fund(uint256,bytes)", parameters=[job_a_id, "0x"]),
        _step("submit_a", wallet_address=provider, contract_address=REFERENCE_CONTRACT,
              signature="submit(uint256,bytes32,bytes)", parameters=[job_a_id, receipt_hash, "0x"]),
        _step("complete_a", wallet_address=evaluator, contract_address=REFERENCE_CONTRACT,
              signature="complete(uint256,bytes32,bytes)", parameters=[job_a_id, reason_hash, "0x"]),
        _step("create_job_b", wallet_address=client, contract_address=REFERENCE_CONTRACT,
              signature="createJob(address,address,uint256,string,address)",
              parameters=[provider, evaluator, deadline, "OutcomeRail refund-path analysis job B", ZERO_ADDRESS]),
        _step("set_budget_b", wallet_address=provider, contract_address=REFERENCE_CONTRACT,
              signature="setBudget(uint256,uint256,bytes)", parameters=[job_b_id, budget, "0x"]),
        _step("approve_b", wallet_address=client, contract_address=USDC_CONTRACT,
              signature="approve(address,uint256)", parameters=[REFERENCE_CONTRACT, budget]),
        _step("fund_b", wallet_address=client, contract_address=REFERENCE_CONTRACT,
              signature="fund(uint256,bytes)", parameters=[job_b_id, "0x"]),
        _step("claim_refund_b", wallet_address=client, contract_address=REFERENCE_CONTRACT,
              signature="claimRefund(uint256)", parameters=[job_b_id]),
    ]


def make_circle_client_factory(env_file: Path | None = None) -> Callable[[], tuple[Any, Any]]:
    """Return a deferred factory; it does not inspect the optional .env file yet."""
    return lambda: _default_client_factory(env_file)


def _default_client_factory(env_file: Path | None = None) -> tuple[Any, Any]:
    """Load local credentials only after authorization; never print credential values."""
    from dotenv import load_dotenv
    from circle.web3 import developer_controlled_wallets as dcw, utils

    if env_file is not None:
        load_dotenv(env_file, override=False)
    api_key = os.getenv("CIRCLE_API_KEY")
    entity_secret = os.getenv("CIRCLE_ENTITY_SECRET")
    if not api_key or not entity_secret:
        raise RuntimeError("Circle credentials are unavailable after authorized execution request")
    return utils.init_developer_controlled_wallets_client(
        api_key=api_key, entity_secret=entity_secret
    ), dcw


def _transaction_view(response: Any) -> Any:
    return response.data.transaction


def _poll_transaction(transactions_api: Any, transaction_id: str, *, poll_interval_seconds: float, max_polls: int, sleep: Callable[[float], None]) -> dict[str, str | None]:
    for _ in range(max_polls):
        transaction = _transaction_view(transactions_api.get_transaction(id=transaction_id))
        state = str(transaction.state)
        if state == "COMPLETE":
            return {"transaction_id": transaction_id, "state": state, "tx_hash": getattr(transaction, "tx_hash", None)}
        if state in {"FAILED", "CANCELLED", "DENIED"}:
            raise TransactionFailedError(f"Circle transaction entered terminal state {state}")
        sleep(poll_interval_seconds)
    raise TimeoutError("Circle transaction did not reach COMPLETE before polling timeout")


def execute_step(step: ExecutionStep, *, execute: bool, confirmation_token: str | None, client_factory: Callable[[], tuple[Any, Any]] | None = None, poll_interval_seconds: float = POLL_INTERVAL_SECONDS, max_polls: int = MAX_POLLS, sleep: Callable[[float], None] = time.sleep) -> dict[str, str | None]:
    """Create exactly one guarded Circle request and poll it to a terminal state.

    The production client factory performs the Circle SDK import and optional
    dotenv load. Tests supply a fake factory; no network is contacted by request
    construction or by a denied call.
    """
    require_execution_authorization(execute=execute, confirmation_token=confirmation_token)
    client, dcw = (client_factory or _default_client_factory)()
    request_payload = {**step.request_fields, "idempotencyKey": step.idempotency_key, "refId": step.ref_id}
    request = dcw.CreateContractExecutionTransactionForDeveloperRequest.from_dict(request_payload)
    transactions_api = dcw.TransactionsApi(client)
    response = transactions_api.create_developer_transaction_contract_execution(request)
    return _poll_transaction(
        transactions_api,
        str(response.data.id),
        poll_interval_seconds=poll_interval_seconds,
        max_polls=max_polls,
        sleep=sleep,
    )
