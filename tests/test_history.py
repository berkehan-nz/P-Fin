"""history.py — portfoy tarihcesi ve kiyas serileri.

Bu dosya "bugun yatirimlarim nasil gitti" sorusunun hafizasi. Yanlis bir
satir, Berke'nin telefonda gordugu ilk sayiyi yanlis yapar. Testler bu
yuzden en kirilgan uc noktada yogunlasiyor: nakdin geri kurulmasi,
dagitimlarin sayilmasi ve eksik veriyle hesaplanan satirin tam satiri
EZMEMESI.
"""

import copy

import pytest

from src import history as H
from src import portfolio as P

DAYS = ["2026-09-29", "2026-09-30", "2026-10-01", "2026-10-02"]


def base_data():
    return {
        "cash_usd": 100.0,
        "positions": [
            {"ticker": "SGOV", "asset_class": "ETF", "entry_date": DAYS[0],
             "entry_price": 100.0, "shares": 5.0, "fees_usd": 0.0, "status": "OPEN"},
            {"ticker": "TL-X", "asset_class": "TL_DEPOSIT", "entry_date": DAYS[0],
             "start_date": DAYS[0], "maturity_date": "2026-12-30",
             "principal_try": 50000.0, "annual_rate_pct": 36.5,
             "withholding_pct": 0.0, "usdtry_at_entry": 50.0, "status": "OPEN"},
        ],
        "closed": [],
        "cash_flows": [],
    }


def series():
    ps = {"SGOV": list(zip(DAYS, [100.0, 100.0, 100.0, 99.70])),
          "QQQ": list(zip(DAYS, [500.0, 510.0, 490.0, 500.0]))}
    divs = {"SGOV": [("2026-10-02", 0.30)], "QQQ": []}
    fx = list(zip(DAYS, [50.0, 50.0, 50.0, 50.0]))
    return ps, divs, fx


@pytest.fixture(autouse=True)
def frozen_today(monkeypatch):
    monkeypatch.setattr(H, "today_iso", lambda: DAYS[-1])
    monkeypatch.setattr(P, "today_iso", lambda: DAYS[-1])


class TestCash:
    def test_later_purchase_is_undone_for_earlier_days(self):
        """30 Ekim parcasi kaydedilince Ekim ortasi satirlari 149 $ eksik
        gorunmemeli: o gun para hala nakitteydi."""
        d = base_data()
        d["positions"].append({"ticker": "QQQM", "asset_class": "ETF",
                               "entry_date": "2026-10-30", "entry_price": 149.0,
                               "shares": 1.0, "fees_usd": 0.0, "status": "OPEN"})
        d["cash_usd"] = 0.0                     # alimdan SONRAKI nakit
        assert H.cash_on(d, "2026-10-15") == 149.0

    def test_capital_is_cash_before_the_first_trades(self):
        d = base_data()
        # 100 nakit + 500 SGOV + 50.000 TL / 50 = 1.000 USD
        assert H.injections(d)[0] == (DAYS[0], pytest.approx(1600.0))


class TestValuation:
    def test_dividend_offsets_ex_date_drop(self):
        """SGOV odeme-disi gunu dagitim kadar duser; deger DUSMEMELI."""
        ps, divs, fx = series()
        rows = H.rebuild(base_data(), price_series=ps, dividends=divs, fx_series=fx)
        sgov = [r["positions"]["SGOV"]["value_usd"] for r in rows]
        assert sgov[-1] == pytest.approx(5 * 99.70 + 5 * 0.30)
        assert sgov[-1] >= sgov[-2]

    def test_tl_accrues_daily_simple_interest(self):
        ps, divs, fx = series()
        rows = H.rebuild(base_data(), price_series=ps, dividends=divs, fx_series=fx)
        # %36,5 / 365 = gunde %0,1 -> 50.000 TL'ye gunde 50 TL, kur sabit 50
        tl = [r["positions"]["TL-X"]["value_try"] for r in rows]
        assert tl[1] - tl[0] == pytest.approx(50.0)

    def test_inception_row_equals_capital_minus_nothing(self):
        ps, divs, fx = series()
        rows = H.rebuild(base_data(), price_series=ps, dividends=divs, fx_series=fx)
        assert rows[0]["total_usd"] == pytest.approx(1600.0)
        assert rows[0]["complete"] is True


class TestBenchmarks:
    def test_all_benchmarks_start_at_capital(self):
        ps, divs, fx = series()
        rows = H.rebuild(base_data(), price_series=ps, dividends=divs, fx_series=fx)
        b = rows[0]["benchmarks"]
        assert b["all_sgov_usd"] == pytest.approx(1600.0)
        assert b["all_qqq_usd"] == pytest.approx(1600.0)
        assert b["all_tl_usd"] == pytest.approx(1600.0)

    def test_all_qqq_tracks_qqq(self):
        ps, divs, fx = series()
        rows = H.rebuild(base_data(), price_series=ps, dividends=divs, fx_series=fx)
        assert rows[1]["benchmarks"]["all_qqq_usd"] == pytest.approx(1600.0 * 1.02)

    def test_all_sgov_includes_distributions(self):
        ps, divs, fx = series()
        rows = H.rebuild(base_data(), price_series=ps, dividends=divs, fx_series=fx)
        assert rows[-1]["benchmarks"]["all_sgov_usd"] == pytest.approx(1600.0)


class TestMerge:
    def _row(self, day, total, complete=True, usable=True):
        return {"date": day, "total_usd": total, "complete": complete,
                "usable": usable, "missing": [] if complete else ["X"]}

    def test_incomplete_row_never_overwrites_complete(self):
        old = [self._row("2026-10-01", 2400.0)]
        new = [self._row("2026-10-01", 1900.0, complete=False, usable=True)]
        assert H.merge(old, new)[0]["total_usd"] == 2400.0

    def test_unusable_row_is_never_written(self):
        """Fiyati olmayan satir bir pozisyonu toplamdan dusurur — sahte cokus."""
        new = [self._row("2026-10-01", 900.0, complete=False, usable=False)]
        assert H.merge([], new) == []

    def test_complete_row_replaces_old(self):
        old = [self._row("2026-10-01", 2400.0)]
        new = [self._row("2026-10-01", 2410.0)]
        assert H.merge(old, new)[0]["total_usd"] == 2410.0

    def test_old_rows_outside_new_range_are_kept(self):
        old = [self._row("2026-09-29", 2390.0), self._row("2026-09-30", 2395.0)]
        new = [self._row("2026-09-30", 2396.0)]
        merged = H.merge(old, new)
        assert [r["date"] for r in merged] == ["2026-09-29", "2026-09-30"]

    def test_missing_price_makes_row_unusable(self):
        ps, divs, fx = series()
        ps["SGOV"] = ps["SGOV"][:0]          # SGOV fiyati hic yok
        rows = H.rebuild(base_data(), price_series=ps, dividends=divs, fx_series=fx)
        assert rows == [] or all(not r["usable"] for r in rows)

    def test_missing_dividends_is_usable_but_incomplete(self):
        ps, divs, fx = series()
        divs["SGOV"] = None                  # bilinmiyor (bos liste degil)
        rows = H.rebuild(base_data(), price_series=ps, dividends=divs, fx_series=fx)
        assert rows and all(r["usable"] and not r["complete"] for r in rows)


class TestPerformance:
    def test_day_change_and_return(self):
        ps, divs, fx = series()
        d = base_data()
        rows = H.rebuild(d, price_series=ps, dividends=divs, fx_series=fx)
        perf = H.performance(rows, d)
        assert perf["status"] == "aktif"
        assert perf["days"] == 3
        prev, last = rows[-2]["total_usd"], rows[-1]["total_usd"]
        assert perf["day_change_usd"] == pytest.approx(last - prev, abs=0.01)
        assert perf["return_usd"] == pytest.approx(last - 1600.0, abs=0.01)

    def test_not_started_yet(self, monkeypatch):
        monkeypatch.setattr(H, "today_iso", lambda: "2026-09-28")
        perf = H.performance([], base_data())
        assert perf["status"] == "baslamadi"
        assert perf["days_to_start"] == 1


class TestLotsAndDayChange:
    def _with_second_lot(self):
        d = base_data()
        d["positions"].append({"ticker": "SGOV", "asset_class": "ETF",
                               "entry_date": DAYS[2], "entry_price": 100.0,
                               "shares": 1.0, "fees_usd": 0.0, "status": "OPEN"})
        d["cash_usd"] = 0.0                    # ikinci parca nakitten alindi
        return d

    def test_second_lot_of_same_ticker_is_summed(self):
        """30 Ekim QQQM parcasi ilk parcayi satirdan silmemeli."""
        ps, divs, fx = series()
        rows = H.rebuild(self._with_second_lot(), price_series=ps,
                         dividends=divs, fx_series=fx)
        assert rows[2]["positions"]["SGOV"]["shares"] == 6.0
        assert rows[2]["positions"]["SGOV"]["value_usd"] == pytest.approx(600.0)

    def test_new_lot_day_is_not_counted_as_gain(self):
        ps, divs, fx = series()
        d = self._with_second_lot()
        rows = H.rebuild(d, price_series=ps, dividends=divs, fx_series=fx)
        day = H.positions_day(rows[1], rows[2])
        assert day["SGOV"]["usd"] == pytest.approx(0.0)   # fiyat ayni

    def test_cash_injection_is_not_a_gain(self):
        ps, divs, fx = series()
        d = base_data()
        d["cash_flows"] = [{"date": DAYS[-1], "amount_usd": 500.0}]
        d["cash_usd"] = 600.0
        rows = H.rebuild(d, price_series=ps, dividends=divs, fx_series=fx)
        perf = H.performance(rows, d)
        # Son gun: SGOV 5 x (99,70 + 0,30) degismedi, TL +50 TL = +1 $,
        # 500 $ giris kazanc sayilmaz.
        assert perf["day_change_usd"] == pytest.approx(1.0, abs=0.01)

    def test_tl_day_change_is_interest_plus_fx(self):
        ps, divs, fx = series()
        rows = H.rebuild(base_data(), price_series=ps, dividends=divs, fx_series=fx)
        day = H.positions_day(rows[0], rows[1])
        assert day["TL-X"]["usd"] == pytest.approx(1.0, abs=0.01)  # 50 TL / 50
