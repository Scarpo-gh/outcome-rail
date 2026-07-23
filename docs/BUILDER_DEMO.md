# OutcomeRail — Arc Builder Demo Paketi

## Tek cümle

**OutcomeRail**, ilk public-data adapter olarak Polymarket orderbook snapshot'ını değerlendiren, deterministic bir execution-feasibility/provenance receipt üreten read-only agent altyapısıdır.

> Trade, wagering, custody, wallet veya Polymarket credential istemez; kârlılık, outcome tahmini veya yatırım sonucu garantisi vermez.

## Neyi çözüyor?

Bir agent ya da kullanıcı “bu outcome için bu boyutta BUY/SELL görünür defterde ne kadar uygulanabilir?” sorusunu sorar. OutcomeRail, yalnız public Gamma ve CLOB verisiyle aşağıdakileri üretir:

- requested-size VWAP ve görünür uygulanabilir miktar;
- `PROCEED`, `REDUCE` veya `BLOCK` kararı;
- snapshot freshness, spread ve price-gap guardrail'leri;
- canonical input manifest;
- değiştirilmeye karşı SHA-256 ile doğrulanabilen receipt;
- isteğe bağlı append-only local evidence zinciri.

## Çalışan akış

```text
market_id + outcome + BUY/SELL + requested_size
        │
        ▼
Public Gamma API ──► outcome token id
        │
        ▼
Public CLOB API ───► timestamp + book hash + visible bid/ask levels
        │
        ▼
OutcomeRail core ──► requested-size VWAP / visible depth
        │
        ├──────────► policy v1.1: snapshot age, spread, price gap
        │
        ▼
Canonical manifest ─► execution receipt ─► local evidence entry
                                      │
                                      ▼
                              independent verification
```

Public demo: [https://scarpo-gh.github.io/outcome-rail/](https://scarpo-gh.github.io/outcome-rail/)

Ayrıntılı görsel: [`outcomerail-architecture.html`](outcomerail-architecture.html). Dosya-URL'si tarayıcı/panel tarafından engellenirse, doğrudan görüntülenebilir SVG sürümü: [`outcomerail-architecture.svg`](outcomerail-architecture.svg).

## Read-only local API

CLI dışında agent/tool entegrasyonu için local WSGI endpoint: `POST /v1/analyze`. Contract, `curl` örneği ve hata yüzeyi: [`API.md`](API.md). API yalnız `127.0.0.1` üzerinde başlar; GitHub Pages static demodur ve API host etmez.

## 2 dakikalık canlı demo

Bu komut yalnız public HTTP okuması yapar. Emir, auth, wallet veya transfer içermez.

```bash
cd /home/hermes/outcome-rail
python3 scripts/demo_receipt.py \
  --market-id <active-gamma-market-id> \
  --outcome Yes \
  --action BUY \
  --size 10
```

Beklenen JSON yüzeyi:

```json
{
  "manifest": {"schema": "outcomerail.input-manifest.v1", "content_hash": "..."},
  "receipt": {
    "schema": "outcomerail.execution-receipt.v1",
    "input": {"manifest_hash": "..."},
    "analysis": {"verdict": "PROCEED | REDUCE | BLOCK"}
  },
  "verified": true,
  "evidence_entry": {"entry_hash": "..."}
}
```

Sonra evidence zincirini doğrula:

```bash
python3 scripts/verify_evidence.py --log evidence/outcomerail.jsonl
```

Başarılı doğrulama örneği:

```json
{"log":"evidence/outcomerail.jsonl","entries":1,"valid":true}
```

## Doğrulanabilirlik iddiası

Receipt aşağıdakileri tek hash kapsamına alır:

- token id, source book timestamp/hash ve snapshot content hash;
- istenen büyüklük, yön, market id ve outcome;
- policy id/sürümü/eşikleri/content hash'i;
- VWAP sonucu, spread, rule id'leri ve verdict;
- input manifest hash'i ve gözlem zamanı.

`verify_execution_receipt()` bu alanlardan biri sonradan değiştirilirse `false` döndürür. Evidence log ise her kaydı önceki entry hash'ine bağlar.

## Arc ile bağlantı

Ürün katmanı off-chain/read-only kalır. Arc Testnet üzerinde ise OutcomeRail için
iki **test-USDC** ERC-8183 kanıtı üretildi. Bunlar trade, wager veya kullanıcı
fonu değildir; ayrı test walletlar arasında bounded analysis-job demonstrasyonudur.

### Job A — receipt teslimi ve complete

- Job ID: `159281`
- Verified OutcomeRail receipt hash: `0x2257db655f069e89c00ff637e36c46612911d5eb3f80fa4d96c68a381c76a02b`
- [createJob](https://testnet.arcscan.app/tx/0x7c5fb3eb26fb6df90eb26af43a8a898dc30d6eb54703ea763849ca0b8f16a635) → [setBudget](https://testnet.arcscan.app/tx/0x8124665d7d6433baa3de320ac9be10f7e3b488ffc4b3ae898d3c5b54896d4d77) → [approve](https://testnet.arcscan.app/tx/0x00d55da8eadb78aa43dc7a36bedb58540c2c60d2cef5709b7f74e1a9e1252615) → [fund](https://testnet.arcscan.app/tx/0x71cb7cfd7521286ee742468c57255dd80a8d76a6de3fef791eac63582bdea589) → [submit](https://testnet.arcscan.app/tx/0x40659649ee965ce59de1fe0f985d6fff89d1de8958521ca6460e0dc9309f832e) → [complete](https://testnet.arcscan.app/tx/0x5968dfe24910eb734fcaaa96cfa7afc9152fbb3611b271f211f1d801312a5ea7)

### Job B — expiry ve refund

- Job ID: `159283`
- [createJob](https://testnet.arcscan.app/tx/0x5778d7a58a5246c0f273a85c208d695577312ed10b8fd561f0c2c0106b6a0f04) → [setBudget](https://testnet.arcscan.app/tx/0x45275f5878ddefd78d0cb5c8c65927e6c98f7948d334494e5a451cbd781b46c7) → [approve](https://testnet.arcscan.app/tx/0x49a012b36f86add4e3c45b70240a5909765434cb7825b690679f0af4b039291c) → [fund](https://testnet.arcscan.app/tx/0x88ba57c48791d2d689ef5e65e3768215a0c8229e226c294d7969aa0cd25d710e) → [claimRefund](https://testnet.arcscan.app/tx/0x94865921d18d15f0c9c3391c0cd7eaa17b887651fc74b0af4bf6ec0e5f565f4e)

Bu kanıtlar yalnız testnet demonstrasyonudur: mainnet, gerçek USDC, custody,
wallet-connect veya otomatik trade içermez.

## Builder feedback isteği

Arc House/Discord için kopyalanabilir İngilizce taslak: [`ARC_HOUSE_FEEDBACK_POST.md`](ARC_HOUSE_FEEDBACK_POST.md). Bu taslak henüz yayımlanmadı.

Aradığımız feedback spesifik:

1. Agent'ın ödeyeceği analiz işi için minimum deliverable ne olmalı: yalnız receipt mi, yoksa signed callback/API response mu?
2. Freshness, spread ve price-gap eşikleri market türüne göre nasıl sürümlenmeli?
3. Test-USDC escrow/release modeli Arc üzerinde bu iş için en sade ve doğrulanabilir nasıl kurulmalı?

## Bilerek kapsam dışı

- Emir gönderme, otomatik trade, cüzdan bağlama veya custody
- Kullanıcı fonu, settlement veya gerçek para akışı
- LLM tabanlı fiyat tahmini ya da yatırım tavsiyesi
- Private WebSocket, private Polymarket credential veya kişisel veri

## Tekrar üretim

```bash
cd /home/hermes/outcome-rail
python3 -m py_compile analysis_manifest.py analysis_job.py policy.py receipt.py scripts/demo_receipt.py
pytest -q
```

Demo paketinin teknik sınırları için ayrıca [`SOURCE_ADAPTATION.md`](SOURCE_ADAPTATION.md) dosyasına bakın.
