# OutcomeRail — Kaynak Botlardan Adaptasyon Haritası

## Doğrudan alınan tasarım

| Kaynak | Kanıt | OutcomeRail karşılığı |
|---|---|---|
| bot_v21 | Requested-size derinlik, orderbook gap ve exit-depth riskleri | V1'in requested-size VWAP / visible-depth kararı. Pozisyon yönetimi veya emir işlemleri taşınmadı. |
| PolyProbe | Gamma metadata + CLOB orderbook'u birlikte kullanma; Cloudflare sorunlarında resmi CLOB SDK tercihi | Read-only Gamma/CLOB adaptörü; `BookSnapshot` kaynak zamanını ve CLOB hash'ini korur. |
| ProBot | LLM'den önce deterministik pre-filter; append-only analiz kaydı | Receipt önce deterministik snapshot + politika + sonuç ile kuruldu. LLM sinyalleri ancak ayrı, sürümlü analiz girdisi olarak eklenebilir. |

## V1 receipt sınırı

`receipt.py` şu alanları tek SHA-256 kanıtına bağlar:

- Token kimliği, CLOB kaynak zamanı/hash'i ve tam snapshot content hash'i
- İstenen boyut ve `BUY` / `SELL` yönü
- Politika kimliği ve sürümü
- VWAP sonucu, visible execution size, spread, karar ve kural kimlikleri
- OutcomeRail'in gözlem zamanı

Receipt doğrulaması değiştirilen verdict, politika, snapshot veya input'u reddeder.

## Bilerek taşınmayanlar

- bot_v21'in order placement, rebalance, position state ve private WebSocket katmanları: OutcomeRail trade yapmayan bir pre-trade analiz ürünü olarak kalır.
- bot_v21'in reward/Q-score mantığı: LP özelindedir; genel execution-quality kararına karıştırılmaz.
- ProBot'un LLM, external sports data ve whale yorumları: kaynak/kanıt sürümü ayrı tasarlanmadan receipt'e yazılmaz. LLM çıktılarını doğrudan finansal karar gibi sabitlemek doğru değildir.
- PolyProbe'un Telegram/UI ve kullanıcı analitiği: presentation/distribution katmanıdır, çekirdeğe alınmaz.

## Sonraki güvenli genişletme

1. **Policy v1.1 (tamamlandı):** max spread, max gap ve snapshot age parametrik kuralları; policy payload/content hash'i receipt'e dahil edildi.
2. **Analysis input manifest:** ProBot benzeri dış veri/LLM kullanılırsa, ham kaynağın hash'i, sağlayıcı, timestamp ve güven seviyesi ayrı manifest olarak receipt'e bağlanır.
3. **Arc provenance:** Ancak açık onayla, receipt hash'i için yeni bir Arc testnet anchor işlemi yapılır. Mevcut test transferi ürün receipt'i değildir; yalnız proje-level teknik kanıttır.

## Güvenlik

İçe aktarma denetiminde `alerts_ws.log`, `positions_ws_archive.jsonl` ve `events.db` ürün koduna alınmadı. Private credential/config dosyaları okunmadı ve OutcomeRail'e kopyalanmadı.
