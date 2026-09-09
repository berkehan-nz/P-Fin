# claude_inbox — analiz yazma alani

Bu klasor, **analiz metnini yazan ajan** ile **sayilari hesaplayan veri hatti**
arasindaki tek arayuzdur.

## Kural

Buraya yazan taraf **sayisal alanlara dokunamaz.** Yalnizca su alanlar kabul
edilir:

| Alan | Ne icin |
|---|---|
| `story` | Is modeli, hendek, neden ucuz, boga/ayi tezi, katalizor, tez kiricilar, haber ozeti, hukum |
| `decision` | AL / BEKLE / ELE karari ve gerekcesi |
| `catalyst_score` | 0-100 arasi katalizor puani (otomatik hesaplanmiyor) |
| `notes` | Serbest not |

Metrikler, fiyatlar, puanlar ve carpanlar **veri hattinin** sorumlulugundadir.
Bu ayrim kasitlidir: elle yazilmis bir sayi hesaplanmis bir metrigin uzerine
yazabilseydi, kartta hangi sayinin nereden geldigi belirsizlesirdi.

## Dosya adi

`<TICKER>.json` — ornegin `DBX.json`. Buyuk harf.

## Sema

`_TEMPLATE.json` dosyasini kopyala ve doldur. Bos birakilan alanlar kartta
zaten yazili olani SILMEZ; yalnizca dolu alanlar uzerine yazar.

```json
{
  "ticker": "DBX",
  "story": {
    "business_model": "Ne satiyor, parayi nasil kazaniyor. 2-4 cumle.",
    "moat": "Rakip neden kolayca kopyalayamiyor. Yoksa 'belirgin bir hendek yok' yaz.",
    "why_cheap_diagnosis": "Kisa teshis, 2-4 kelime. Orn: 'Buyume yavasladi'",
    "why_cheap_rationale": "Piyasa neden boyle fiyatliyor. 2-4 cumle.",
    "bull_case": ["Madde madde, her biri tek cumle"],
    "bear_case": ["Madde madde, her biri tek cumle"],
    "catalyst": {
      "type": "Yeniden fiyatlanmayi ne tetikler",
      "expected_date": "2026Q4",
      "confidence": "dusuk | orta | yuksek"
    },
    "thesis_breakers": ["Hangi gelisme tezi gecersiz kilar"],
    "analyst_narrative": "Analistler ne diyor, katiliyor musun",
    "news_summary": "Son donem haberlerinin ozeti",
    "claude_verdict": "Iki satirlik hukum. Kart izgarasinda ilk 140 karakteri gorunur.",
    "author": "claude",
    "updated_at": "2026-09-09"
  },
  "decision": {
    "action": "BEKLE",
    "date": "2026-09-09",
    "rationale": "Neden bu karar",
    "author": "berke"
  }
}
```

## Sinirlar

- Metin alanlari en fazla 4000 karakter
- Liste alanlari en fazla 12 madde
- `decision.action` yalnizca `AL`, `BEKLE` veya `ELE` olabilir
- `catalyst_score` 0-100 arasinda

Kurallara uymayan dosya **islenmez** ve GitHub Actions'ta hata olarak gorunur.
Kartlar bozulmaz.

## Ne zaman islenir

Bu klasore her yazildiginda **Merge** is akisi otomatik calisir (~30 saniye)
ve kartlari gunceller. Ayrica gunluk kosu da her sabah birlestirir.

## Once karti oku

Analiz yazmadan once sirketin mevcut verisini oku:

```
https://raw.githubusercontent.com/berkehan-nz/P-Fin/main/data/cards/<TICKER>.json
```

Kartin `data_quality` bolumune bak. `status` alani `kotu` ise sayilara
guvenme; `issues` listesi neyin eksik oldugunu soyler.
