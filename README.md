# Nexizon Yatirim Dashboard

ABD hisselerinde 1-2 yillik vadede **yeniden fiyatlanma (re-rating)** firsatlari
arayan kural tabanli bir tarama, analiz ve portfoy takip sistemi.

Python 3.11 veri hatti + cercevesiz statik HTML/JS dashboard. **Tum veri
kaynaklari ucretsizdir**; ucretli API kullanilmaz.

---

## Neden bu tasarim

Dashboard'u **iki kullanici** kullaniyor:

- **Berke** — tarayicidan
- **Claude** — sohbet arayuzunden, GitHub raw dosyalarini okuyarak

Claude'un tarayicisi yok; yalnizca repodaki JSON dosyalarini okuyabiliyor ve
Claude Code araciligiyla yazabiliyor. Bu yuzden:

> **TUM DURUM DOSYADA TUTULUR.** `localStorage`'da kalici veri saklanmaz
> (yalnizca tema ve gorunum tercihi). Dashboard bir **JSON okuyucu/yazicidir**,
> veritabani degildir.

Repo public'tir — icinde kisisel veri yoktur. Portfoy dosyasi yalnizca sembol,
tarih, fiyat ve adet tasir.

---

## Hizli baslangic

```bash
git clone https://github.com/berkehan-nz/P-Fin.git
cd P-Fin
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

cp .env.example .env      # SEC_USER_AGENT'i kendi adin ve e-postanla doldur
python -m pytest tests/   # 147 test, ag gerektirmez

python -m src.run_seed    # ILK IS: 36 tohum sirket icin kart uret
python3 -m http.server 8000
# tarayicida: http://localhost:8000/docs/
```

> `docs/index.html` dosyasini `file://` ile acma — tarayici `fetch` isteklerini
> engeller. Repo **kokunden** bir HTTP sunucusu calistir.

---

## Anahtarlar

`.env` (yerel) ve GitHub Secrets (Actions) icinde tanimlanir.

| Anahtar | Zorunlu | Nereden | Ne icin |
|---|---|---|---|
| `SEC_USER_AGENT` | **EVET** | kendin yazarsin | SEC her istekte gercek ad + e-posta ister; yoksa **403** doner. Bicim: `"Ad Soyad eposta@ornek.com"` |
| `FINNHUB_API_KEY` | hayir | [finnhub.io/register](https://finnhub.io/register) | Haber + kazanc takvimi (60 istek/dk) |
| `FRED_API_KEY` | hayir | [fredaccount.stlouisfed.org](https://fredaccount.stlouisfed.org/apikeys) | Makro serit (10y tahvil, TUFE, issizlik) |

Finnhub/FRED anahtari yoksa ilgili bolumler bos gorunur; **veri hatti calismaya
devam eder**. SEC anahtari (User-Agent) olmadan hicbir sey calismaz.

---

## Komutlar

| Komut | Ne yapar | Ne kadar surer |
|---|---|---|
| `python -m src.run_seed` | 36 tohum sirket icin tam metrik seti + kart | ~5-10 dk |
| `python -m src.run_seed --tickers DBX,LSCC` | alt kume | saniyeler |
| `python -m src.run_funnel` | tam evren taramasi (Asama 0-4) | **saatler** |
| `python -m src.run_funnel --limit 500` | hizli deneme | ~20 dk |
| `python -m src.run_funnel --skip-sync` | SEC toplu verisini yeniden indirme | — |
| `python -m src.run_daily` | fiyat, haber, portfoy + `merge_story()` | ~2-5 dk |
| `python scripts/init_data.py` | `data/` klasorunu bos semalarla kurar | anlik |
| `python -m pytest tests/` | 147 test | < 1 sn |
| `RUN_NETWORK_TESTS=1 python -m pytest tests/test_live_edgar.py` | canli EDGAR dogrulamasi | ~1 dk |

---

## Repo yapisi

```
src/
  config.py           TUM esikler, agirliklar, sektor listeleri, SEED_TICKERS
  fundamentals.py     Normalize finansal veri modeli (TTM, ceyreklik seriler)
  metrics.py          EV, carpanlar, marjlar, ROIC, 40 Kurali, momentum
  scores.py           Piotroski F, Altman Z'', Beneish M, Sloan, ters DCF
  percentiles.py      Sektor ici + sirketin kendi 5 yillik yuzdelikleri
  scoring.py          Asama 4 puanlamasi (Ucuzluk/Kalite/Saglamlik/...)
  funnel.py           Asama 0-4 eleme mantigi + "nerede elenirdi" teshisi
  cards.py            Kart JSON uretimi + merge_story() + yazili blok koruma
  watchlist.py        Elle eklenen sirketler
  portfolio.py        Pozisyon takibi, K/Z, benchmark, uyarilar
  pipeline.py         Kosu adimlarinin ortak parcalari
  run_seed.py         TOHUM LISTESI kosusu
  run_funnel.py       Tam evren taramasi
  run_daily.py        Gunluk guncelleme
  sources/
    edgar_bulk.py     SEC toplu ZIP -> sqlite onbellek (API limiti yok)
    edgar_api.py      companyfacts, submissions, Form 4, XBRL -> Fundamentals
    prices.py         Stooq CSV (birincil) + yfinance (yedek)
    finnhub_api.py    Haber, kazanc takvimi
    fred_api.py       Makro
    analyst.py        Analist konsensusu (BILGI alani, karar alani degil)
    finra_short.py    Kisa pozisyon (iki haftalik FINRA dosyalari)
data/                 CIKTI — repoya commit edilir, Claude buradan okur
  candidates.json  universe.json  funnel_log.json  macro.json
  overview.json  thresholds.json  watchlist.json  portfolio.json
  portfolio_state.json  cards/<TICKER>.json
claude_inbox/         Claude'un yazdigi hikaye/analiz dosyalari
docs/                 GitHub Pages dashboard (vanilla JS, cerceve yok)
tests/                pytest
.github/workflows/    bootstrap · daily · weekly · tests
```

---

## Tohum listesi

9 Eylul 2026'da Finviz ile on tarama yapildi, **36 aday** belirlendi. Bu liste
`config.SEED_TICKERS` icinde durur ve **huniden bagimsiz** olarak islenir —
ama huninin hangi asamasinda elenecegi de hesaplanip kartta gosterilir
(esiklerin dogru olup olmadigini ogrenmek icin).

**Kol A** (karli, ucuz, kaliteli — 24): ADEA, CRUS, DOCU, DUOL, EXLS, FFIV,
FRSH, G, INOD, LYFT, MNTN, NXT, PATH, PAYS, PCTY, PEGA, QLYS, QTWO, RAMP,
RELY, SONO, WDAY, YOU, ZBRA

**Kol B** (buyume, dusuk/negatif kar — 12): AMPL, AVPT, BRZE, CALX, CPAY,
FLYW, FSLY, GPN, GRND, KVYO, NTAP, ZETA

MNTN, RELY, YOU her iki taramadan da gecti → `track: "both"`.

### On uyarilar (kartta `flags.warnings` alaninda)

- **CPAY, GPN, NTAP** — bu olcekte %20+ ceyreklik buyume organik olamaz;
  muhtemelen satin alma kaynakli. `rev_growth_organic_suspect: true` isaretlenir.
- **LYFT** — F/K 2,27 neredeyse kesin tek seferlik kalem (vergi varligi kaydi
  gibi). Nakit donusumu ve tahakkuk testleri bunu yakalar.
- **BRZE** — 8 Eylul'de %11 dustu. Taze sok; haber akisi one cikarilir.

---

## Huni

| Asama | Ne yapar |
|---|---|
| **0 — Evren** | ABD borsalari, adi hisse. Haric: ADR, SIC 6000-6799 (finans/gayrimenkul), hasilatsiz biyoteknoloji. Piyasa degeri 300M-50.000M USD, fiyat > 5 USD, 30 gunluk ortalama dolar hacmi > 5M USD |
| **1 — Sert filtreler** | Brut marj > %30 **VE** hasilat buyumesi TTM > %5 **VE** (FCF > 0 **VEYA** (buyume > %25 **VE** 40 Kurali ≥ 40)) **VE** net borc/FAVOK < 3 **VE** hisse artisi < %5 **VE** SBC/FCF < 1 |
| **2 — Tuzak eleme** | Beneish M > −1.78 · Altman Z'' < 1.1 (guvenilirse) · Piotroski F < 4 (**sadece Kol A**) · nakit donusumu < 0.7 uc yil ust uste · hasilat **VE** brut marj 2 yildir dusuyor · vade duvari > 1 **ve** FCF < 0 · IPO < 12 ay |
| **3 — Goreli ucuzluk** | **Kol A:** ev_ebit sektor yuzdeligi ≤ 40 **VEYA** FCF verimi > %4; **VE** ev_ebit kendi 5 yil yuzdeligi ≤ 50. **Kol B:** ev_gross_profit sektor ≤ 40 **VE** ev_sales kendi 5 yil ≤ 50. **Ikisinde de:** ima edilen buyume ≤ gerceklesen CAGR × 1.5 |
| **4 — Puanla** | Ucuzluk 25 / Kalite 20 / Saglamlik 15 / Momentum 15 / Kazanc kalitesi 10 / Katalizor 15 (elle). Sektor basina en fazla 10. Ilk 50 |

Her kosu `data/funnel_log.json`'a asama basina kalan sayiyi ve en sik eleme
sebeplerini yazar — esikleri neyin elediğini gormeden iyilestirmek mumkun degil.

---

## Esiklerin gerekcesi

Tum esikler `src/config.py` icindedir ve `data/thresholds.json` olarak servis
edilir. **Dashboard'a sabit gomulu hicbir sayi yoktur.**

| Esik | Deger | Neden |
|---|---|---|
| Brut marj > %30 | Asama 1 | Altinda fiyatlama gucu yok; maliyet soklarini gecirilemez |
| EV/EBIT < 12 yesil | Renk | ~%8 kazanc verimi; uzun vadeli hisse getirisi ile ayni mertebe |
| FCF verimi > %6 yesil | Renk | 10 yillik tahvilin belirgin uzerinde risk primi |
| SBC/FCF < 1 | Asama 1 | 1'in ustunde sirket urettigi tum nakdi calisana hisse olarak dagitiyor |
| Hisse artisi < %5 | Asama 1 | Uzerinde seyrelme, hisse basina degeri buyumeden hizli eritir |
| Net borc/FAVOK < 3 | Asama 1 | Uzerinde faiz artislarinda bilanco kirilgan |
| Beneish M > −1.78 | Asama 2 | Modelin standart "muhtemel manipulator" esigi |
| Altman Z'' < 1.1 | Asama 2 | Imalat disi versiyonun sikinti bolgesi |
| Piotroski F < 4 | Asama 2 (**sadece Kol A**) | Kol B'de zaten dusuk cikar; orada eleme sebebi degil |
| Ima edilen ≤ gerceklesen × 1.5 | Asama 3 | Fiyatin hatasiz gidise bagli olmamasi |
| Iskonto orani %10 | Ters DCF | Uzun vadeli hisse getirisi varsayimi |
| Terminal buyume %3 | Ters DCF | Uzun vadeli nominal GSYH buyumesi |
| Tek pozisyon > %15 | Portfoy | Konsantrasyon uyarisi; ~10 pozisyonlu portfoyde ust sinir |

### Kasitli tasarim kararlari

- **EV kiralama yukumluluklerini ICERMEZ.** Operasyonel kiralamayi borca eklemek
  yazilim/hizmet sirketlerini sistematik olarak pahali gosterir. Ayri kolonda
  (`lease_liabilities`) saklanir.
- **ROIC iki yontemle hesaplanir.** Ozkaynak negatifse (agresif geri alim, orn.
  Dropbox) `(a) NOPAT/(ozkaynak+borc−nakit)` anlamsizdir — payda kuculur, ROIC
  sahte bicimde patlar. O durumda `(b) NOPAT/net isletme varliklari` kullanilir
  ve `roic_method` alanina yazilir.
- **Negatif paydada carpan uretilmez.** EBIT ≤ 0 ise `ev_ebit` **None**'dir,
  buyuk bir sayi degil. Sahte sayi, eksik sayidan tehlikelidir.
- **Eksik veri gri, kirmizi degil.** Veri yoklugu kotu haber degildir.
- **Eksik puan bileseni sifirlanmaz**, agirlik havuzundan cikarilir ve kalanlar
  yeniden normalize edilir; `weight_coverage` ne kadarinin hesaplanabildigini
  soyler.
- **Yuzdelikler hayatta kalanlar uzerinden hesaplanir.** Asama 0-2'de elenen
  sirketler referans havuzunu bozar (iflas riskli sirketler carpanlari yapay
  olarak dusurur).
- **Sektorde 8'den az sirket varsa** tum evrene dusulur ve hucre `*` ile
  isaretlenir — yanilticilik olmasin.

---

## Claude ile calisma akisi

### 1. Claude'a sor

Her kartta ve sirket detay sayfasinda **"Claude'a sor"** butonu var. Sirketin
ozet JSON'unu ve `raw.githubusercontent.com` linkini panoya kopyalar. Sohbete
yapistir.

### 2. Claude analizi yazar

Claude `claude_inbox/<TICKER>.json` dosyasina yazar:

```json
{
  "ticker": "DBX",
  "story": {
    "business_model": "...",
    "moat": "...",
    "why_cheap_diagnosis": "Buyume yavasladi",
    "why_cheap_rationale": "...",
    "bull_case": ["...", "..."],
    "bear_case": ["...", "..."],
    "catalyst": {"type": "...", "expected_date": "2026Q4", "confidence": "orta"},
    "thesis_breakers": ["..."],
    "news_summary": "...",
    "claude_verdict": "Iki satirlik hukum.",
    "updated_at": "2026-09-09"
  },
  "catalyst_score": 70
}
```

### 3. `merge_story()` birlestirir

`run_daily.py` her kosuda cagirir. **Cakismada inbox kazanir.** Inbox yalnizca
`story` ve `decision` bloklarina dokunabilir — sayisal alanlar veri hattinin
sorumlulugundadir.

### 4. Berke karar verir

Sirket detayindaki **Karar kutusu** bir JSON parcasi uretir (AL/BEKLE/ELE +
gerekce). Kopyala → Claude Code'a yapistir, ya da "GitHub'da ac" ile web
duzenleyicisinde ekle.

### Kartlar asla ezilmez

Veri hatti gunde bir tum kartlari yeniden uretir. `preserve_authored()` her
uretimde `story` ve `decision` bloklarini korur — bu koruma olmasa her kosu
Claude'un analizini ve Berke'nin kararini silerdi.

30 gunden eski Claude notlari dashboard'da **soluk** gorunur.

---

## Otomasyon

| Is akisi | Ne zaman | Ne yapar |
|---|---|---|
| **Bootstrap (tohum listesi)** | elle | 36 tohum sirket icin kart uretir — **ilk is bu** |
| **Daily (fiyat ve haber)** | hafta ici 07:00 TSI | fiyat, momentum, haber, kazanc takvimi, portfoy + `merge_story()` |
| **Weekly (huni)** | pazar 05:00 TSI | SEC toplu veriyi gunceller, huniyi bastan calistirir |
| **Tests** | her push | pytest + JSON gecerlilik |

**Degisiklik yoksa commit atilmaz** — `write_json()` icerigi karsilastirir ve
zaman damgalarini karsilastirma disinda tutar.

---

## Test verisi hakkinda

`tests/fixtures.py` icindeki DBX / LSCC / KVYO rakamlari, sirketlerin kamuya
acik FY2025 mali tablolarindan derlenmis **yaklasik** degerlerdir ve
sartnamedeki hedef oranlari uretecek sekilde tutarli hale getirilmistir.
Amac **hesap motorunu** dogrulamaktir, EDGAR verisinin kendisini degil:

| | Hedef | Hesaplanan |
|---|---|---|
| DBX EV/EBIT | ≈ 14.7 | 14.70 |
| DBX FCF verimi | ≈ %9.1 | %9.10 |
| DBX Piotroski F | 6 | 6 |
| DBX Beneish M | ≈ −3.1 | −3.13 |
| DBX ozkaynak negatif | `roic_method="b"`, `z_unreliable=true` | ✓ |
| LSCC EV/Hasilat | ≈ 30 | 30.00 |
| LSCC FCF verimi | ≈ %0.8 | %0.80 |
| LSCC Piotroski F | 5 | 5 |
| LSCC Altman Z'' | ≈ 10.4 | 10.40 |
| KVYO EBIT | < 0 → Kol B | ✓ |
| KVYO EV/Brut kar | ≈ 5.0 | 5.00 |
| KVYO 40 Kurali | ≈ 48.5 | 48.51 |
| KVYO Piotroski F | 4 | 4 |

Gercek EDGAR verisiyle dogrulama `tests/test_live_edgar.py` icindedir
(`RUN_NETWORK_TESTS=1` ile calisir).

---

## GitHub Pages

Ayarlar → Pages → Source: **Deploy from a branch**, Branch: `main`, Folder:
**`/ (root)`**.

Dashboard `data/` klasorunu su sirayla arar: `../data` → `./data` →
`raw.githubusercontent.com`. Bu yuzden Pages hangi klasorden servis edilirse
edilsin calisir, ama `/ (root)` en dogrusudur (veri repoda tek kopya kalir).

Adres: `https://berkehan-nz.github.io/P-Fin/docs/`

---

## Bilinen sinirlar

- **Midas API'si yok** — islemler `data/portfolio.json` icine elle girilir.
  Dashboard'daki form JSON parcasi uretir.
- **Form 4 yalnizca dosyalama SAYISIDIR**, tutar degil. Tutar icin her Form 4'un
  XML'ini ayri cekmek gerekir; ucretsiz kotada evren capinda pahali.
- **Analist hedef fiyatlari puanlamaya girmez** — sistematik olarak iyimserdir.
- **Tam evren taramasi saatler surer.** Haftalik is akisinda calisir; gunluk
  kosuda yalnizca fiyata bagli alanlar tazelenir.
- **Ceyreklik veri yetersizse** metrikler yillik tablodan hesaplanir ve kart
  `data_basis: "annual"` uyarisi tasir.
