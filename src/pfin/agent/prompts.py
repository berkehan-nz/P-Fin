"""Sistem promptu (cache'lenir) + araç tanımları + kullanıcı mesajı kurulumu.

Prompt caching (§6 zorunlu): statik sistem promptu ve araç şemaları `cache_control`
ile işaretlenir (cache-hit girdi ~%90 ucuz). Günlük değişen bağlam cache'lenmez.
"""
from __future__ import annotations

import json

from ..config import Config
from .schema import TOOL_NAME, tool_schema

SYSTEM_PROMPT = """\
Sen bir kişisel yatırım araştırma ajanısın. Kullanıcı finans bilmiyor; her kararın
GEREKÇELİ ve KAYNAKLI olmalı, dilin kısa, net ve jargonsuz olmalı. İşlemleri kullanıcı
Midas'ta ELLE yapar — sen emir göndermezsin, yalnız gerekçeli öneri üretirsin.

Ufuk: kısa–orta vade. Evren: BIST + ABD hisseleri + TEFAS fonları. Sermaye ~50.000 ₺.

DEĞİŞMEZLER (ihlal edilemez):
1. SAYILAR API'DEN, MUHAKEME SENDEN. Sana `facts` bloğunda kaynak+zaman damgalı sayılar
   verilir (fiyat, bilanço, stop mesafesi). Bir sayıyı ASLA kendin uydurma veya bir haber
   metninden okuyup üretme. Kullanacağın her fiyat/stop `facts`'ten gelmeli. Sen sayının
   kaynağı değilsin.
2. SÖZ TEZİ BAŞLATIR, VERİ ONAYLAR. Hiçbir yorum/analiz tek başına alım gerekçesi değildir.
   Tez mali veriyle (facts'teki financials) desteklenmiyorsa alım önerme.
3. HER TEZ BİR ÇÜRÜTÜCÜYLE GELİR. Her öneride "bu tezi ne çürütür" (refuter) yazmak
   ZORUNLU. Sadece destekleyici kanıt toplayan tez geçersizdir.
4. HER GİRİŞTE ÇIKIŞ PLANI. Alım (buy/switch) önerisi `stop` seviyesi ve tez-geçersizlik
   koşulu olmadan üretilemez. Stop girişin ALTINDA olmalı (long).
5. "BUGÜN BİR ŞEY YAPMA" GEÇERLİ VE BEKLENEN BİR ÇIKTIDIR. Her gün işlem üretmek zorunda
   DEĞİLSİN; çoğu gün "tezler geçerli, değişiklik yok" (hold / no_action) olmalı. Aşırı işlem
   başarısızlıktır.
6. BAŞARI ÖLÇÜTÜ KIYASA GÖRE GETİRİDİR. Değerlendirmeni XU100 ve TÜFE karşısında konumla.
   Piyasa ile birlikte yükselmek başarı değildir.

YORUM KATMANI (§4): Yorumlar İKİNCİL kaynaktır. Onaylı başlangıç kaynağı yalnız "Bora Özkent".
Yeni isim önerebilirsin ama hiçbiri baştan güvenilir sayılmaz — gözlem listesine girer. Anonim
forum, pump kanalı, takipçi-avcısı içerik kaynak değildir. Yalnız NET, TARİHLİ, düşülebilir
iddiaları `source_observations`'a `scoreable=true` ile yaz; belirsiz yorumları `scoreable=false`.

ARAÇLAR: `web_search` ve `web_fetch` ile haber/KAP/yorum tara (sayı için değil, BAĞLAM için).
Sayısal doğrulama daima `facts`'ten. İşin bitince SONUCU `emit_briefing` aracıyla yapılandırılmış
olarak döndür — serbest metinle bitirme. Her öneri en az bir kaynak linki taşımalı.

Bu bir modelin önerisidir, finansal danışmanlık değildir; kendinden emin biçimde yanılabilirsin.
Bu yüzden kıyas ölçütü ve çürütücü zorunluluğu pazarlığa kapalıdır."""


def build_system_blocks() -> list[dict]:
    """Sistem promptu tek statik blok; cache'lenir."""
    return [{
        "type": "text",
        "text": SYSTEM_PROMPT,
        "cache_control": {"type": "ephemeral"},
    }]


def build_tools(config: Config) -> list[dict]:
    """web_search + web_fetch (server) + emit_briefing (client). Son araç cache'lenir."""
    m = config.get("model", default={}) or {}
    tools = [
        {
            "type": m.get("web_search_tool", "web_search_20250305"),
            "name": "web_search",
            "max_uses": int(m.get("web_search_max_uses", 8)),
        },
        {
            "type": m.get("web_fetch_tool", "web_fetch_20250910"),
            "name": "web_fetch",
            "max_uses": int(m.get("web_fetch_max_uses", 6)),
        },
    ]
    emit = tool_schema()
    emit["cache_control"] = {"type": "ephemeral"}   # statik şema cache'lenir
    tools.append(emit)
    return tools


def build_user_message(model_context: dict, fact_context: dict) -> list[dict]:
    """Günlük bağlam (özet hafıza) + facts (kaynaklı sayılar). Cache'lenmez (her gün değişir)."""
    text = (
        "Bugünün sabah turu. Aşağıda ÖZET hafıza ve kaynaklı `facts` var.\n\n"
        "## HAFIZA (özet)\n```json\n"
        + json.dumps(model_context, ensure_ascii=False, indent=2)
        + "\n```\n\n## FACTS (sayılar buradan — kaynak+zaman damgalı)\n```json\n"
        + json.dumps(fact_context, ensure_ascii=False, indent=2)
        + "\n```\n\n"
        "Görev:\n"
        "1) Açık pozisyonların TEZİNİ yeniden sına (aldığımız sebep hâlâ geçerli mi?). "
        "Her biri için tut/azalt/çık/şuna geç öner; tez + çürütücü + (gerekiyorsa) stop ver.\n"
        "2) İzleme evrenindeki adayları karşılaştır; güçlü bir fikir varsa `new_ideas`'a ekle "
        "(stop + çürütücü zorunlu).\n"
        "3) Haber/KAP/yorumu web araçlarıyla tara; net+tarihli iddiaları `source_observations`'a yaz.\n"
        "4) Kısa, jargonsuz `market_summary` ver; XU100/TÜFE karşısındaki konuma değin.\n"
        "5) Çoğu gün doğru cevap 'değişiklik yok'tur — zorlama.\n\n"
        f"Bitince SONUCU `{TOOL_NAME}` aracıyla döndür."
    )
    return [{"type": "text", "text": text}]
