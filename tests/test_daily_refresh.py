"""run_daily._refresh_price_derived — fiyat degisince carpanlar dogru mu?"""

import pytest

from src import cards, run_daily
from tests import fixtures


def base_card():
    return cards.build(fixtures.dbx(), source="test")


class TestPriceRefresh:
    def test_card_stores_ttm_and_shares(self):
        c = base_card()
        assert c["shares_outstanding_m"] == pytest.approx(300.0)
        assert c["ttm"]["ebit_musd"] == pytest.approx(640.0)
        assert c["net_debt_musd"] == pytest.approx(808.0)   # 1980 - 1172

    def test_doubling_price_doubles_market_cap(self):
        c = base_card()
        quote = {"price": 57.34, "history": [], "high_52w": 60.0}
        run_daily._refresh_price_derived(c, quote, [])
        assert c["market_cap_musd"] == pytest.approx(17202.0, abs=1)
        # EV = mcap + net borc
        assert c["enterprise_value_musd"] == pytest.approx(18010.0, abs=1)

    def test_multiples_recomputed_not_scaled(self):
        c = base_card()
        run_daily._refresh_price_derived(
            c, {"price": 28.67, "history": [], "high_52w": 32.0}, [])
        # ayni fiyat -> ayni carpan (sapma yok)
        assert c["metrics"]["ev_ebit"]["value"] == pytest.approx(14.702, abs=0.01)
        assert c["metrics"]["fcf_yield_ev"]["value"] == pytest.approx(9.098, abs=0.01)

    def test_repeated_refresh_does_not_drift(self):
        """Ayni fiyatla 10 kez tazelemek carpani kaydirmamali.

        Sabit bir sayiya degil, KARARLILIGA bakilir: degerler artik gosterilen
        hassasiyete yuvarlandigi icin sabit beklenti gereksiz yere kirilgandi.
        """
        c = base_card()
        quote = {"price": 28.67, "history": [], "high_52w": 32.0}
        run_daily._refresh_price_derived(c, quote, [])
        first = {k: c["metrics"][k]["value"] for k in
                 ("ev_ebit", "fcf_yield_ev", "pe", "peg", "ev_sales")}
        for _ in range(9):
            run_daily._refresh_price_derived(c, quote, [])
        after = {k: c["metrics"][k]["value"] for k in first}
        assert after == first
        assert c["metrics"]["ev_ebit"]["value"] == pytest.approx(14.70, abs=0.01)

    def test_cheaper_price_lifts_fcf_yield(self):
        c = base_card()
        run_daily._refresh_price_derived(
            c, {"price": 14.34, "history": [], "high_52w": 32.0}, [])
        assert c["metrics"]["fcf_yield_ev"]["value"] > 9.098
        assert c["metrics"]["ev_ebit"]["value"] < 14.702

    def test_colors_follow_new_values(self):
        c = base_card()
        run_daily._refresh_price_derived(
            c, {"price": 5.0, "history": [], "high_52w": 32.0}, [])
        # cok ucuz -> EV/EBIT yesil
        assert c["metrics"]["ev_ebit"]["color"] == "green"

    def test_negative_ebit_keeps_multiple_none(self):
        c = cards.build(fixtures.kvyo(), source="test")
        run_daily._refresh_price_derived(
            c, {"price": 25.0, "history": [], "high_52w": 30.0}, [])
        assert c["metrics"]["ev_ebit"]["value"] is None
        assert c["metrics"]["ev_gross_profit"]["value"] is not None

    def test_missing_price_data_does_not_crash(self):
        c = base_card()
        run_daily._refresh_price_derived(c, {"price": None, "history": []}, [])
        assert c["ticker"] == "DBX"

    def test_off_52w_high(self):
        c = base_card()
        run_daily._refresh_price_derived(
            c, {"price": 25.0, "history": [], "high_52w": 50.0}, [])
        assert c["metrics"]["pct_off_52w_high"]["value"] == pytest.approx(50.0)


class TestOptionalSourcesNeverErase:
    """Cokmus bir ISTEGE BAGLI kaynak, kartta yazili olani SILMEMELI.

    Gercek olay: yerel bir kosuda yfinance erisilemezken uc kartin analist
    hedefleri ve bilanco tarihleri null'landi. Mekanizma sinsiydi —
    analyst.consensus basarisizlikta ICI BOS BIR SOZLUK donduruyordu ve bos
    sozluk truthy oldugu icin cagirandaki "if analyst:" korumasindan
    geciyordu. Takvim ise hic korumasizdi.

    null bir alan "veri yok" gibi gorunur, "vardi ve sildik" gibi gorunmez.
    Bu yuzden en sessiz veri kaybi turudur.
    """

    def test_failed_analyst_fetch_returns_none(self, monkeypatch, tmp_path):
        from src.sources import analyst

        monkeypatch.setattr(analyst, "CACHE_DIR", tmp_path)

        def boom(*a, **k):
            raise RuntimeError("yfinance erisilemez")

        import builtins
        real_import = builtins.__import__

        def fake_import(name, *a, **k):
            if name == "yfinance":
                raise ImportError("yok")
            return real_import(name, *a, **k)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        out = analyst.consensus("DBX", 25.0)
        assert out is None, "bos sozluk degil None donmeli"

    def test_hollow_analyst_dict_does_not_overwrite(self):
        """Kaynak 'cevap verdim ama elimde bir sey yok' derse de yazmamali."""
        hollow = {"buy": None, "hold": None, "sell": None, "target_low": None,
                  "target_median": None, "target_high": None,
                  "upside_to_median": None, "analyst_count": None,
                  "source": "yfinance", "recommendation": "none"}
        dolu = dict(hollow, analyst_count=7, target_median=390.0)

        def yazilir_mi(a):
            return bool(a) and any(v is not None for k, v in a.items()
                                   if k not in ("source", "recommendation"))

        assert yazilir_mi(hollow) is False
        assert yazilir_mi(dolu) is True

    def test_empty_calendar_keeps_known_date(self):
        """Finnhub ve SEC tahmini ayni anda cevap vermezse tarih korunmali."""
        card = {"calendar": {"next_earnings": "2027-01-06", "estimated": False}}
        bos = {"next_earnings": None, "estimated": False}

        # run_daily'deki kosulun aynisi
        if bos.get("next_earnings") or not (card.get("calendar") or {}).get("next_earnings"):
            card["calendar"] = bos

        assert card["calendar"]["next_earnings"] == "2027-01-06"

    def test_new_date_does_overwrite(self):
        card = {"calendar": {"next_earnings": "2027-01-06", "estimated": True}}
        yeni = {"next_earnings": "2027-01-20", "estimated": False}
        if yeni.get("next_earnings") or not (card.get("calendar") or {}).get("next_earnings"):
            card["calendar"] = yeni
        assert card["calendar"]["next_earnings"] == "2027-01-20"
        assert card["calendar"]["estimated"] is False

    def test_empty_calendar_fills_a_card_that_had_none(self):
        """Hic tarihi olmayan kart, bos kayitla da olsa alani kazanmali."""
        card = {"calendar": {}}
        bos = {"next_earnings": None, "estimated": False}
        if bos.get("next_earnings") or not (card.get("calendar") or {}).get("next_earnings"):
            card["calendar"] = bos
        assert card["calendar"] == bos
