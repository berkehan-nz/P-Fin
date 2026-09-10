"""Merkezi yapilandirma.

KURAL: Kodun hicbir yerinde sihirli sayi olmayacak. Her esik, agirlik, sektor
listesi ve tohum liste burada durur. Dashboard bu dosyadan uretilen
``data/thresholds.json`` dosyasini okur; degerler HTML/JS icine gomulmez.
"""

from __future__ import annotations

import os
from pathlib import Path

# --------------------------------------------------------------------------
# Yollar
# --------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
CARDS_DIR = DATA_DIR / "cards"
INBOX_DIR = ROOT / "claude_inbox"
CACHE_DIR = ROOT / ".cache"
DOCS_DIR = ROOT / "docs"

for _d in (DATA_DIR, CARDS_DIR, INBOX_DIR, CACHE_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------
# Kimlik / anahtarlar
# --------------------------------------------------------------------------
# SEC her istekte gercek bir iletisim adresi tasiyan User-Agent ister; yoksa 403.
SEC_USER_AGENT = os.getenv("SEC_USER_AGENT", "Berkehan Turk berkehan@nexizon.com")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")
FRED_API_KEY = os.getenv("FRED_API_KEY", "")

# SEC saniyede 10 istek siniri koyuyor; guvenli tarafta kaliyoruz.
SEC_RATE_LIMIT_PER_SEC = 8.0
FINNHUB_RATE_LIMIT_PER_MIN = 55  # ucretsiz kota 60/dk

HTTP_TIMEOUT_SEC = 30
HTTP_MAX_RETRIES = 5
HTTP_BACKOFF_BASE_SEC = 2.0  # 2, 4, 8, 16, 32

# --------------------------------------------------------------------------
# TOHUM LISTESI — 9 Eylul 2026 Finviz on taramasi
# --------------------------------------------------------------------------
SEED_DATE = "2026-09-09"
SEED_SOURCE_TAG = "seed_20260909"

# Kol A: karli, ucuz, kaliteli
SEED_TRACK_A = [
    "ADEA", "CRUS", "DOCU", "DUOL", "EXLS", "FFIV", "FRSH", "G",
    "INOD", "LYFT", "MNTN", "NXT", "PATH", "PAYS", "PCTY", "PEGA",
    "QLYS", "QTWO", "RAMP", "RELY", "SONO", "WDAY", "YOU", "ZBRA",
]

# Kol B: buyume, dusuk/negatif kar
SEED_TRACK_B = [
    "AMPL", "AVPT", "BRZE", "CALX", "CPAY", "FLYW",
    "FSLY", "GPN", "GRND", "KVYO", "NTAP", "ZETA",
]

# Her iki taramadan da gecenler
SEED_BOTH_TRACKS = ["MNTN", "RELY", "YOU"]

SEED_TICKERS = sorted(set(SEED_TRACK_A) | set(SEED_TRACK_B))

# Tohum listesini ureten Finviz kriterleri (kartta ve README'de gosterilir)
SEED_SCREEN_CRITERIA = {
    "track_a": {
        "gross_margin_min_pct": 30.0,
        "rev_growth_qoq_min_pct": 5.0,
        "p_fcf_max": 25.0,
        "roi_min_pct": 10.0,
        "debt_to_equity_max": 1.0,
    },
    "track_b": {
        "gross_margin_min_pct": 50.0,
        "rev_growth_qoq_min_pct": 20.0,
        "p_sales_max": 6.0,
    },
    "common": {
        "country": "USA",
        "market_cap_musd_min": 300.0,
        "market_cap_musd_max": 50_000.0,
        "price_min_usd": 5.0,
        "avg_volume_min_shares": 500_000,
    },
}

# Tohum listesi islenirken elle konulacak on uyarilar.
# Bunlar kartin flags.warnings alanina yazilir.
SEED_PREWARNINGS = {
    "CPAY": [
        "Bu olcekte %20+ ceyreklik buyume organik olamaz; buyume muhtemelen "
        "satin alma kaynakli. 10-K/8-K devralma kontrolu gerekli.",
    ],
    "GPN": [
        "Bu olcekte %20+ ceyreklik buyume organik olamaz; buyume muhtemelen "
        "satin alma kaynakli. 10-K/8-K devralma kontrolu gerekli.",
    ],
    "NTAP": [
        "Bu olcekte %20+ ceyreklik buyume organik olamaz; buyume muhtemelen "
        "satin alma kaynakli. 10-K/8-K devralma kontrolu gerekli.",
    ],
    "LYFT": [
        "F/K 2,27 seviyesinde — neredeyse kesin tek seferlik kalem "
        "(ornegin ertelenmis vergi varligi kaydi). Nakit donusumu ve "
        "tahakkuk testleri dogrulamali.",
    ],
    "BRZE": [
        "8 Eylul 2026'da %11 dustu. Taze sok; son kazanc raporu ve haber "
        "akisi one cikarilmali.",
    ],
}

# On uyarisi olan ve organik buyume supheli olarak isaretlenecek sirketler
SEED_FORCE_ORGANIC_SUSPECT = ["CPAY", "GPN", "NTAP"]

# --------------------------------------------------------------------------
# HUNI — Asama 0: Evren
# --------------------------------------------------------------------------
UNIVERSE = {
    "market_cap_musd_min": 300.0,
    "market_cap_musd_max": 50_000.0,
    "price_min_usd": 5.0,
    "avg_dollar_volume_30d_min_usd": 5_000_000.0,
    # Haric tutulan SIC araligi: finans, sigorta, gayrimenkul
    "excluded_sic_ranges": [(6000, 6799)],
    # Hasilatsiz biyoteknoloji (SIC 2836/8731 + hasilat esigi altinda)
    "biotech_sic_codes": [2836, 8731],
    "biotech_min_revenue_musd": 10.0,
    "exclude_adr": True,
    "allowed_exchanges": ["NYSE", "Nasdaq", "NASDAQ", "NYSE American", "NYSEAMERICAN", "AMEX"],
}

# --------------------------------------------------------------------------
# HUNI — Asama 1: Sert filtreler
# --------------------------------------------------------------------------
STAGE1 = {
    # ILKE: sert filtre BILINEN KOTU degeri eler, VERI YOKLUGUNU elemez.
    # Bir XBRL etiketi eslesmedigi icin sirketi atmak, etiketleme bicimine
    # gore sistematik ve GORUNMEZ bir yanlilik yaratir — brut marji
    # hesaplanamayan sirket, brut marji dusuk sirket demek degildir.
    # Eksik girdiler isaretlenip tasinir; Asama 3 zaten sayiyi gercekten
    # gerektirdiginde eleyecektir.
    "kill_on_missing_data": False,
    "gross_margin_min_pct": 30.0,
    "rev_growth_ttm_min_pct": 5.0,
    # FCF > 0  VEYA  (buyume > X VE Rule of 40 >= Y)
    "high_growth_exemption_growth_pct": 25.0,
    "high_growth_exemption_rule40_min": 40.0,
    "net_debt_to_ebitda_max": 3.0,
    "share_count_growth_max_pct": 5.0,
    # Yillik hisse artisi tek seferlik olaylarla sisebilir: IPO'da imtiyazli
    # hisse donusumu (MNTN %268), konvertibl itfasi (QTWO), eski SPAC
    # seyrelmesi (AVPT). Bunlar surekli seyrelme DEGILDIR. Son iki ceyrekte
    # hisse sayisi ardisik dusuyorsa yillik artis affedilir.
    "share_count_recent_decline_exempts": True,
    "sbc_to_fcf_max": 1.0,
}

# --------------------------------------------------------------------------
# HUNI — Asama 2: Tuzak eleme
# --------------------------------------------------------------------------
STAGE2 = {
    # Altman Z'' abonelik sirketlerinde kirilir: pesin tahsil edilen yillik
    # bedel ERTELENMIS GELIR olarak kisa vadeli yukumluluge yazilir, isletme
    # sermayesi negatife doner ve model "iflas bolgesi" der. FRSH -1,26
    # cikiyordu; oysa 665 mn $ net nakdi ve hic borcu yok.
    "z_deferred_revenue_share_of_current_liabilities": 0.40,
    "beneish_m_max": -1.78,          # ustunde ise manipulasyon suphesi
    "altman_z_min": 1.1,             # altinda ise sikinti bolgesi
    "piotroski_f_min_track_a": 4,    # altinda ise ele (SADECE Kol A)
    "cash_conversion_min": 0.7,
    "cash_conversion_consecutive_years": 3,
    "declining_years": 2,            # hasilat VE brut marj kac yildir dusuyor
    "maturity_wall_max": 1.0,        # 2 yilda vadesi gelen borc / nakit
    "ipo_lockup_months": 12,
}

# --------------------------------------------------------------------------
# HUNI — Asama 3: Goreli ucuzluk
# --------------------------------------------------------------------------
STAGE3 = {
    "track_a": {
        "ev_ebit_sector_pct_max": 40.0,
        "fcf_yield_min_pct": 4.0,
        "ev_ebit_own_5y_pct_max": 50.0,
    },
    "track_b": {
        "ev_gross_profit_sector_pct_max": 40.0,
        "ev_sales_own_5y_pct_max": 50.0,
    },
    # Her iki kolda: ima edilen buyume <= gerceklesen CAGR * carpan.
    # CARPIM TEK BASINA YETMEZ: CAGR %0,3 olan bir sirkette esik %0,45'e
    # duser ve %7,7'lik makul bir ima edilen buyume "asiri" sayilir.
    # Bu yuzden mutlak bir pay da eklenir; esik ikisinin BUYUGU olur.
    "implied_growth_vs_cagr_max_multiple": 1.5,
    "implied_growth_absolute_headroom_pct": 5.0,
    # Kol B tanimi: EBIT <= 0 VEYA faaliyet marji < X
    "track_b_operating_margin_pct": 5.0,
}

# --------------------------------------------------------------------------
# HUNI — Asama 4: Puanlama
# --------------------------------------------------------------------------
# AGIRLIK GEREKCELERI
# Momentum 15 -> 5: bu sistem 1-2 yillik YENIDEN FIYATLANMA ariyor. Yuksek
# 6/12 aylik getiriyi odullendirmek, yeniden fiyatlanmasi COKTAN OLMUS
# isimleri one cikarir — tam olarak aramadigimiz sey. Momentum artik
# "dusen bicak degil" olcusu; kucuk agirlikla kaliyor cunku serbest dususte
# olan bir hisseye girmek de ayri bir risk.
# Katalizor 15 -> 25: acilan 10 puan buraya. Yeniden fiyatlanmayi tetikleyecek
# somut bir olayin varligi, gecmis fiyat hareketinden cok daha belirleyici.
SCORE_WEIGHTS = {
    "value": 25,
    "quality": 20,
    "safety": 15,
    "momentum": 5,
    "earnings_quality": 10,
    "catalyst": 25,  # elle girilir, otomatik hesaplanmaz
}

# Bir blokta alt metriklerin ne kadari hesaplanabildi? Dusuk kapsama, puanin
# az sayida metrige dayandigi anlamina gelir. Puani CEZALANDIRMAK yanlis
# olurdu (veri yoklugu kotu haber degildir), ama o blogun toplam puandaki
# AGIRLIGI azaltilmali: az bilgi, az soz hakki.
COVERAGE = {
    "min_weight_factor": 0.35,   # kapsama 0 olsa bile blok tamamen susmasin
    "low_coverage_flag": 0.60,   # bunun altinda kartta "veri yetersiz" rozeti
}

# Puanlamada uc degerlerin yuzdelik siralamasini bozmasini engelleyen tavanlar.
# GORUNEN DEGER DEGISMEZ — yalnizca siralama icin kirpilir.
# NTAP'in ROIC'i %352 cikiyor cunku agresif geri alim sonrasi yatirilan
# sermaye sifira yaklasiyor; bu, sirketin digerlerinden 20 kat iyi oldugu
# anlamina gelmez, paydanin kucuk oldugu anlamina gelir.
SCORE_CAPS = {
    "roic": (None, 60.0),
    "cash_conversion": (None, 5.0),
    "interest_coverage": (None, 100.0),
    "gross_profitability": (None, 2.0),
    "current_ratio": (None, 10.0),
}

# Her ana puanin hangi alt metriklerden olustugu ve alt agirliklari.
# Alt bilesenler sektor ici yuzdelik olarak 0-100'e olceklenir.
# "invert": dusuk deger iyi demek (orn. EV/EBIT)
SCORE_COMPONENTS = {
    "value": [
        {"metric": "ev_ebit", "weight": 0.30, "invert": True},
        {"metric": "ev_gross_profit", "weight": 0.20, "invert": True},
        {"metric": "ev_sales", "weight": 0.15, "invert": True},
        {"metric": "fcf_yield_ev", "weight": 0.25, "invert": False},
        {"metric": "earnings_yield", "weight": 0.10, "invert": False},
    ],
    "quality": [
        {"metric": "roic", "weight": 0.30, "invert": False},
        {"metric": "gross_profitability", "weight": 0.20, "invert": False},
        {"metric": "gross_margin", "weight": 0.20, "invert": False},
        {"metric": "fcf_margin", "weight": 0.15, "invert": False},
        {"metric": "rule_of_40", "weight": 0.15, "invert": False},
    ],
    "safety": [
        {"metric": "net_debt_to_ebitda", "weight": 0.30, "invert": True},
        {"metric": "interest_coverage", "weight": 0.20, "invert": False},
        {"metric": "current_ratio", "weight": 0.20, "invert": False},
        {"metric": "altman_z", "weight": 0.30, "invert": False},
    ],
    # Momentum artik "kim daha cok kazandirdi" degil, "dusus durdu mu"
    # olcuyor. Mutlak getiri ve zirveye yakinlik KASITLI OLARAK cikarildi:
    # zirveye yakin olmak, yeniden fiyatlanma firsatinin AZALDIGI anlamina
    # gelir. Bu iki alan kartta bilgi olarak durmaya devam ediyor.
    "momentum": [
        {"metric": "rel_strength_3m", "weight": 0.60, "invert": False},
        {"metric": "rel_strength_6m", "weight": 0.40, "invert": False},
    ],
    "earnings_quality": [
        {"metric": "cash_conversion", "weight": 0.30, "invert": False},
        {"metric": "sloan_accruals", "weight": 0.25, "invert": True},
        {"metric": "beneish_m", "weight": 0.20, "invert": True},
        {"metric": "piotroski_f", "weight": 0.25, "invert": False},
    ],
}

MAX_PER_SECTOR = 12       # Asama 4 ciktisinda sektor basina en fazla
FINAL_CANDIDATE_COUNT = 50

# --------------------------------------------------------------------------
# Ters DCF
# --------------------------------------------------------------------------
REVERSE_DCF = {
    "discount_rate": 0.10,
    "terminal_growth": 0.03,
    "projection_years": 10,
    "growth_search_min": -0.50,
    "growth_search_max": 1.50,
}

# --------------------------------------------------------------------------
# Tek seferlik kalem / organik buyume tespiti
# --------------------------------------------------------------------------
# Serbest dususte olan hisse: son 3 ayda endekse gore bu kadar geride ise
# "dusen bicak" uyarisi. ELEME SEBEBI DEGIL — deger yatiriminda en iyi
# girisler cogu zaman dususten sonra gelir — ama gormeden girilmemeli.
FALLING_KNIFE_REL_STRENGTH_3M = -15.0

ANOMALY = {
    # net kar / EBIT bu oranin ustundeyse tek seferlik kalem suphesi
    "net_income_to_ebit_ratio_max": 2.0,
    # efektif vergi orani negatifse tek seferlik kalem suphesi
    "negative_tax_rate_flag": True,
    # Net kar hasilatin bu payindan kucukse nakit donusumu oranini hesaplama;
    # payda sifira yakinken oran anlamsiz buyur.
    "cash_conversion_min_net_income_share": 0.02,
    # organik buyume suphesi: buyume > X VE piyasa degeri > Y
    "organic_suspect_growth_pct": 20.0,
    "organic_suspect_market_cap_musd": 10_000.0,
    # ya da serefiye yillik artisi > Z
    "organic_suspect_goodwill_growth_pct": 15.0,
}

# --------------------------------------------------------------------------
# RENK ESIKLERI
# --------------------------------------------------------------------------
# direction "high_good": deger >= green_min yesil, >= yellow_min sari, altinda kirmizi
# direction "low_good" : deger <= green_max yesil, <= yellow_max sari, ustunde kirmizi
# Veri yoksa gri.
THRESHOLDS = {
    "ev_ebit": {
        "label": "EV/FVOK", "unit": "x", "direction": "low_good",
        "green_max": 12, "yellow_max": 18,
        "help": "Isletme degerinin faiz ve vergi oncesi kara orani. Sermaye "
                "yapisindan bagimsiz F/K. Tuzak: tek seferlik kalemler EBIT'i "
                "sisirir, dususte ucuz gorunur.",
        "formula": "EV / EBIT (TTM)",
    },
    "ev_ebitda": {
        "label": "EV/FAVOK", "unit": "x", "direction": "low_good",
        "green_max": 9, "yellow_max": 14,
        "help": "Amortisman oncesi. Sermaye yogun sirketlerde yanilticidir; "
                "yatirim harcamasini gormezden gelir.",
        "formula": "EV / EBITDA (TTM)",
    },
    "ev_gross_profit": {
        "label": "EV/Brut kar", "unit": "x", "direction": "low_good",
        "green_max": 8, "yellow_max": 15,
        "help": "Kar etmeyen ama yuksek brut marjli yazilim sirketleri icin "
                "en saglam deger olcusu. Brut kar manipulasyona en dayanikli kalem.",
        "formula": "EV / Brut kar (TTM)",
    },
    "ev_sales": {
        "label": "EV/Hasilat", "unit": "x", "direction": "low_good",
        "green_max": 4, "yellow_max": 7,
        "help": "En kaba olcu. Marj farklarini gormezden gelir; sadece ayni "
                "sektor icinde karsilastirilabilir.",
        "formula": "EV / Hasilat (TTM)",
    },
    "fcf_yield_ev": {
        "label": "FCF verimi (EV)", "unit": "%", "direction": "high_good",
        "green_min": 6, "yellow_min": 3,
        "help": "Serbest nakit akisinin isletme degerine orani. Tahvil faizi ile "
                "dogrudan karsilastirilabilir. Tuzak: tek seferlik tahsilatlar.",
        "formula": "(Isletme nakit akisi - Yatirim harcamasi) / EV",
    },
    "fcf_yield_mcap": {
        "label": "FCF verimi (Piyasa degeri)", "unit": "%", "direction": "high_good",
        "green_min": 6, "yellow_min": 3,
        "help": "Hissedara dusen nakit verimi. Borclu sirketlerde EV versiyonundan "
                "yuksek cikar; ikisini birlikte oku.",
        "formula": "FCF / Piyasa degeri",
    },
    "pe": {
        "label": "F/K", "unit": "x", "direction": "low_good",
        "green_max": 15, "yellow_max": 25,
        "help": "Fiyat / net kar. Tek seferlik kalemlere en acik oran. "
                "one_off_earnings bayragi varsa bu sayiyi yok say.",
        "formula": "Fiyat / Hisse basina net kar (TTM)",
    },
    "earnings_yield": {
        "label": "Kazanc verimi", "unit": "%", "direction": "high_good",
        "green_min": 8, "yellow_min": 5,
        "help": "EBIT/EV. Greenblatt'in 'sihirli formul' getirisi. EV/EBIT'in tersi.",
        "formula": "EBIT / EV",
    },
    "peg": {
        "label": "PEG", "unit": "x", "direction": "low_good",
        "green_max": 1.0, "yellow_max": 2.0,
        "help": "F/K bolu buyume. Buyume tahmini yanlissa oran anlamsizdir.",
        "formula": "F/K / (hasilat buyumesi %)",
    },
    "rev_growth_ttm": {
        "label": "Hasilat buyumesi (TTM)", "unit": "%", "direction": "high_good",
        "green_min": 15, "yellow_min": 5,
        "help": "Son 12 ayin bir onceki 12 aya gore buyumesi. Satin alma "
                "kaynakli buyume organik degildir; rev_growth_organic_suspect'e bak.",
        "formula": "(TTM hasilat / onceki TTM hasilat) - 1",
    },
    "rev_cagr_3y": {
        "label": "Hasilat BYBO (3y)", "unit": "%", "direction": "high_good",
        "green_min": 15, "yellow_min": 5,
        "help": "3 yillik bilesik yillik buyume orani. Tek yillik siciramalari yumusatir.",
        "formula": "(Hasilat_t / Hasilat_t-3)^(1/3) - 1",
    },
    "gross_margin": {
        "label": "Brut marj", "unit": "%", "direction": "high_good",
        "green_min": 60, "yellow_min": 30,
        "help": "Fiyatlama gucunun en dogrudan gostergesi. Dusen brut marj "
                "rekabet baskisinin ilk isaretidir.",
        "formula": "Brut kar / Hasilat",
    },
    "operating_margin": {
        "label": "Faaliyet marji", "unit": "%", "direction": "high_good",
        "green_min": 20, "yellow_min": 8,
        "help": "EBIT / hasilat. Olcek ekonomisinin calisip calismadigini gosterir.",
        "formula": "EBIT / Hasilat",
    },
    "fcf_margin": {
        "label": "FCF marji", "unit": "%", "direction": "high_good",
        "green_min": 20, "yellow_min": 10,
        "help": "Her 100 dolar hasilattan kalan serbest nakit. Muhasebe karindan "
                "daha zor manipule edilir.",
        "formula": "FCF / Hasilat",
    },
    "roic": {
        "label": "ROIC", "unit": "%", "direction": "high_good",
        "green_min": 15, "yellow_min": 8,
        "help": "Yatirilan sermayenin getirisi. Sermaye maliyetinin (~%10) "
                "uzerinde olmali. Ozkaynak negatifse (b) yontemi kullanilir.",
        "formula": "NOPAT / Yatirilan sermaye",
    },
    "gross_profitability": {
        "label": "Brut karlilik", "unit": "x", "direction": "high_good",
        "green_min": 0.33, "yellow_min": 0.20,
        "help": "Novy-Marx olcusu: brut kar / toplam varlik. Uzun vadede "
                "F/K'dan daha guclu bir getiri ongoruculugu var.",
        "formula": "Brut kar / Toplam varlik",
    },
    "rule_of_40": {
        "label": "40 Kurali", "unit": "", "direction": "high_good",
        "green_min": 40, "yellow_min": 30,
        "help": "Hasilat buyumesi % + FCF marji %. Yazilimda buyume/karlilik "
                "dengesinin standart olcusu.",
        "formula": "Hasilat buyumesi % + FCF marji %",
    },
    "rule_of_40_ebitda": {
        "label": "40 Kurali (FAVOK)", "unit": "", "direction": "high_good",
        "green_min": 40, "yellow_min": 30,
        "help": "FCF yerine EBITDA marji ile. FCF versiyonu ile arasindaki fark "
                "buyuk olcude hisse bazli odemedir (SBC).",
        "formula": "Hasilat buyumesi % + EBITDA marji %",
    },
    "piotroski_f": {
        "label": "Piotroski F", "unit": "/9", "direction": "high_good",
        "green_min": 7, "yellow_min": 5,
        "help": "9 maddelik temel saglik kontrol listesi. 4 ve alti zayif "
                "bilanco/nakit akisi demek.",
        "formula": "9 ikili testin toplami",
    },
    "altman_z": {
        "label": "Altman Z''", "unit": "", "direction": "high_good",
        "green_min": 2.6, "yellow_min": 1.1,
        "help": "Iflas riski skoru (imalat disi versiyon). Ozkaynak negatifse "
                "anlamsizdir; z_unreliable bayragina bak.",
        "formula": "3.25 + 6.56A + 3.26B + 6.72C + 1.05D",
    },
    "beneish_m": {
        "label": "Beneish M", "unit": "", "direction": "low_good",
        "green_max": -2.22, "yellow_max": -1.78,
        "help": "Kazanc manipulasyonu olasiligi. -1.78 ustu 'muhtemel manipulator'. "
                "Hizli buyuyen saglikli sirketlerde de yanlis alarm verebilir.",
        "formula": "8 degiskenli Beneish modeli",
    },
    "sloan_accruals": {
        "label": "Sloan tahakkuk", "unit": "", "direction": "low_good",
        "green_max": 0.0, "yellow_max": 0.10,
        "help": "Karin ne kadari nakde donmemis. Yuksek tahakkuk gelecek yil "
                "dusuk getiri ile iliskili.",
        "formula": "(Net kar - CFO - CFI) / Toplam varlik",
    },
    "cash_conversion": {
        "label": "Nakit donusumu", "unit": "x", "direction": "high_good",
        "green_min": 1.0, "yellow_min": 0.7,
        "help": "Isletme nakit akisi / net kar. 1'in altinda surekli kalmasi "
                "karin kagit uzerinde kaldigini gosterir.",
        "formula": "CFO / Net kar",
    },
    "sbc_to_revenue": {
        "label": "SBC / Hasilat", "unit": "%", "direction": "low_good",
        "green_max": 8, "yellow_max": 15,
        "help": "Hisse bazli odemenin hasilata orani. Gercek bir maliyettir; "
                "FCF'te gorunmez ama hisse sayisini artirir.",
        "formula": "Hisse bazli odeme / Hasilat",
    },
    "sbc_to_fcf": {
        "label": "SBC / FCF", "unit": "x", "direction": "low_good",
        "green_max": 0.3, "yellow_max": 1.0,
        "help": "1'in ustunde ise sirket urettigi tum nakiti calisanlara "
                "hisse olarak dagitiyor demektir.",
        "formula": "Hisse bazli odeme / FCF",
    },
    "share_count_change_1y": {
        "label": "Hisse sayisi degisimi", "unit": "%", "direction": "low_good",
        "green_max": 0, "yellow_max": 3,
        "help": "Negatif = geri alim (iyi). Pozitif = seyrelme. SBC agir "
                "sirketlerde geri alimlar sadece seyrelmeyi dengeler.",
        "formula": "Yillik seyreltilmis hisse sayisi degisimi",
    },
    "net_debt_to_ebitda": {
        "label": "Net borc / FAVOK", "unit": "x", "direction": "low_good",
        "green_max": 0, "yellow_max": 3,
        "help": "Negatif = net nakit (yesil). 3'un ustu, faiz artislarinda "
                "kirilgan bilanco demek.",
        "formula": "(Finansal borc - Nakit) / EBITDA",
    },
    "interest_coverage": {
        "label": "Faiz karsilama", "unit": "x", "direction": "high_good",
        "green_min": 8, "yellow_min": 3,
        "help": "EBIT / faiz gideri. 3'un altinda operasyonel bir aksama "
                "dogrudan temerrut riskine donusur.",
        "formula": "EBIT / Faiz gideri",
    },
    "current_ratio": {
        "label": "Cari oran", "unit": "x", "direction": "high_good",
        "green_min": 2.0, "yellow_min": 1.2,
        "help": "Donen varlik / kisa vadeli yukumluluk. Yazilimda ertelenmis "
                "gelir bu orani yapay olarak dusurur.",
        "formula": "Donen varlik / Kisa vadeli yukumluluk",
    },
    "maturity_wall_2y": {
        "label": "Vade duvari (2y)", "unit": "x", "direction": "low_good",
        "green_max": 0.5, "yellow_max": 1.0,
        "help": "2 yilda vadesi gelen borc / nakit. 1'in ustu ve FCF negatifse "
                "yeniden finansman riski var.",
        "formula": "2 yilda vadesi gelen borc / Nakit",
    },
    "implied_growth": {
        "label": "Ima edilen buyume", "unit": "%", "direction": "low_good",
        "green_max": 8, "yellow_max": 15,
        "help": "Bugunku fiyatin 10 yil boyunca varsaydigi FCF buyumesi. "
                "Sirketin gercek buyumesiyle karsilastir.",
        "formula": "Ters DCF (r=%10, terminal g=%3)",
    },
    "implied_vs_actual_growth": {
        "label": "Ima edilen / Gercek buyume", "unit": "x", "direction": "low_good",
        "green_max": 1.0, "yellow_max": 1.5,
        "help": "1'in altinda: piyasa sirketin mevcut buyumesini bile "
                "fiyatlamamis. 1.5 ustu: fiyat hatasiz gidise bagli.",
        "formula": "implied_growth / rev_cagr_3y",
    },
    "return_6m": {
        "label": "6 aylik getiri", "unit": "%", "direction": "high_good",
        "green_min": 10, "yellow_min": 0,
        "help": "Mutlak fiyat getirisi. Tek basina karar araci degil.",
        "formula": "Fiyat / 6 ay onceki fiyat - 1",
    },
    "return_12m": {
        "label": "12 aylik getiri", "unit": "%", "direction": "high_good",
        "green_min": 15, "yellow_min": 0,
        "help": "Mutlak 12 aylik fiyat getirisi.",
        "formula": "Fiyat / 12 ay onceki fiyat - 1",
    },
    "rel_strength_3m": {
        "label": "3 ay goreli getiri", "unit": "%", "direction": "high_good",
        "green_min": 0, "yellow_min": -15,
        "help": "Nasdaq 100'e gore son 3 aylik fark. Bu sistemde momentum "
                "'kim kazandirdi' degil 'dusus durdu mu' olcusudur; sert "
                "negatif deger dusen bicak uyarisidir.",
        "formula": "Hisse 3a getirisi - QQQ 3a getirisi",
    },
    "return_3m": {
        "label": "3 aylik getiri", "unit": "%", "direction": "high_good",
        "green_min": 5, "yellow_min": -10,
        "help": "Son 3 ayin mutlak fiyat getirisi.",
        "formula": "Fiyat / 3 ay onceki fiyat - 1",
    },
    "rel_strength_6m": {
        "label": "6 ay goreli getiri", "unit": "%", "direction": "high_good",
        "green_min": 0, "yellow_min": -15,
        "help": "Nasdaq 100'e gore fark. Sert negatif deger 'deger tuzagi' "
                "riskinin en erken sinyalidir.",
        "formula": "Hisse 6a getirisi - QQQ 6a getirisi",
    },
    "rel_strength_12m": {
        "label": "12 ay goreli getiri", "unit": "%", "direction": "high_good",
        "green_min": 0, "yellow_min": -20,
        "help": "Nasdaq 100'e gore 12 aylik fark.",
        "formula": "Hisse 12a getirisi - QQQ 12a getirisi",
    },
    "pct_off_52w_high": {
        "label": "52 hafta zirveden uzaklik", "unit": "%", "direction": "low_good",
        "green_max": 15, "yellow_max": 35,
        "help": "Zirveden ne kadar uzakta. Derin dususler hem firsat hem "
                "kirilma sinyali olabilir; hikayeye bak.",
        "formula": "1 - Fiyat / 52 hafta zirve",
    },
}

# Kart uzerinde dort blok halinde gosterilecek metrik sirasi
METRIC_BLOCKS = {
    "Degerleme": [
        "ev_ebit", "ev_ebitda", "ev_gross_profit", "ev_sales",
        "fcf_yield_ev", "fcf_yield_mcap", "pe", "earnings_yield", "peg",
        "implied_growth", "implied_vs_actual_growth",
    ],
    "Buyume": [
        "rev_growth_ttm", "rev_cagr_3y", "gross_margin", "operating_margin",
        "fcf_margin", "rule_of_40", "rule_of_40_ebitda",
    ],
    "Kalite": [
        "roic", "gross_profitability", "cash_conversion",
        "sbc_to_revenue", "sbc_to_fcf", "share_count_change_1y", "piotroski_f",
    ],
    "Saglamlik ve Tuzak": [
        "net_debt_to_ebitda", "interest_coverage", "current_ratio",
        "maturity_wall_2y", "altman_z", "beneish_m", "sloan_accruals",
    ],
}

# Kart izgarasinda kol basina gosterilen uc anahtar metrik
HEADLINE_METRICS = {
    "A": ["ev_ebit", "fcf_yield_ev", "roic"],
    "B": ["ev_sales", "rev_growth_ttm", "rule_of_40"],
}

# --------------------------------------------------------------------------
# Sektorler — SEC SIC kodu ana gruplari
# --------------------------------------------------------------------------
SIC_MAJOR_GROUPS = {
    (100, 999): "Tarim",
    (1000, 1499): "Madencilik",
    (1500, 1799): "Insaat",
    (2000, 2199): "Gida ve tutun",
    (2200, 2399): "Tekstil ve giyim",
    (2400, 2699): "Orman urunleri ve kagit",
    (2700, 2799): "Basim ve yayin",
    (2800, 2899): "Kimya ve ilac",
    (2900, 2999): "Petrol rafinaj",
    (3000, 3299): "Kaucuk, plastik, cam",
    (3300, 3499): "Metal",
    (3500, 3599): "Makine ve bilgisayar donanimi",
    (3600, 3699): "Elektronik ve elektrikli ekipman",
    (3700, 3799): "Ulasim ekipmani",
    (3800, 3899): "Olcum ve tibbi cihaz",
    (3900, 3999): "Cesitli imalat",
    (4000, 4799): "Ulastirma",
    (4800, 4899): "Iletisim",
    (4900, 4999): "Kamu hizmetleri",
    (5000, 5199): "Toptan ticaret",
    (5200, 5999): "Perakende",
    (6000, 6799): "Finans ve gayrimenkul",
    (7000, 7299): "Konaklama ve kisisel hizmet",
    # 7300'ler tek grup olunca evrenin buyuk kismi ayni kovaya dusuyor ve
    # sektor kotasi (en fazla 10) listenin yarisini kesiyor. Yazilim/hizmet
    # alt gruplari ayristirildi.
    (7370, 7372): "Yazilim ve programlama",
    (7373, 7374): "Veri isleme ve sistem entegrasyonu",
    (7375, 7379): "Bilgi hizmetleri",
    (7300, 7369): "Is hizmetleri",
    (7380, 7399): "Diger is hizmetleri",
    (7400, 7999): "Cesitli hizmetler",
    (8000, 8099): "Saglik hizmetleri",
    (8200, 8299): "Egitim",
    (8700, 8799): "Muhendislik ve arastirma",
    (9000, 9999): "Kamu ve diger",
}

# Sektor yuzdeligi hesabi icin bir grupta en az kac sirket olmali;
# altindaysa tum evrene gore hesaplanir.
MIN_PEERS_FOR_SECTOR_PERCENTILE = 8

# --------------------------------------------------------------------------
# Portfoy
# --------------------------------------------------------------------------
PORTFOLIO = {
    "max_position_weight_pct": 15.0,
    "earnings_warning_days": 7,
    "tax_year_warning_days": 30,        # 1 yil dolmasina kalan gun
    "review_overdue_grace_days": 0,
    "benchmarks": {"nasdaq100": "QQQ", "sp500": "SPY"},
    "default_broker": "Midas",
}

# --------------------------------------------------------------------------
# Makro (FRED seri kodlari)
# --------------------------------------------------------------------------
FRED_SERIES = {
    "us10y": {"id": "DGS10", "label": "ABD 10 yillik tahvil", "unit": "%"},
    "cpi_yoy": {"id": "CPIAUCSL", "label": "TUFE (yillik)", "unit": "%", "transform": "yoy_pct"},
    "unemployment": {"id": "UNRATE", "label": "Issizlik", "unit": "%"},
    "ism_proxy": {"id": "INDPRO", "label": "Sanayi uretimi (yillik)", "unit": "%", "transform": "yoy_pct"},
    "fed_funds": {"id": "DFF", "label": "Fed politika faizi", "unit": "%"},
}

# --------------------------------------------------------------------------
# Fiyat kaynaklari
# --------------------------------------------------------------------------
STOOQ_URL = "https://stooq.com/q/d/l/?s={symbol}.us&i=d"
BENCHMARK_TICKERS = ["QQQ", "SPY"]
PRICE_HISTORY_DAYS = 800          # ~3 yil; 52 hafta ve 12 aylik getiri icin yeterli
AVG_VOLUME_WINDOW_DAYS = 30

# --------------------------------------------------------------------------
# EDGAR toplu veri
# --------------------------------------------------------------------------
EDGAR = {
    "company_tickers_url": "https://www.sec.gov/files/company_tickers.json",
    "bulk_zip_url": "https://www.sec.gov/files/dera/data/financial-statement-data-sets/{year}q{quarter}.zip",
    "companyfacts_url": "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json",
    "submissions_url": "https://data.sec.gov/submissions/CIK{cik:010d}.json",
    "quarters_to_load": 8,
    "sqlite_cache": "edgar_bulk.sqlite",
}

FINNHUB = {
    "news_url": "https://finnhub.io/api/v1/company-news",
    "earnings_url": "https://finnhub.io/api/v1/calendar/earnings",
    "news_lookback_days": 30,
    "max_news_per_ticker": 8,
}

FRED_URL = "https://api.stlouisfed.org/fred/series/observations"

# --------------------------------------------------------------------------
# Dashboard'a servis edilecek esik dosyasi
# --------------------------------------------------------------------------
def thresholds_payload() -> dict:
    """``data/thresholds.json`` icerigi. Dashboard renkleri buradan okur."""
    return {
        "thresholds": THRESHOLDS,
        "score_plain": SCORE_PLAIN,
        "metric_blocks": METRIC_BLOCKS,
        "headline_metrics": HEADLINE_METRICS,
        "score_weights": SCORE_WEIGHTS,
        "stage1": STAGE1,
        "stage2": STAGE2,
        "stage3": STAGE3,
        "universe": {k: v for k, v in UNIVERSE.items() if k != "excluded_sic_ranges"},
        "reverse_dcf": REVERSE_DCF,
        "portfolio": {k: v for k, v in PORTFOLIO.items() if k != "benchmarks"},
        "seed": {
            "date": SEED_DATE,
            "criteria": SEED_SCREEN_CRITERIA,
            "track_a": SEED_TRACK_A,
            "track_b": SEED_TRACK_B,
            "both_tracks": SEED_BOTH_TRACKS,
        },
    }


def sector_for_sic(sic: int | str | None) -> str:
    """SIC kodunu ana gruba cevirir."""
    if sic is None or sic == "":
        return "Bilinmiyor"
    try:
        code = int(sic)
    except (TypeError, ValueError):
        return "Bilinmiyor"
    for (lo, hi), name in SIC_MAJOR_GROUPS.items():
        if lo <= code <= hi:
            return name
    return "Bilinmiyor"


def is_excluded_sic(sic: int | str | None) -> bool:
    """Finans/gayrimenkul gibi haric tutulan SIC araliklari."""
    try:
        code = int(sic)
    except (TypeError, ValueError):
        return False
    return any(lo <= code <= hi for lo, hi in UNIVERSE["excluded_sic_ranges"])


def color_for(metric: str, value: float | None) -> str:
    """Bir metrik degeri icin renk kodu dondurur."""
    if value is None:
        return "gray"
    spec = THRESHOLDS.get(metric)
    if spec is None:
        return "gray"
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "gray"
    if v != v:  # NaN
        return "gray"
    if spec["direction"] == "low_good":
        if v <= spec["green_max"]:
            return "green"
        if v <= spec["yellow_max"]:
            return "yellow"
        return "red"
    if v >= spec["green_min"]:
        return "green"
    if v >= spec["yellow_min"]:
        return "yellow"
    return "red"


# --------------------------------------------------------------------------
# Metrik hesap parametreleri
# --------------------------------------------------------------------------
METRIC_PARAMS = {
    # Efektif vergi orani hesaplanamazsa (zarar, negatif vergi) kullanilacak
    # varsayilan. ABD federal kurumlar vergisi + ortalama eyalet payi.
    "default_tax_rate": 0.23,
    # Efektif vergi orani bu araligin disindaysa guvenilmez sayilir
    "tax_rate_sane_min": 0.0,
    "tax_rate_sane_max": 0.50,
    # Marj degisimi kac yil geriye bakilarak olculur
    "margin_change_years": 3,
    "cagr_years": 3,
    # Momentum pencereleri (islem gunu)
    "window_3m_days": 63,
    "window_6m_days": 126,
    "window_12m_days": 252,
    "window_52w_days": 252,
    # Kendi tarihsel dagilimi icin kac ceyreklik kayan TTM
    "own_history_quarters": 20,
    # EV/EBIT gibi oranlarda payda negatifse metrik anlamsiz -> None
    "require_positive_denominator": [
        "ev_ebit", "ev_ebitda", "ev_gross_profit", "pe", "peg",
    ],
}


# --------------------------------------------------------------------------
# SADE TURKCE ACIKLAMALAR
# --------------------------------------------------------------------------
# Her metrik icin: gunluk dille ne oldugu, biriminin adi, ve degeri yerine
# koyunca anlamli bir CUMLE veren sablon. Dashboard sayiyi tek basina
# gostermez; yanina bu cumleyi yazar.
#
# Kural: finans jargonu bilmeyen biri de okuyup anlayabilmeli. "1,00x" bir
# sey ifade etmez; "Her 1 dolar karin 1,00 dolari nakde donuyor" eder.
METRIC_PLAIN = {
    "ev_ebit": ("Sirketin tamaminin degeri, yillik faaliyet karinin kac katina esit",
                "kat", "Sirketi bugun tamamen satin alsan, faaliyet kariyla {v} yilda kendini oderdi"),
    "ev_ebitda": ("Tamaminin degeri, amortisman oncesi karin kac kati", "kat",
                  "Amortisman oncesi karla {v} yilda kendini oderdi"),
    "ev_gross_profit": ("Tamaminin degeri, yillik brut karin kac kati", "kat",
                        "Brut karla {v} yilda kendini oderdi"),
    "ev_sales": ("Tamaminin degeri, yillik satislarin kac kati", "kat",
                 "Her 1 dolarlik yillik satis icin {v} dolar odiyorsun"),
    "fcf_yield_ev": ("Urettigi serbest nakit, sirketin toplam degerinin yuzde kaci",
                     "yuzde", "Sirketi tamamen alsan, yatirdigin paranin yilda %{v} kadari nakit olarak geri donerdi"),
    "fcf_yield_mcap": ("Serbest nakit, hisselerin toplam degerinin yuzde kaci", "yuzde",
                       "Hisseye odedigin paranin yilda %{v} kadari nakit olarak uretiliyor"),
    "pe": ("Fiyat, hisse basina net karin kac kati", "kat",
           "Bugunku karla {v} yilda kendini oderdi"),
    "earnings_yield": ("Faaliyet karinin, sirketin toplam degerine orani", "yuzde",
                       "Tamamini alsan faaliyet kari yilda %{v} getiri demek"),
    "peg": ("Fiyat/kazanc oraninin buyume hizina bolunmusu", "kat",
            "Buyumeye gore fiyat carpani {v} (1 alti ucuz, 2 ustu pahali sayilir)"),
    "rev_growth_ttm": ("Son 12 ayin satislari, onceki 12 aya gore ne kadar degisti",
                       "yuzde", "Satislar bir yilda %{v} degisti"),
    "rev_cagr_3y": ("Son 3 yilin ortalama yillik satis buyumesi", "yuzde",
                    "3 yildir yilda ortalama %{v} buyuyor"),
    "gross_margin": ("100 dolarlik satistan, urunun maliyeti dustukten sonra kalan",
                     "yuzde", "Her 100 dolarlik satistan {v} dolar brut kar kaliyor"),
    "operating_margin": ("100 dolarlik satistan, tum faaliyet giderleri sonrasi kalan",
                         "yuzde", "Her 100 dolarlik satistan {v} dolar faaliyet kari kaliyor"),
    "fcf_margin": ("100 dolarlik satistan gercekten cebe giren nakit", "yuzde",
                   "Her 100 dolarlik satistan {v} dolar serbest nakit kaliyor"),
    "ebitda_margin": ("Amortisman oncesi kar marji", "yuzde",
                      "Her 100 dolarlik satistan {v} dolar FAVOK kaliyor"),
    "roic": ("Isletmeye yatirilan her 100 dolarin yilda kac dolar getirdigi", "yuzde",
             "Yatirilan sermaye yilda %{v} getiri uretiyor"),
    "gross_profitability": ("Brut karin toplam varliklara orani", "kat",
                            "Her 1 dolarlik varlik {v} dolar brut kar uretiyor"),
    "rule_of_40": ("Buyume yuzdesi + nakit marji. Yazilimda saglik olcusu",
                   "puan", "Buyume ve nakit karliligi toplami {v} (40 ustu saglikli)"),
    "rule_of_40_ebitda": ("40 Kuralinin FAVOK marjiyla hesaplanan versiyonu", "puan",
                          "FAVOK ile hesaplandiginda {v}"),
    "rule_of_40_gap": ("Iki 40 Kurali arasindaki fark — buyuk olcude hisse bazli odeme",
                       "puan", "Iki hesap arasindaki {v} puanlik fark buyuk olcude calisana verilen hisse"),
    "piotroski_f": ("9 maddelik temel saglik kontrolunden kac tanesini geciyor",
                    "puan", "9 saglik testinin {v} tanesini geciyor"),
    "altman_z": ("Iflas riski skoru — yuksek olan guvenli", "puan",
                 "Iflas riski skoru {v} (2,6 ustu guvenli, 1,1 alti tehlikeli)"),
    "beneish_m": ("Muhasebe oynamasi olasiligi — dusuk olan iyi", "puan",
                  "Manipulasyon skoru {v} (-1,78 ustu supheli sayilir)"),
    "sloan_accruals": ("Karin ne kadarinin nakde donmedigi — dusuk olan iyi", "oran",
                       "Karin nakde donmeyen kismi {v} (negatif olmasi iyi)"),
    "cash_conversion": ("Kagit uzerindeki karin ne kadari gercekten nakde donuyor",
                        "kat", "Her 1 dolar karin {v} dolari nakde donuyor"),
    "sbc_to_revenue": ("Calisanlara hisse olarak verilenin satislara orani", "yuzde",
                       "Satislarin %{v} kadari calisana hisse olarak veriliyor"),
    "sbc_to_fcf": ("Calisanlara verilen hisse, uretilen nakdin kac kati", "kat",
                   "Uretilen her 1 dolar nakdin {v} dolari calisana hisse olarak gidiyor"),
    "share_count_change_1y": ("Hisse sayisi bir yilda ne kadar degisti — negatif iyi",
                              "yuzde", "Hisse sayisi bir yilda %{v} degisti (negatif = geri alim, ortaklik payin artiyor)"),
    "net_debt_to_ebitda": ("Net borc, yillik FAVOK'un kac kati", "kat",
                           "Net borc yillik FAVOK'un {v} kati"),
    "interest_coverage": ("Faaliyet kari, faiz giderinin kac kati", "kat",
                          "Faaliyet kari faiz giderinin {v} kati"),
    "current_ratio": ("Donen varliklar, kisa vadeli borclarin kac kati", "kat",
                      "Kisa vadeli borclarin {v} kati kadar donen varlik var"),
    "maturity_wall_2y": ("2 yilda odenecek borc, eldeki nakdin kac kati", "kat",
                         "2 yilda vadesi gelen borc, nakdin {v} kati"),
    "lease_liabilities": ("Kiralama yukumlulukleri (EV hesabina DAHIL DEGIL)",
                          "milyon dolar", "{v} milyon dolarlik kiralama yukumlulugu var"),
    "net_debt": ("Finansal borc eksi nakit — negatif ise net nakit", "milyon dolar",
                 "Net borc {v} milyon dolar (negatif = borctan cok nakdi var)"),
    "implied_growth": ("Bugunku fiyat, sirketin yilda ne kadar buyuyecegini varsayiyor",
                       "yuzde", "Bu fiyat, nakit akisinin yilda %{v} buyumesini varsayiyor"),
    "implied_vs_actual_growth": ("Fiyatin varsaydigi buyume, gerceklesenin kac kati",
                                 "kat", "Fiyat, gerceklesen buyumenin {v} katini varsayiyor"),
    "return_6m": ("Son 6 ayda hisse ne kadar getirdi", "yuzde", "6 ayda %{v} getirdi"),
    "return_12m": ("Son 12 ayda hisse ne kadar getirdi", "yuzde", "12 ayda %{v} getirdi"),
    "rel_strength_3m": ("3 ayda Nasdaq 100'e gore ne kadar iyi/kotu gitti", "yuzde",
                        "3 ayda Nasdaq 100'den %{v} farkli"),
    "return_3m": ("Son 3 ayda hisse ne kadar getirdi", "yuzde", "3 ayda %{v} getirdi"),
    "rel_strength_6m": ("6 ayda Nasdaq 100'e gore ne kadar iyi/kotu gitti", "yuzde",
                        "6 ayda Nasdaq 100'den %{v} farkli"),
    "rel_strength_12m": ("12 ayda Nasdaq 100'e gore fark", "yuzde",
                         "12 ayda Nasdaq 100'den %{v} farkli"),
    "pct_off_52w_high": ("Son 1 yilin en yuksek fiyatindan ne kadar asagida", "yuzde",
                         "1 yilin zirvesinden %{v} asagida"),
    "gross_margin_change_3y": ("Brut marj 3 yilda kac puan degisti", "puan",
                               "Brut marj 3 yilda {v} puan degisti"),
    "operating_margin_change_3y": ("Faaliyet marji 3 yilda kac puan degisti", "puan",
                                   "Faaliyet marji 3 yilda {v} puan degisti"),
    "fcf_margin_change_3y": ("Nakit marji 3 yilda kac puan degisti", "puan",
                             "Nakit marji 3 yilda {v} puan degisti"),
}

# Aciklamalari esik tanimlarina yedir
for _key, (_plain, _unit, _sentence) in METRIC_PLAIN.items():
    if _key in THRESHOLDS:
        THRESHOLDS[_key]["plain"] = _plain
        THRESHOLDS[_key]["unit_name"] = _unit
        THRESHOLDS[_key]["sentence"] = _sentence

# Puan bloklarinin sade aciklamalari
SCORE_PLAIN = {
    "total": ("Genel puan", "Bes basligin agirlikli ortalamasi. 0-100 arasi; "
              "yuksek olan daha cazip. Ayni sektordeki digerleriyle karsilastirilarak hesaplanir."),
    "value": ("Ucuzluk", "Sirket, urettigi kar ve nakde gore ne kadar ucuz. "
              "Sektordeki digerlerine gore siralanir."),
    "quality": ("Kalite", "Isin kendisi ne kadar iyi: marjlar, sermaye getirisi, "
                "buyume ve karlilik dengesi."),
    "safety": ("Saglamlik", "Bilanco ne kadar dayanikli: borc, faiz odeme gucu, "
               "kisa vadeli likidite, iflas riski."),
    "momentum": ("Momentum", "Bu sistemde momentum 'kim daha cok kazandirdi' "
                 "DEGIL, 'dusus durdu mu' olcusudur. 1-2 yillik yeniden "
                 "fiyatlanma ariyoruz; yuksek 12 aylik getiriyi odullendirmek "
                 "yeniden fiyatlanmasi COKTAN OLMUS isimleri one cikarirdi. "
                 "Agirligi bu yuzden dusuk (5); acilan pay katalizore verildi."),
    "earnings_quality": ("Kazanc kalitesi", "Raporlanan kar gercek mi: nakde donuyor mu, "
                         "muhasebe oynamasi isareti var mi."),
    "catalyst": ("Katalizor", "Yeniden fiyatlanmayi tetikleyecek somut bir olay var mi. "
                 "Bu puani otomatik hesaplamiyoruz; Claude analiz yazarken elle giriyor."),
}
