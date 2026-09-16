"""KRITIK TARIHLER TAKVIMI — makro yayinlar, bilancolar, SEC olaylari.

Uc ucretsiz kaynak:

* **FRED** ``/release/dates`` — TUFE, istihdam, GSYH gibi yayinlarin
  GELECEK tarihleri. ``include_release_dates_with_no_data=true`` olmadan
  yalnizca gecmis tarihler doner; takvim icin sart olan budur.
* **Finnhub** kazanc takvimi — portfoy ve adaylarin bilanco gunleri
  (zaten cekiliyor, burada takvime cevriliyor).
* **SEC EDGAR** ``submissions`` — 8-K gibi OLAY dosyalamalari. Anahtar
  gerektirmez, yalnizca User-Agent ister.

TASARIM: takvim SADECE TARIH tasir, yorum tasimaz. "Bu tarihte ne olacak"
bilgisi kaynagin kendisinden gelir; tahmin veya beklenti uretmiyoruz.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

from .. import config
from ..util import http_get, read_json, today_iso

# FRED yayin kimlikleri. Bunlar piyasayi gercekten oynatan yayinlar;
# tamamini listelemek takvimi gurultuye bogar.
FRED_RELEASES = {
    10: ("TUFE (CPI)", "enflasyon"),
    50: ("Istihdam raporu", "isgucu"),
    53: ("GSYH (GDP)", "buyume"),
    46: ("URFE (PPI)", "enflasyon"),
    21: ("Perakende satislar", "talep"),
    13: ("Sanayi uretimi", "uretim"),
}

# Panoda one cikarilacak SEC form turleri ve ne anlama geldikleri.
# Form 4 (icerden alim-satim) HARIC: gunde onlarca geliyor ve yon bilgisi
# tasimadigi icin takvimi doldurup asil olaylari gorunmez kiliyor.
EVENT_FORMS = {
    "8-K": "Onemli olay bildirimi",
    "10-Q": "Ceyreklik rapor",
    "10-K": "Yillik rapor",
    "SC 13D": "Aktivist yatirimci pozisyonu",
    "SC 13G": "Buyuk pay bildirimi",
    "S-1": "Halka arz basvurusu",
    "S-3": "Ikincil arz kaydi",
    "424B5": "Ikincil arz fiyatlamasi",
    "DEF 14A": "Genel kurul cagrisi",
}


# --------------------------------------------------------------------------
# Makro yayin tarihleri (FRED)
# --------------------------------------------------------------------------
def macro_releases(*, days_ahead: int = 45) -> list[dict]:
    """Yaklasan makro veri yayinlari."""
    if not config.FRED_API_KEY:
        return []

    start = today_iso()
    end = (date.today() + timedelta(days=days_ahead)).isoformat()
    out: list[dict] = []

    for release_id, (label, topic) in FRED_RELEASES.items():
        try:
            resp = http_get(
                "https://api.stlouisfed.org/fred/release/dates",
                params={
                    "release_id": release_id,
                    "api_key": config.FRED_API_KEY,
                    "file_type": "json",
                    # Gelecek tarihler YALNIZCA bu bayrakla doner.
                    "include_release_dates_with_no_data": "true",
                    "realtime_start": start,
                    "realtime_end": end,
                    "sort_order": "asc",
                    "limit": 20,
                },
                timeout=20,
            )
            payload = resp.json()
        except Exception as exc:  # noqa: BLE001
            print(f"  [uyari] FRED yayin {label}: {str(exc)[:60]}")
            continue

        for row in (payload.get("release_dates") or []):
            day = row.get("date")
            if day and start <= day <= end:
                out.append({"date": day, "kind": "makro", "title": label,
                            "detail": topic, "ticker": None})

    return out


# --------------------------------------------------------------------------
# Bilanco tarihleri (Finnhub — zaten cekilmis takvimden)
# --------------------------------------------------------------------------
def earnings_events(earnings: dict[str, str], tickers: set[str],
                    *, days_ahead: int = 120) -> list[dict]:
    """``{ticker: tarih}`` sozlugunu takvim olaylarina cevirir.

    Pencere makro yayinlardan GENIS: bilancolar ceyrekte bir geliyor, 45
    gunluk pencere sezon disinda hepsini disarida birakiyordu (en yakini
    64 gun sonraydi ve takvimde tek bir bilanco gorunmuyordu).
    """
    start = today_iso()
    end = (date.today() + timedelta(days=days_ahead)).isoformat()
    out = []
    for ticker, day in (earnings or {}).items():
        if ticker in tickers and day and start <= day <= end:
            out.append({"date": day, "kind": "bilanco",
                        "title": f"{ticker} bilanco", "detail": None,
                        "ticker": ticker})
    return out


# --------------------------------------------------------------------------
# SEC olay dosyalamalari
# --------------------------------------------------------------------------
def sec_events(cik_by_ticker: dict[str, int], *, days_back: int = 10,
               per_ticker: int = 3) -> list[dict]:
    """Son gunlerde gelen 8-K ve benzeri OLAY dosyalamalari.

    Gecmise bakar (yayimlanmis olaylar), takvimin "olan biten" tarafi.
    Form 4 disaridadir: gunluk gurultu, olay degil.
    """
    from . import edgar_api

    floor = (date.today() - timedelta(days=days_back)).isoformat()
    out: list[dict] = []

    for ticker, cik in cik_by_ticker.items():
        if not cik:
            continue
        sub = edgar_api.submissions(cik)
        recent = ((sub or {}).get("filings") or {}).get("recent") or {}
        forms = recent.get("form") or []
        dates = recent.get("filingDate") or []
        accs = recent.get("accessionNumber") or []
        docs = recent.get("primaryDocument") or []

        found = 0
        for i, form in enumerate(forms):
            if found >= per_ticker:
                break
            if i >= len(dates) or dates[i] < floor:
                break                      # liste tarihe gore sirali
            label = EVENT_FORMS.get(form)
            if not label:
                continue
            acc = (accs[i] if i < len(accs) else "").replace("-", "")
            doc = docs[i] if i < len(docs) else ""
            out.append({
                "date": dates[i],
                "kind": "sec",
                "title": f"{ticker} · {form}",
                "detail": label,
                "ticker": ticker,
                "url": (f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{doc}"
                        if acc and doc else None),
            })
            found += 1

    return out


def build(*, earnings: dict[str, str], tickers: set[str],
          cik_by_ticker: dict[str, int]) -> dict:
    """Takvimin tamami: gecmis olaylar + yaklasan tarihler, tarihe gore sirali."""
    events = (macro_releases()
              + earnings_events(earnings, tickers)
              + sec_events(cik_by_ticker))
    events.sort(key=lambda e: (e["date"], e["kind"]))

    today = today_iso()
    return {
        "upcoming": [e for e in events if e["date"] >= today][:40],
        "recent": [e for e in events if e["date"] < today][-25:][::-1],
        "source": "fred+finnhub+sec",
    }
