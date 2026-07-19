# OutcomeRail

Prediction-market kullanıcıları ve agent’ları için **işlem öncesi execution-quality** motoru.

> Prototype / hackathon V1. Trade yapmaz, custody almaz ve sonuçların kârlılık garantisi olduğu iddiasında bulunmaz.

## V1 mevcut kapsamı

- Görünür orderbook seviyelerinden requested-size VWAP
- BUY için ask, SELL için bid tarafının simülasyonu
- `PROCEED`, `REDUCE`, `BLOCK` kararları
- Top-of-book spread ve görünür derinlik kanıtı
- Deterministik SHA-256 report hash
- Canonical, off-chain doğrulanabilir execution receipt: snapshot, input, politika ve sonucu tek hash'e bağlar
- Public, read-only Polymarket Gamma/CLOB snapshot adaptörü

## Karar kuralları

| Sonuç | Kural |
|---|---|
| `PROCEED` | İstenen boyut görünür defterde tamamen karşılanıyor. |
| `REDUCE` | Boyutun en az yarısı ama tamamı görünür. |
| `BLOCK` | Boyutun yarısından azı görünür. |

Bu yalnızca visible liquidity değerlendirmesidir. Public CLOB adaptörü snapshot `timestamp` ve `hash` değerlerini de taşır; V1 REST snapshot kullanır ve stale/HTTP hatalarını sessizce gizlemez.

## Receipt kanıtı

`receipt.py`, işlem öncesi analiz için off-chain bir makbuz üretir. Receipt; tam orderbook snapshot content hash'ini, CLOB kaynak metadata'sını, istenen boyutu/yönü, politika kimliği-sürümünü ve `PROCEED`/`REDUCE`/`BLOCK` sonucunu tek SHA-256 hash'e bağlar. `verify_execution_receipt()` sonradan değiştirilmiş bir alanı reddeder.

Bu **finansal settlement değildir**: trade, custody, ödeme, otomatik emir veya kârlılık iddiası yoktur. Arc'a yeni bir işlem de göndermez.

## Policy v1.1 guardrails

`policy.py`, base VWAP raporunu yalnız daha temkinli hale getirir; `BLOCK` kararını asla gevşetmez. Varsayılan policy:

- Snapshot yaşı > 30 saniye veya parse edilemeyen/gelecek kaynak zamanı → `BLOCK` (`STALE_SNAPSHOT`)
- Spread > 0.03 → `REDUCE` (`WIDE_SPREAD`)
- İşlem yönündeki book seviyelerinde en büyük fiyat boşluğu > 0.02 → `REDUCE` (`LARGE_PRICE_GAP`)

Policy'nin eşikleri ve content hash'i receipt'e yazılır. Gerçek, public bir token için yalnız read-only demo:

```bash
# Tercih edilen public market yolu
python3 scripts/demo_receipt.py --market-id <gamma-market-id> --outcome Yes --action BUY --size 10

# Alternatif: bilinen public CLOB token id ile
python3 scripts/demo_receipt.py --token-id <public-clob-token-id> --action BUY --size 10
```

Market yolu Gamma'dan outcome token'ını çözer ve receipt'e canonical input manifest hash'ini de bağlar. Manifest ayrıca kullanılan public Gamma market ve CLOB book endpoint URL'lerini hash kapsamına alır; CLOB'un kaynak timestamp/hash'i receipt snapshot'ında korunur. Market komutu varsayılan olarak `evidence/outcomerail.jsonl` içine append-only, hash-zincirli **yerel** evidence entry yazar; bu dosya git'e dahil edilmez. Bütünlüğü bağımsız doğrulamak için:

```bash
python3 scripts/verify_evidence.py --log evidence/outcomerail.jsonl
```

Arc anchor komutu deneysel ve public demo kapsamı dışındadır: zincire işlem gönderir. Yalnız ayrı açık onayla, testnet'te ve local credential'larla çalıştırılmalıdır.

Kaynak botlardan alınabilecek/ayrıştırılan yetenekler: [`docs/SOURCE_ADAPTATION.md`](docs/SOURCE_ADAPTATION.md).

Arc builder görünürlüğü için kısa ürün hikâyesi, canlı demo komutu, doğrulama adımları ve mimari: [`docs/BUILDER_DEMO.md`](docs/BUILDER_DEMO.md).

Public demo: [scarpo-gh.github.io/outcome-rail](https://scarpo-gh.github.io/outcome-rail/)

## Çalıştırma

```bash
cd outcome-rail
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip pytest
pytest -q
```

## Güvenlik sınırları

- Polymarket trading credential’ı istenmez veya saklanmaz.
- Otomatik trade yapılmaz.
- Circle API key, Entity Secret veya recovery file bu projeye konmaz.
- Arc entegrasyonu daha sonra report hash / job receipt kanıtı için eklenir; V1 motoru zincirden bağımsızdır.
