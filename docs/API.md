# OutcomeRail Read-only Analysis API — V1

`POST /v1/analyze` assesses a Polymarket market/outcome snapshot for execution feasibility using only public Gamma and CLOB data, with Polymarket as the first public-data adapter. This endpoint does not initiate trading, wallet, custody, transfer, wagering, investment-advice, credential, or Arc on-chain operations.

> This WSGI service does not run on GitHub Pages. Pages serves only the static demo and documentation; the API is designed for local loopback use.

## Run

```bash
cd /path/to/outcome-rail
python3 scripts/serve_api.py
```

Default address: `http://127.0.0.1:8080`.

To choose a different local port:

```bash
python3 scripts/serve_api.py --port 8090
```

The loopback default is intentional. This minimal V1 must not be bound to the public internet without authentication, rate limiting, and a reverse proxy.

## Request

```bash
curl --fail --silent --show-error \
  --request POST http://127.0.0.1:8080/v1/analyze \
  --header 'Content-Type: application/json' \
  --data '{
    "market_id": "540817",
    "outcome": "Yes",
    "action": "BUY",
    "size": "10"
  }'
```

| Field | Type | Rule |
|---|---|---|
| `market_id` | string | Non-empty public Gamma market identifier. |
| `outcome` | string | Non-empty outcome label. |
| `action` | string | Exactly `BUY` or `SELL`. |
| `size` | string | Positive, finite decimal; for example `"10"`. |

The body may be at most 8,192 bytes.

## Successful response — `200 OK`

```json
{
  "manifest": {
    "schema": "outcomerail.input-manifest.v1",
    "content_hash": "..."
  },
  "receipt": {
    "schema": "outcomerail.execution-receipt.v1",
    "input": {"manifest_hash": "..."},
    "analysis": {"verdict": "PROCEED | REDUCE | BLOCK"}
  },
  "verified": true
}
```

`manifest.content_hash` matches `receipt.input.manifest_hash`. A successful API response neither returns nor writes a local evidence entry or evidence-log path.

## Errors

| HTTP | `error.code` | Condition |
|---|---|---|
| `400` | `invalid_request` | Malformed JSON, a missing field, or invalid `Content-Length`. |
| `404` | `not_found` | A path other than `/v1/analyze`. |
| `404` | `market_or_outcome_not_found` | The public market/outcome could not be resolved. |
| `405` | `method_not_allowed` | A method other than POST; returns `Allow: POST`. |
| `413` | `payload_too_large` | Body exceeds the 8,192-byte limit. |
| `422` | `invalid_request` | Invalid `action` or `size`. |
| `502` | `public_source_unavailable` | Public market data is temporarily unavailable. |
| `500` | `analysis_failed` | Sanitized unexpected analysis failure. |

The error format is deterministic:

```json
{"error":{"code":"invalid_request","message":"..."}}
```

## Boundaries

- V1 only uses public Polymarket Gamma/CLOB GET calls.
- It is snapshot-based; a receipt is not a guarantee of immediate order executability or profitability.
- Unlike `scripts/demo_receipt.py`, the API does not write an append-only evidence log by default.
- It uses the dependency-free standard-library WSGI stack for local development.
