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

    def test_row_from_an_older_portfolio_is_dropped(self):
        """20 Ekim: yeni mevduattan once yazilan bugunun satiri, yeniden
        hesaplanamayinca son satir kalip mevduati toplamdan dusurmemeli."""
        ps, divs, fx = series()
        old = H.rebuild(base_data(), price_series=ps, dividends=divs, fx_series=fx)
        d = TestTryInjection()._with_second_deposit()
        new = H.rebuild(d, price_series=ps, dividends=divs, fx_series=fx, upto=DAYS[2])
        merged = H.merge(old, new)
        assert [r["date"] for r in merged] == DAYS[:3]
        assert "TL-Y" in merged[-1]["positions"]

    def test_same_portfolio_keeps_rows_outside_new_range(self):
        ps, divs, fx = series()
        d = base_data()
        old = H.rebuild(d, price_series=ps, dividends=divs, fx_series=fx)
        new = H.rebuild(copy.deepcopy(d), price_series=ps, dividends=divs, fx_series=fx,
                        upto=DAYS[2])
        assert [r["date"] for r in H.merge(old, new)] == DAYS

    def test_rows_without_a_key_are_dropped_once_keys_exist(self):
        """Ilk kosu: izsiz eski satirlar yeniden hesaplanmadiysa atilir."""
        ps, divs, fx = series()
        d = base_data()
        old = [{k: v for k, v in r.items() if k != "inputs"}
               for r in H.rebuild(d, price_series=ps, dividends=divs, fx_series=fx)]
        new = H.rebuild(d, price_series=ps, dividends=divs, fx_series=fx, upto=DAYS[2])
        assert [r["date"] for r in H.merge(old, new)] == DAYS[:3]

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


class TestFxDayBeforeUsOpen:
    def test_todays_fx_adds_a_row_before_us_open(self):
        """TSI sabahi: ETF fiyati dunku, kur bugunku. Bugunun satiri olmali
        ki toplam ile pozisyon tablosu ayni gunu gostersin."""
        ps, divs, fx = series()
        fx = fx + [("2026-10-05", 51.0)]          # pazartesi, ABD henuz acilmadi
        rows = H.rebuild(base_data(), price_series=ps, dividends=divs,
                         fx_series=fx, upto="2026-10-05")
        assert rows[-1]["date"] == "2026-10-05"
        assert rows[-1]["positions"]["SGOV"]["price"] == 99.70   # dunku kapanis
        assert rows[-1]["usdtry"] == 51.0

    def test_today_has_a_row_even_before_the_first_fx_print(self):
        """Kur kaynagi bugunu henuz yazmadi: satir yine olur (dunku kur,
        bugunun faizi) ki ust toplam pozisyon tablosuyla ayni olsun."""
        ps, divs, fx = series()
        rows = H.rebuild(base_data(), price_series=ps, dividends=divs,
                         fx_series=fx, upto="2026-10-05")
        assert rows[-1]["date"] == "2026-10-05"
        assert rows[-1]["usdtry"] == 50.0
        tl = rows[-1]["positions"]["TL-X"]
        assert tl["accrued_net_try"] == pytest.approx(50000 * 0.365 * 6 / 365, abs=0.01)

    def test_weekend_fx_quote_adds_no_row(self):
        ps, divs, fx = series()
        fx = fx + [("2026-10-03", 51.0)]          # cumartesi
        rows = H.rebuild(base_data(), price_series=ps, dividends=divs,
                         fx_series=fx, upto="2026-10-03")
        assert rows[-1]["date"] == DAYS[-1]


class TestTryInjection:
    """Bankadan dogrudan TL ile acilan mevduat portfoy disi yeni sermayedir."""

    def _with_second_deposit(self):
        d = base_data()
        d["positions"].append({
            "ticker": "TL-Y", "asset_class": "TL_DEPOSIT", "entry_date": DAYS[2],
            "start_date": DAYS[2], "maturity_date": "2027-01-02", "principal_try": 50000.0,
            "annual_rate_pct": 36.5, "withholding_pct": 0.0, "usdtry_at_entry": 50.0,
            "status": "OPEN"})
        d["cash_flows"] = [{"date": DAYS[2], "amount_try": 50000.0, "usdtry": 50.0}]
        return d

    def test_earlier_rows_are_not_inflated(self):
        ps, divs, fx = series()
        a = H.rebuild(base_data(), price_series=ps, dividends=divs, fx_series=fx)
        b = H.rebuild(self._with_second_deposit(), price_series=ps, dividends=divs, fx_series=fx)
        assert b[0]["total_usd"] == a[0]["total_usd"]
        assert b[1]["total_usd"] == a[1]["total_usd"]
        assert b[2]["total_usd"] == pytest.approx(a[2]["total_usd"] + 1000.0, abs=0.01)

    def test_injection_is_not_a_gain(self):
        ps, divs, fx = series()
        d = self._with_second_deposit()
        rows = H.rebuild(d, price_series=ps, dividends=divs, fx_series=fx)
        perf = H.performance(rows[:3], d)
        assert perf["invested_usd"] == pytest.approx(2600.0)
        assert perf["day_change_usd"] == pytest.approx(1.0, abs=0.01)   # yalnizca faiz

    def test_return_ignores_capital_not_yet_priced(self):
        """Bugun gelen para, satiri olmayan bir gunde sahte kayip yaratmamali."""
        ps, divs, fx = series()
        d = self._with_second_deposit()
        rows = H.rebuild(d, price_series=ps, dividends=divs, fx_series=fx)
        perf = H.performance(rows[:2], d)
        assert perf["invested_usd"] == pytest.approx(1600.0)


class TestContributionsVsGrowth:
    """Pano "para ekledim" ile "portfoy buyudu"yu ayri gostermeli."""

    def _rows(self, d):
        ps, divs, fx = series()
        return H.annotate_flows(H.rebuild(d, price_series=ps, dividends=divs, fx_series=fx), d)

    def test_each_row_carries_invested_capital(self):
        rows = self._rows(TestTryInjection()._with_second_deposit())
        assert [r["invested_usd"] for r in rows] == [1600.0, 1600.0, 2600.0, 2600.0]

    def test_only_the_flow_day_is_marked(self):
        rows = self._rows(TestTryInjection()._with_second_deposit())
        assert rows[2]["added_usd"] == 1000.0
        assert rows[2]["added_try"] == 50000.0
        assert all("added_usd" not in r for i, r in enumerate(rows) if i != 2)

    def test_gain_is_unchanged_by_new_money(self):
        """Deger - yatirilan: giris olsa da olmasa da ayni kazanc."""
        a = self._rows(base_data())
        b = self._rows(TestTryInjection()._with_second_deposit())
        for i in (0, 1):
            assert b[i]["total_usd"] - b[i]["invested_usd"] == pytest.approx(
                a[i]["total_usd"] - a[i]["invested_usd"], abs=0.01)
        # 2. gun yeni mevduat ilk gununu yasiyor (faiz 0): kazanc farki yok.
        assert b[2]["total_usd"] - b[2]["invested_usd"] == pytest.approx(
            a[2]["total_usd"] - a[2]["invested_usd"], abs=0.01)

    def test_performance_splits_initial_added_and_gain(self):
        d = TestTryInjection()._with_second_deposit()
        rows = self._rows(d)
        perf = H.performance(rows[:3], d)
        assert perf["initial_usd"] == pytest.approx(1600.0)
        assert perf["added_usd"] == pytest.approx(1000.0)
        assert perf["day_added_usd"] == pytest.approx(1000.0)
        assert perf["return_usd"] == pytest.approx(
            perf["value_usd"] - perf["initial_usd"] - perf["added_usd"], abs=0.01)
        c = perf["contributions"]
        assert [x["initial"] for x in c] == [True, False]
        assert c[1] == {"date": DAYS[2], "usd": 1000.0, "try": 50000.0, "usdtry": 50.0,
                        "initial": False, "note": None}

    def test_no_flow_day_reports_zero_added(self):
        d = TestTryInjection()._with_second_deposit()
        perf = H.performance(self._rows(d), d)
        assert perf["day_added_usd"] == 0.0

    def test_kept_old_rows_are_annotated_too(self):
        """Birlestirmede korunan eski tam satir da yatirilan alanini almali."""
        d = TestTryInjection()._with_second_deposit()
        ps, divs, fx = series()
        old = H.rebuild(d, price_series=ps, dividends=divs, fx_series=fx)
        rows = H.annotate_flows(H.merge(old, []), d)
        assert rows[3]["invested_usd"] == 2600.0
