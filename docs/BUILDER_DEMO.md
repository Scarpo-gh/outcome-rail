# OutcomeRail — Arc Builder Demo Paketi

## Tek cümle

**OutcomeRail**, bir Polymarket analiz isteğini public orderbook verisiyle değerlendiren, deterministic bir execution-quality receipt üreten ve input provenance'ını doğrulanabilir manifest'e bağlayan read-only agent altyapısıdır.

> Trade yapmaz, custody almaz, cüzdan veya Polymarket credential istemez; kârlılık/sonuç garantisi vermez.

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

Mevcut ürün katmanı off-chain/read-only'dir. Arc için şu anki kanıt, ayrı olarak doğrulanmış Circle Developer-Controlled Wallet testnet transferidir:

- [Arc Testnet transaction](https://testnet.arcscan.app/tx/0x5bfe13e4be52ae771bc814edd58b5c63f07501a53e197b80127aa65ccbef8615)

Bu transfer **OutcomeRail receipt settlement'i değildir**. Bir sonraki Arc-native adım, ancak gerçek feedback/agent talebi varsa bounded bir analysis job için test-USDC escrow ve receipt doğrulamasına göre release/refund tasarlamaktır.

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
