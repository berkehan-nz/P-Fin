# Kişisel Finans Ajanı (P-Fin)

Sürekli canlı bir yatırım araştırma ajanı. Her sabah portföy + piyasa brifingi maili atar,
her pozisyon için **gerekçeli ve kaynaklı** aksiyon önerir, gün içi kritik gelişmede uyarır.
Kararları ajan üretir; **işlemleri kullanıcı Midas'ta elle yapar.** Sistem emir göndermez,
broker'a bağlanmaz.

> Bu bir modelin önerisidir, finansal danışmanlık değildir. Başarı ölçütü mutlak getiri değil,
> **XU100 ve TÜFE'ye karşı** getiridir (§2.6).

---

## Değişmezler (pazarlığa kapalı — mimarinin merkezinde)

1. **Sayılar API'den, muhakeme LLM'den.** LLM asla bir sayının kaynağı değildir. Tüm fiyat/
   bilanço/stop `data/facts.py` paketinden gelir (kaynak + zaman damgalı).
2. **Söz tezi başlatır, veri onaylar.** Yorum tek başına alım gerekçesi olamaz.
3. **Her tez bir çürütücüyle gelir.** `refuter` alanı zorunlu; yoksa korkuluk reddeder.
4. **Her girişte çıkış planı.** Stop'suz veya girişin üstünde stop'lu alım reddedilir.
5. **"Bugün bir şey yapma" geçerli ve beklenen çıktıdır.** Aşırı işlem başarısızlıktır.
6. **Başarı kıyasa göredir.** Her rapor XU100 + TÜFE karşısındaki konumu gösterir.

## Mimari

| Katman | Modül | Not |
|---|---|---|
| Hafıza | `pfin/memory/` | `state.json` şeması (panelle sözleşme), atomik store, **özetleme/budama** (§3.4) |
| Veri ($0) | `pfin/data/` | BIST/TEFAS/XU100/TÜFE → **borsapy**; ABD fiyat → **Twelve Data** (sayaçlı); ABD temel → **yfinance**; KAP |
| Sabah turu | `pfin/agent/` | Opus 4.8 + `web_search`/`web_fetch` + **forced tool-use** (yapılandırılmış JSON), prompt caching |
| Korkuluk | `pfin/guardrails/` | §3.3 deterministik süzgeç — model ne derse desin uygulanır |
| Nöbetçi | `pfin/watchman/` | LLM'siz eşik izleyici, **taşınabilir tetikleyici** (§3.1) |
| Rapor | `pfin/report/` | Sabah brifingi + acil uyarı (HTML+text), SMTP |
| P&L | `pfin/pnl/` | Gerçekleşen fill kaydı, ortalama maliyet, kıyas (§3.6) |
| Kaynak karnesi | `pfin/sources/` | İddia→sonuç (§4); Bora Özkent başlangıç, ölçümden muaf değil |
| Bütçe | `pfin/cost/` | Token/$ sayacı, aylık tavan, aşımda self-throttle (§6) |
| Panel | `panel/` | `state.json`'ı okuyan React panel (§3.7) |

## Kurulum

### 1) Sırları GitHub Secrets'a girin (repoya ASLA commit'lemeyin)

`ANTHROPIC_API_KEY`, `TWELVEDATA_API_KEY` (ücretsiz Basic), `EVDS_API_KEY`
([evds3.tcmb.gov.tr](https://evds3.tcmb.gov.tr) — TÜFE/kıyas için ücretsiz), `SMTP_HOST`,
`SMTP_PORT`, `SMTP_USER`, `SMTP_PASS` (Gmail → **uygulama şifresi**), `MAIL_TO`.

Lokal test için `.env.example` → `.env` kopyalayıp doldurun (`.env` gitignore'dadır).

### 2) İlk state ve evren

`config.yaml`'de `universe` (BIST/US/TEFAS) ve `watchlist`'i düzenleyin. İlk `state.json`
otomatik oluşur (`init-state`) ya da elle:

```bash
pip install -r requirements.txt
PYTHONPATH=src python -m pfin.cli init-state --cash 50000
```

### 3) İlk sabah turunu görün (Adım 3 — buraya kadar çalışmadan ileri gidilmez)

- **Elle:** GitHub → Actions → **Sabah Turu** → *Run workflow*. İlk mailiniz gelir; brifing
  ayrıca artefakt olarak yüklenir.
- **Veri katmanını kanıtlayın:** Actions'ta ya da lokal (açık internet gerekir):
  ```bash
  PYTHONPATH=src python -m pfin.cli data-check --symbol ASELS --market BIST
  ```

## Komutlar

```bash
PYTHONPATH=src python -m pfin.cli morning-run [--dry-run] [--no-mail] [--out out]
PYTHONPATH=src python -m pfin.cli sentinel-run [--no-mail]
PYTHONPATH=src python -m pfin.cli record-fill --symbol THYAO --market BIST --side buy \
      --shares 20 --price 255 --stop 240 --thesis "..." --refuter "..." --source "https://..."
PYTHONPATH=src python -m pfin.cli data-check [--symbol ASELS --market BIST]
PYTHONPATH=src python -m pfin.cli show
```

İşlem kaydını GitHub UI'dan da yapabilirsiniz: Actions → **İşlem Kaydı (Fill)** → formu doldurun.

## Otomasyon (GitHub Actions)

- **Sabah Turu** (`morning.yml`): hafta içi ~08:00 TR + elle tetik. Run sonunda `state.json`
  commit'lenir (§3.4 hafıza korunur).
- **Nöbetçi** (`sentinel.yml`): hafta içi 15 dk'da bir, LLM yok. Stop kırılması → acil mail.
- **İşlem Kaydı** (`record-fill.yml`): elle form ile gerçekleşen fiyatı girer.

> GitHub cron gecikebilir; bu kabul edilmiş bir sınırdır. Nöbetçi taşınabilir yazıldı:
> VPS'e geçilse **kod değişmez**, yalnız `sentinel-run`'ı çağıran zamanlayıcı değişir (§3.1).

## Panel

```bash
cd panel && python3 -m http.server 8000   # → http://localhost:8000 (state.json'ı bu klasöre kopyalayın)
```
Kendi React uygulamanız varsa `panel/finans-ajani-panel.jsx`'i import edin (aynı `state.json` şeması).

## Testler

```bash
python -m pytest -q     # korkuluklar, şema/store, sayaç, P&L, bütçe, nöbetçi
```

## Kabul kriterleri (§9)

- [x] Korkuluk: hiçbir alım önerisi stop'suz değil; girişin üstünde stop reddedilir *(test edildi)*
- [x] Her karar gerekçe **ve** ≥1 kaynak linki taşır; kaynaksız öneri reddedilir *(test edildi)*
- [x] Hiçbir sayı LLM metninden türetilmiyor — hepsi `facts` (API) kaynaklı, izlenebilir
- [x] Ajan bazı günler "işlem yok" diyebiliyor (beklenen çıktı)
- [x] Her rapor XU100 ve TÜFE karşısındaki durumu gösteriyor
- [x] Aylık API harcaması sayaçtan okunabiliyor ve tavanı aşınca self-throttle
- [x] `state.json` her run sonunda commit'leniyor; hafıza kaybolmuyor
- [ ] **Her sabah gecikmeden mail geliyor** — Secrets girilip ilk `morning.yml` tetiklenince doğrulanır

> **Not (bu ortam):** Bu repo geliştirme sandbox'ında yazıldı; sandbox'ın egress politikası
> piyasa-veri hostlarını (Yahoo/TradingView/TEFAS) engellediği için canlı veri çekimi **burada**
> kanıtlanamadı. Kod doğru API şekline göre yazıldı ve mantık birim testleriyle doğrulandı;
> canlı veri GitHub Actions'ta (açık internet) `data-check` ile kanıtlanır.

## Bilinçli olarak yapmadıklarımız (§10)

Otomatik emir gönderme yok (Midas public API'si yok), VPS yok (nöbetçi taşınabilir),
13F/hedge fon takibi yok (bayat sinyal), backtest optimizasyonu yok (aşırı uydurma riski —
canlı karne tutulur), gün içi al-sat yok.
