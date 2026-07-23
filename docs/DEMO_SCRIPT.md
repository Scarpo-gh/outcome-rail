# OutcomeRail — 3 Dakikalık Builder Demo

## Amaç

OutcomeRail'in public prediction-market verisinden deterministic receipt ürettiğini ve Arc Testnet'te iki farklı bounded ERC-8183 sonucu kanıtladığını göstermek.

## 0:00–0:25 — Problem

> Bir agent bir public-data analizi teslim ettiğinde, talebin, verinin, politikanın ve sonucun sonradan doğrulanabilir biçimde birbirine bağlı kalması gerekir. Sadece bir API cevabı bu provenance zincirini sağlamaz.

## 0:25–0:55 — OutcomeRail receipt

Göster:

```bash
python3 scripts/demo_receipt.py --market-id <active-gamma-market-id> --outcome Yes --action BUY --size 5
```

Vurgula:

- Yalnız public Gamma/CLOB verisi okunur.
- VWAP, visible depth ve freshness/spread guardrail'leri değerlendirilir.
- Sonuç `PROCEED`, `REDUCE` veya `BLOCK` olur.
- Snapshot, policy, input ve sonuç tek SHA-256 receipt hash'ine bağlanır.

> Bu trade sinyali veya emir değildir. Demo receipt'imizde verdict `BLOCK` oldu; amaç analitik kanıtın teslimidir.

## 0:55–1:45 — Job A: receipt → complete

Göster: [`ARC_EVIDENCE.md`](ARC_EVIDENCE.md#job-a--receipt-delivery-and-completion)

> Job A'da requester job açtı ve 5 test-USDC bütçesini fonladı. Provider, doğrulanmış OutcomeRail receipt hash'ini `submit` ile teslim etti. Evaluator aynı job'ı `complete` ile kapattı.

Vurgula:

```text
create → budget → approve → fund → submit(receipt hash) → complete
```

## 1:45–2:25 — Job B: expiry → refund

Göster: [`ARC_EVIDENCE.md`](ARC_EVIDENCE.md#job-b--expiry-and-refund)

> Aynı bounded modelde Job B fonlandı ama deliverable gönderilmedi. Deadline sonrasında `claimRefund` çağrısı çalıştı.

Vurgula:

```text
create → budget → approve → fund → expiry → claimRefund
```

## 2:25–3:00 — Sınırlar ve sonraki soru

> OutcomeRail trade yapmaz, Polymarket credential istemez, kullanıcı cüzdanı bağlamaz, custody yapmaz ve mainnet/gerçek USDC kullanmaz. Polymarket yalnız ilk public-data adapter'dır.

Builder feedback sorusu:

> Agentic analysis delivery için receipt hash tek başına yeterli mi; yoksa signed callback veya standardize edilmiş deliverable schema ile mi ilerlemeliyiz?

## Canlı demo kontrolü

```bash
pytest -q
/home/hermes/.foundry/bin/forge test -q
python3 scripts/verify_evidence.py --log evidence/outcomerail.jsonl
```

Sunumda yalnız doğrulanabilir Arcscan linkleri ve repo test çıktıları kullanılmalıdır.
