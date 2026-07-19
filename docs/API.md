# OutcomeRail Read-only Analysis API — V1

`POST /v1/analyze`, bir Polymarket market/outcome isteğini yalnız public Gamma ve CLOB verisiyle değerlendirir. Trade, wallet, custody, transfer, settlement, credential veya Arc on-chain işlemi başlatmaz.

> Bu WSGI servis GitHub Pages üzerinde çalışmaz. Pages yalnız static demo/dokümantasyonu sunar; API local loopback için tasarlanmıştır.

## Çalıştırma

```bash
cd /path/to/outcome-rail
python3 scripts/serve_api.py
```

Varsayılan adres: `http://127.0.0.1:8080`.

Farklı bir local port seçmek için:

```bash
python3 scripts/serve_api.py --port 8090
```

Varsayılanı bilinçli olarak loopback'tir. Bu minimal V1; auth/rate-limit/reverse-proxy olmadan public internete bind edilmemelidir.

## İstek

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

| Alan | Tür | Kural |
|---|---|---|
| `market_id` | string | Boş olmayan public Gamma market kimliği. |
| `outcome` | string | Boş olmayan outcome adı. |
| `action` | string | Tam olarak `BUY` veya `SELL`. |
| `size` | string | Pozitif, sonlu decimal. Örn. `"10"`. |

Body en fazla 8192 byte olabilir.

## Başarılı yanıt — `200 OK`

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

`manifest.content_hash` ile `receipt.input.manifest_hash` eşleşir. API başarı yanıtı local evidence entry veya evidence-log path döndürmez ve yazmaz.

## Hatalar

| HTTP | `error.code` | Durum |
|---|---|---|
| `400` | `invalid_request` | Bozuk JSON, eksik alan veya geçersiz `Content-Length`. |
| `404` | `not_found` | `/v1/analyze` dışında path. |
| `404` | `market_or_outcome_not_found` | Public market/outcome çözülemedi. |
| `405` | `method_not_allowed` | POST dışında method; `Allow: POST` döner. |
| `413` | `payload_too_large` | Body 8192 byte sınırını geçti. |
| `422` | `invalid_request` | Geçersiz `action` veya `size`. |
| `502` | `public_source_unavailable` | Public market verisi geçici olarak erişilemez. |
| `500` | `analysis_failed` | Sanitise edilmiş beklenmeyen analiz hatası. |

Hata formatı deterministiktir:

```json
{"error":{"code":"invalid_request","message":"..."}}
```

## Sınırlar

- V1 yalnız public Polymarket Gamma/CLOB GET çağrılarını kullanır.
- Snapshot tabanlıdır; receipt anlık emir uygulanabilirliği veya kârlılık garantisi değildir.
- API, `scripts/demo_receipt.py` aksine varsayılan olarak append-only evidence log üretmez.
- Local development için dependency-free stdlib WSGI kullanır.
