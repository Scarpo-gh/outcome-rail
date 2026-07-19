# Arc House / Discord — Teknik Feedback Postu

> Bu metin paylaşım için taslaktır; henüz Arc House veya Discord'a gönderilmedi.

## Başlık

**Feedback request: verifiable, read-only prediction-market analysis jobs on Arc**

## Post metni

Hi all — I’m building **OutcomeRail**, a read-only execution-quality layer for prediction-market agents.

Given a public Polymarket `market_id`, outcome, side and requested size, it:

- resolves the public outcome token through Gamma;
- reads the public CLOB orderbook;
- computes requested-size VWAP and visible-depth availability;
- applies deterministic freshness, spread and price-gap guardrails;
- returns `PROCEED`, `REDUCE`, or `BLOCK`;
- produces a canonical input manifest and tamper-evident execution receipt.

The current V1 is intentionally narrow: no trade placement, custody, wallet connection, private credentials, or settlement. A live public-data smoke run produces a verified receipt and an append-only local evidence entry.

Architecture / demo package: https://scarpo-gh.github.io/outcome-rail/

I’d appreciate feedback on one specific next step: **what is the simplest Arc-native model for a bounded agent analysis job?**

My current direction is:

```text
agent opens a small test-USDC analysis job
→ OutcomeRail returns a receipt within a bounded TTL
→ contract verifies required receipt fields / a trusted verifier attestation
→ release to provider, otherwise refund
```

Questions:

1. For an early testnet prototype, is a signed callback/attestation more practical than attempting full on-chain verification of an off-chain orderbook receipt?
2. What is the minimum useful on-chain job schema beyond `job_id`, requester, provider, amount, expiry and receipt hash?
3. Are there existing Arc examples or builders working on similar agent-payment / escrow flows that would be useful to study?

I’m looking for architecture feedback, not trading advice or promotion. Happy to share the sanitized code/demo once it is published.

## Yayın öncesi kontrol

- `<PUBLIC_REPO_OR_DEMO_URL>` yerini gerçek public URL ile değiştir.
- Yalnız çalışır, sanitise edilmiş repo/demoyu bağla.
- Wallet adresi, API key, `.env`, recovery file veya private log paylaşma.
- “test-USDC” dışında ödül/airdrop/rol talebi ekleme.
- Paylaşım sonrası gelen somut feedback'i `docs/` altında tarihli not olarak kaydet; Arc House'a ikinci post atmak yerine aynı başlığı güncelle.
