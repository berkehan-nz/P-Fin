"""Dis inceleme sonrasi yapilan duzeltmeler.

Her test, incelemede SOMUT olarak isaret edilen bir sirketin durumunu
kullaniyor; boylece duzeltmenin gercekten o sorunu cozdugu gorulur.
"""

import pytest

from src import funnel, metrics, overrides, scores, scoring
from src.config import COVERAGE, SCORE_CAPS, SCORE_WEIGHTS
from src.fundamentals import Period
from tests import fixtures


# --------------------------------------------------------------- kapsama
class TestCoverageWeighting:
    """YOU'nun kalite puani 94 ama kapsama 0,30 — uc metrik bosken iki
    metrik tum blogu tasiyordu ve sirket listenin basina yerlesiyordu."""

    def test_low_coverage_reduces_block_influence(self):
        blocks = {"value": 50.0, "quality": 94.0, "safety": 50.0,
                  "momentum": 50.0, "earnings_quality": 50.0}
        full = scoring.total_score(blocks, coverage={k: 1.0 for k in blocks})
        thin = scoring.total_score(blocks, coverage={**{k: 1.0 for k in blocks},
                                                     "quality": 0.30})
        assert thin["total"] < full["total"], "dusuk kapsama etkiyi azaltmali"

    def test_score_value_itself_is_not_punished(self):
        """Kapsama puani DUSURMEZ, yalnizca agirligini azaltir.
        Veri yoklugu kotu haber degildir."""
        blocks = {"value": 50.0, "quality": 94.0, "safety": None,
                  "momentum": None, "earnings_quality": None}
        s = scoring.total_score(blocks, coverage={"quality": 0.30})
        assert s["quality"] == 94.0

    def test_coverage_factor_is_reported(self):
        s = scoring.total_score({"quality": 80.0}, coverage={"quality": 0.4})
        assert s["coverage_factors"]["quality"] == pytest.approx(0.4)

    def test_coverage_has_a_floor(self):
        """Kapsama 0'a yakinsa bile blok tamamen susmasin."""
        s = scoring.total_score({"quality": 80.0}, coverage={"quality": 0.01})
        assert s["coverage_factors"]["quality"] == COVERAGE["min_weight_factor"]

    def test_block_flags_low_coverage(self):
        _, d = scoring.score_block("quality", {"roic": 80.0})
        assert d["low_coverage"] is True

    def test_full_coverage_not_flagged(self):
        pcts = {c["metric"]: 60.0 for c in
                __import__("src.config", fromlist=["x"]).SCORE_COMPONENTS["quality"]}
        _, d = scoring.score_block("quality", pcts)
        assert d["low_coverage"] is False


# -------------------------------------------------------------- momentum
class TestMomentumRealignment:
    """Sistem 1-2 yillik YENIDEN FIYATLANMA ariyor. Yuksek 12 aylik getiriyi
    odullendirmek, yeniden fiyatlanmasi coktan olmus isimleri one cikarir."""

    def test_weight_reduced_and_catalyst_raised(self):
        assert SCORE_WEIGHTS["momentum"] == 5
        assert SCORE_WEIGHTS["catalyst"] == 25
        assert sum(SCORE_WEIGHTS.values()) == 100

    def test_absolute_returns_no_longer_scored(self):
        from src.config import SCORE_COMPONENTS
        used = {c["metric"] for c in SCORE_COMPONENTS["momentum"]}
        assert "return_12m" not in used
        assert "return_6m" not in used
        assert "pct_off_52w_high" not in used, \
            "zirveye yakinlik odullendirilmemeli — firsatin azaldigi anlamina gelir"

    def test_momentum_now_measures_stabilisation(self):
        from src.config import SCORE_COMPONENTS
        used = {c["metric"] for c in SCORE_COMPONENTS["momentum"]}
        assert used == {"rel_strength_3m", "rel_strength_6m"}

    def test_three_month_relative_strength_computed(self):
        f = fixtures.dbx()
        f.price_history = [(f"2026-{m:02d}-01", 100.0 + m) for m in range(1, 13)] * 30
        bench = [(f"2026-{m:02d}-01", 100.0) for m in range(1, 13)] * 30
        r = metrics.compute(f, benchmark=bench)
        assert "rel_strength_3m" in r["metrics"]


# ---------------------------------------------------------- uc degerler
class TestOutlierCaps:
    """NTAP ROIC %352, AVPT %179 — geri alim sonrasi yatirilan sermaye
    sifira yaklasinca oran patliyor ve yuzdelik dagilimini kendine cekiyor."""

    def test_roic_capped_for_ranking_only(self):
        assert scoring.cap_for_scoring("roic", 352.0) == SCORE_CAPS["roic"][1]
        assert scoring.cap_for_scoring("roic", 22.0) == 22.0

    def test_cash_conversion_capped(self):
        assert scoring.cap_for_scoring("cash_conversion", 40.6) == 5.0

    def test_uncapped_metric_passes_through(self):
        assert scoring.cap_for_scoring("gross_margin", 82.0) == 82.0

    def test_cap_does_not_touch_displayed_value(self):
        from src import cards
        f = fixtures.dbx()
        c = cards.build(f, source="test")
        shown = c["metrics"]["roic"]["value"]
        assert shown is not None and shown > SCORE_CAPS["roic"][1], \
            "gercek deger kartta oldugu gibi kalmali"

    def test_debt_free_company_gets_credit_not_blank(self):
        """Borcu olmayan sirket 'veri yok' diye saglamlik puanindan pay
        alamiyordu — tersine bir yanlilik."""
        f = fixtures.lscc()      # borcsuz
        p = f.annuals[-1]
        p.interest_expense = 0
        r = metrics.compute(f)
        assert r["metrics"]["interest_coverage"] == SCORE_CAPS["interest_coverage"][1]

    def test_indebted_company_without_interest_data_stays_blank(self):
        f = fixtures.dbx()       # 1.980M borc
        f.annuals[-1].interest_expense = None
        r = metrics.compute(f)
        assert r["metrics"]["interest_coverage"] is None

    def test_cash_conversion_blank_when_net_income_negligible(self):
        """KVYO'da net kar sifira yakinken oran 40,6 cikiyordu."""
        f = fixtures.kvyo()
        p = f.annuals[-1]
        p.net_income = p.revenue * 0.005      # hasilatin %0,5'i
        p.cfo = 250
        r = metrics.compute(f)
        assert r["metrics"]["cash_conversion"] is None

    def test_cash_conversion_kept_when_net_income_meaningful(self):
        f = fixtures.dbx()
        r = metrics.compute(f)
        assert r["metrics"]["cash_conversion"] is not None


# ------------------------------------------------------- huni alarmlari
class TestFunnelFalseAlarms:
    def _row(self, name="KVYO"):
        r = funnel.evaluate(fixtures.ALL[name]())
        r["avg_dollar_volume_30d"] = 50e6
        r["metrics"]["sbc_to_fcf"] = 0.5
        r["metrics"]["share_count_change_1y"] = 1.0
        return r

    def test_one_off_dilution_forgiven_when_shares_now_falling(self):
        """MNTN %268 (IPO'da imtiyazli donusum), QTWO %8,3 (konvertibl itfasi),
        AVPT %24,8 (eski SPAC) — surekli seyrelme degil."""
        r = self._row()
        r["metrics"]["share_count_change_1y"] = 24.8
        f = r["fundamentals"]
        f.quarters = [Period(period_end=f"2026-{m:02d}-30", period_type="Q",
                             shares_diluted=c)
                      for m, c in ((3, 220.0), (6, 215.0), (9, 210.0))]
        assert funnel.stage1(r) is None
        assert r["stage1_exemptions"]

    def test_ongoing_dilution_still_kills(self):
        r = self._row()
        r["metrics"]["share_count_change_1y"] = 24.8
        f = r["fundamentals"]
        f.quarters = [Period(period_end=f"2026-{m:02d}-30", period_type="Q",
                             shares_diluted=c)
                      for m, c in ((3, 200.0), (6, 210.0), (9, 220.0))]
        assert "Hisse sayisi artisi" in funnel.stage1(r)

    def _cheap_peer_table(self, row):
        """Sirketi sektorun en ucuzu yapan bir akran havuzu kurar; boylece
        Asama 3'un ucuzluk kapisi acilir ve ima edilen buyume testine
        gercekten ulasilir."""
        import copy
        from src import percentiles
        peers = []
        for i in range(10):
            p = copy.deepcopy(row)
            p["metrics"] = dict(row["metrics"])
            p["metrics"]["ev_gross_profit"] = 20.0 + i     # hepsi bizden pahali
            p["metrics"]["ev_sales"] = 20.0 + i
            peers.append(p)
        row["metrics"]["ev_gross_profit"] = 2.0
        row["metrics"]["ev_sales"] = 2.0
        return percentiles.build_sector_table(peers + [row])

    def test_implied_growth_gets_absolute_headroom(self):
        """ADEA: CAGR %0,3 olunca carpimsal esik %0,45'e duser ve %4,5'lik
        makul bir ima edilen buyume 'asiri' sayilirdi."""
        r = self._row()
        r["metrics"]["rev_cagr_3y"] = 0.3
        r["metrics"]["implied_growth"] = 4.5
        r["own_pct"] = {}
        table = self._cheap_peer_table(r)
        assert funnel.stage3(r, "B", table) is None

    def test_genuinely_excessive_implied_growth_still_kills(self):
        r = self._row()
        r["metrics"]["rev_cagr_3y"] = 0.3
        r["metrics"]["implied_growth"] = 40.0
        r["own_pct"] = {}
        table = self._cheap_peer_table(r)
        assert "Ima edilen buyume" in (funnel.stage3(r, "B", table) or "")


class TestAltmanSaaSException:
    """FRSH -1,26 ile 'iflas bolgesi' cikiyordu; 665 mn $ net nakdi ve hic
    borcu yok. Sebep: pesin tahsil edilen abonelik bedeli ertelenmis gelir
    olarak kisa vadeli yukumluluge yaziliyor."""

    def _saas(self, deferred, cash, debt):
        return Period(
            period_end="2026-06-30", period_type="TTM",
            assets=1200, current_assets=900, current_liabilities=700,
            liabilities=800, equity=400, retained_earnings=-300,
            operating_income=40, deferred_revenue=deferred,
            cash=cash, short_term_investments=0,
            long_term_debt=debt, short_term_debt=0)

    def test_deferred_revenue_heavy_net_cash_company_is_flagged(self):
        r = scores.altman_z(self._saas(deferred=500, cash=665, debt=0))
        assert r["unreliable"] is True
        assert "Ertelenmis gelir" in r["reason"]

    def test_indebted_company_not_exempted(self):
        r = scores.altman_z(self._saas(deferred=500, cash=100, debt=900))
        assert r["unreliable"] is False

    def test_low_deferred_revenue_not_exempted(self):
        r = scores.altman_z(self._saas(deferred=50, cash=665, debt=0))
        assert r["unreliable"] is False

    def test_exempted_company_is_not_killed_at_stage2(self):
        r = funnel.evaluate(fixtures.lscc())
        r["flags"]["z_unreliable"] = True
        r["metrics"]["altman_z"] = -1.26
        assert funnel.stage2(r, "A") is None


# ------------------------------------------------- bayrak/puan aktarimi
class TestZUnreliableReachesFunnel:
    """Istisna scores.altman_z icinde DOGRU hesaplaniyordu ama huniye hic
    ulasmiyordu: funnel satirindaki ``flags`` yalnizca metrics.compute'tan
    geliyor, o da sadece ozkaynak negatifligine bakiyor. FRSH boylece
    "Altman Z'' -1.26" gerekcesiyle eleniyordu.

    Mevcut testler bayragi ELLE set ettigi icin kopuklugu gormuyordu;
    bu testler zinciri uctan uca kuruyor.
    """

    def test_scores_compute_exports_flag(self):
        f = fixtures.frsh()
        res = scores.compute(f, metrics.compute(f))
        assert res["flags"]["z_unreliable"] is True
        assert "Ertelenmis gelir" in res["flags"]["z_unreliable_reason"]

    def test_funnel_row_carries_flag_without_manual_override(self):
        r = funnel.evaluate(fixtures.frsh())
        assert r["metrics"]["altman_z"] < 1.1        # esigin altinda
        assert r["flags"]["z_unreliable"] is True    # ama guvenilmez
        assert r["flags"].get("z_unreliable_reason")

    def test_subscription_company_survives_stage2(self):
        r = funnel.evaluate(fixtures.frsh())
        reason = funnel.stage2(r, "A")
        assert reason is None or "Altman" not in reason

    def test_negative_equity_still_flagged(self):
        """Eski (ozkaynak) yolu kirilmadi."""
        r = funnel.evaluate(fixtures.dbx())
        assert r["flags"]["z_unreliable"] is True

    def test_healthy_company_not_flagged(self):
        r = funnel.evaluate(fixtures.lscc())
        assert r["flags"]["z_unreliable"] is False

    def test_card_warning_uses_actual_reason(self):
        from src import cards
        c = cards.build(fixtures.frsh(), source="test")
        assert c["flags"]["z_unreliable"] is True
        assert any("Ertelenmis gelir" in w for w in c["flags"]["warnings"])


# ----------------------------------------- kapsama carpani merge yolunda
class TestCoverageSurvivesMerge:
    """Kapsama carpani ``scoring.compute`` icinde dogru uygulaniyordu, ama
    ``merge_story`` katalizor puani girildiginde toplami BASTAN hesapliyor
    ve kapsamayi gecmiyordu — carpanlar sessizce 1,0'a donuyordu.

    YOU'nun kartinda tam olarak bu oldu: kalite kapsamasi 0,30, "veri
    yetersiz" rozeti gorunuyor, ama coverage_factors 1,0 ve puan
    cezalandirilmamis.
    """

    def _card(self):
        return {
            "ticker": "YOU",
            "scores": {"value": 96.2, "quality": 96.7, "safety": 53.0,
                       "momentum": 6.0, "earnings_quality": 56.9},
            "score_detail": {
                "value": {"coverage": 0.80},
                "quality": {"coverage": 0.30},     # 3 metrik bos
                "safety": {"coverage": 1.0},
                "momentum": {"coverage": 1.0},
                "earnings_quality": {"coverage": 0.80},
            },
        }

    def test_block_coverage_reads_detail(self):
        from src import cards
        cov = cards.block_coverage(self._card()["score_detail"])
        assert cov["quality"] == 0.30
        assert cov["safety"] == 1.0

    def test_block_coverage_tolerates_missing_detail(self):
        from src import cards
        assert cards.block_coverage(None) == {}
        assert cards.block_coverage({"quality": {}}) == {}

    def test_merge_keeps_coverage_factors(self, tmp_path):
        from src import cards
        (tmp_path / "YOU.json").write_text(
            '{"ticker": "YOU", "catalyst_score": 45}', encoding="utf-8")
        card = cards.merge_story(self._card(), inbox_dir=tmp_path)
        factors = card["scores"]["coverage_factors"]
        assert factors["quality"] == COVERAGE["min_weight_factor"]   # 0,30 -> taban
        assert factors["safety"] == 1.0

    def test_merge_penalises_total(self, tmp_path):
        """Dusuk kapsamali YUKSEK puan artik toplami tek basina tasiyamaz."""
        from src import cards
        (tmp_path / "YOU.json").write_text(
            '{"ticker": "YOU", "catalyst_score": 45}', encoding="utf-8")
        thin = cards.merge_story(self._card(), inbox_dir=tmp_path)

        full_card = self._card()
        full_card["score_detail"]["quality"]["coverage"] = 1.0
        full = cards.merge_story(full_card, inbox_dir=tmp_path)

        assert thin["scores"]["total"] < full["scores"]["total"]


# ------------------------------------------------- elle veri duzeltmeleri
class TestOverrides:
    """Chat'teki ajan veride hata buldugunda sayiyi DOGRUDAN yazamamali;
    kaynagiyla birlikte ham donem verisini duzeltmeli ve her sey yeniden
    hesaplanmali."""

    def _entry(self, **kw):
        base = {"ticker": "YOU", "period_end": "latest", "field": "gross_profit",
                "value": 190.4, "reason": "10-Q s.4", "author": "claude",
                "source_url": "https://www.sec.gov/Archives/x.htm"}
        base.update(kw)
        return base

    def test_valid_entry_accepted(self):
        assert overrides.validate_entry(self._entry()) == []

    def test_source_is_mandatory(self):
        problems = overrides.validate_entry(self._entry(source_url=""))
        assert any("source_url" in p for p in problems)

    def test_reason_is_mandatory(self):
        problems = overrides.validate_entry(self._entry(reason=""))
        assert any("reason" in p for p in problems)

    def test_derived_field_rejected(self):
        """fcf bir ozellik — ezilirse girdiyle cikti celisir."""
        problems = overrides.validate_entry(self._entry(field="fcf"))
        assert any("ham alan degil" in p for p in problems)

    def test_score_field_rejected(self):
        problems = overrides.validate_entry(self._entry(field="total"))
        assert problems

    def test_apply_changes_raw_period_and_reports_provenance(self):
        f = fixtures.frsh()
        before = f.latest_period().gross_profit
        applied = overrides.apply(f, [self._entry(ticker="FRSH", value=700.0)])
        assert len(applied) == 1
        assert f.latest_period().gross_profit == 700.0
        assert applied[0]["before"] == before
        assert applied[0]["after"] == 700.0
        assert applied[0]["source_url"].startswith("https://")

    def test_apply_is_scoped_to_ticker(self):
        f = fixtures.frsh()
        before = f.latest_period().gross_profit
        overrides.apply(f, [self._entry(ticker="YOU", value=700.0)])
        assert f.latest_period().gross_profit == before

    def test_metrics_recompute_from_corrected_input(self):
        """Duzeltme brut MARJI da degistirmeli — metrigi ayrica yazmaya
        gerek kalmamali."""
        f = fixtures.frsh()
        base = metrics.compute(f)["metrics"]["gross_margin"]
        overrides.apply(f, [self._entry(ticker="FRSH", value=400.0)])
        assert metrics.compute(f)["metrics"]["gross_margin"] != base

    def test_card_warns_and_records(self):
        from src import cards
        f = fixtures.frsh()
        f.overrides_applied = overrides.apply(f, [self._entry(ticker="FRSH", value=700.0)])
        c = cards.build(f, source="test")
        assert c["overrides"][0]["field"] == "gross_profit"
        assert any("ELLE DUZELTME" in w for w in c["flags"]["warnings"])

    def test_unknown_period_is_skipped_not_crashed(self):
        f = fixtures.frsh()
        assert overrides.apply(f, [self._entry(ticker="FRSH", period_end="1999-01-01")]) == []


# ----------------------------------------------- puan yayimlama tabani
class TestScoreFloor:
    """FRSH: tum otomatik bloklar bos, yalnizca elle girilen katalizor (60)
    kaldi; toplam 60,0 cikti ve sirket siralamaya altinci olarak girdi."""

    def test_catalyst_only_is_not_published(self):
        s = scoring.total_score({k: None for k in
                                 ("value", "quality", "safety", "momentum", "earnings_quality")},
                                catalyst=60.0)
        assert s["total"] is None
        assert s["weight_coverage"] == 0.25
        assert "katalizor" in s["not_scored"]

    def test_normal_coverage_still_published(self):
        s = scoring.total_score({"value": 60.0, "quality": 60.0, "safety": 60.0,
                                 "momentum": 60.0, "earnings_quality": 60.0}, catalyst=60.0)
        assert s["total"] == 60.0
        assert "not_scored" not in s

    def test_nothing_at_all(self):
        s = scoring.total_score({k: None for k in
                                 ("value", "quality", "safety", "momentum", "earnings_quality")})
        assert s["total"] is None and s["not_scored"]


# ------------------------------------------- alt kume kosusu yuzdelik havuzu
class TestSubsetPercentilePool:
    def test_single_row_pool_yields_no_percentiles(self):
        """Hatanin kendisi: tek satirlik havuzda yuzdelik cikmaz."""
        from src import percentiles
        r = funnel.evaluate(fixtures.frsh())
        table = percentiles.build_sector_table([r])
        p, basis = percentiles.sector_percentile(table, r["sector"], "gross_margin",
                                                 r["metrics"]["gross_margin"])
        assert p is None and basis == "none"

    def test_pool_from_cards_restores_percentiles(self, tmp_path, monkeypatch):
        import json
        from src import percentiles, pipeline
        r = funnel.evaluate(fixtures.frsh())
        for i in range(10):
            (tmp_path / f"P{i}.json").write_text(json.dumps({
                "ticker": f"P{i}", "sector": r["sector"],
                "metrics": {"gross_margin": {"value": 50.0 + i * 4}}}))
        monkeypatch.setattr(pipeline, "CARDS_DIR", tmp_path)
        pool = [r] + pipeline.sector_rows_from_cards(exclude={"FRSH"})
        table = percentiles.build_sector_table(pool)
        p, basis = percentiles.sector_percentile(table, r["sector"], "gross_margin",
                                                 r["metrics"]["gross_margin"])
        assert p is not None and basis == "sector"

    def test_run_tickers_excluded_from_card_pool(self, tmp_path, monkeypatch):
        import json
        from src import pipeline
        (tmp_path / "FRSH.json").write_text(json.dumps({"ticker": "FRSH", "sector": "x", "metrics": {}}))
        monkeypatch.setattr(pipeline, "CARDS_DIR", tmp_path)
        assert pipeline.sector_rows_from_cards(exclude={"FRSH"}) == []


# --------------------------------------------- pano veri dogrulugu denetimi
class TestDisplayCorrectness:
    """Sirket sayfasindaki sayilarin ve isaretlerin dogrulugu."""

    def test_negative_sentences_exist_for_sign_flipping_metrics(self):
        """Negatifte anlami donen her metrigin ayri bir cumlesi olmali."""
        from src import config
        for key in ("implied_growth", "fcf_margin", "operating_margin", "roic",
                    "rev_cagr_3y", "earnings_yield", "fcf_yield_ev",
                    "fcf_yield_mcap", "return_12m", "rel_strength_12m"):
            assert config.THRESHOLDS[key].get("sentence_neg"), key

    def test_negative_sentence_reverses_meaning(self):
        from src import config
        assert "KUCULME" in config.THRESHOLDS["implied_growth"]["sentence_neg"]
        assert "YAKILIYOR" in config.THRESHOLDS["fcf_margin"]["sentence_neg"]
        assert "buyume" not in config.THRESHOLDS["implied_growth"]["sentence_neg"]

    def test_thresholds_payload_carries_negative_sentences(self):
        """Pano bunu thresholds.json'dan okuyor; payload'a girmezse ise yaramaz."""
        from src import config
        payload = config.thresholds_payload()
        assert payload["thresholds"]["implied_growth"].get("sentence_neg")

    def test_sparkline_ends_on_latest_price(self):
        from src.sources.prices import sparkline
        rows = [(f"2026-{(i // 28) + 1:02d}-{(i % 28) + 1:02d}", 100.0 + i)
                for i in range(200)]
        sp = sparkline(rows)
        assert sp[-1] == rows[-1][1]
        assert sp[0] == rows[-126][1]

    def test_color_matches_displayed_value(self):
        """Kartta yazan sayi ile rengi ayni girdiden gelmeli."""
        from src import cards
        from src.config import color_for
        for key, raw in (("sbc_to_fcf", 0.2996), ("current_ratio", 1.9996)):
            shown = cards._round(raw, key)
            assert color_for(key, shown) == color_for(key, cards._round(raw, key))

    def test_daily_refresh_updates_peg_and_implied_growth(self):
        from src import run_daily
        from tests.test_daily_refresh import base_card
        c = base_card()
        c["metrics"]["rev_growth_ttm"] = {"value": 10.0, "sector_pct": None,
                                          "own_5y_pct": None, "pct_basis": "none"}
        run_daily._refresh_price_derived(
            c, {"price": 28.67, "history": [], "high_52w": 32.0}, [])
        pe = c["metrics"]["pe"]["value"]
        assert c["metrics"]["peg"]["value"] == pytest.approx(pe / 10.0, abs=0.01)
        # ters DCF alani da EV ile birlikte tazelenmeli
        assert "implied_growth_pct" in c["reverse_dcf"]

    def test_peg_follows_price(self):
        """Fiyat degisince peg de degismeli — pe ile birlikte."""
        from src import run_daily
        from tests.test_daily_refresh import base_card
        out = []
        for price in (28.67, 14.34):
            c = base_card()
            c["metrics"]["rev_growth_ttm"] = {"value": 10.0, "sector_pct": None,
                                              "own_5y_pct": None, "pct_basis": "none"}
            run_daily._refresh_price_derived(
                c, {"price": price, "history": [], "high_52w": 32.0}, [])
            out.append(c["metrics"]["peg"]["value"])
        assert out[1] < out[0]

    def test_chart_metric_contradiction_is_flagged(self):
        """Ceyreklik grafik ile TTM metrigi celisirse kart bunu yazmali."""
        from src import cards
        f = fixtures.frsh()
        c = cards.build(f, source="test")
        # tutarli fixture'da uyari CIKMAMALI
        assert not any("GRAFIK-METRIK" in w for w in c["flags"]["warnings"])


class TestSurvivorsIndex:
    """Huni sayfasi 157 ayri dosyayi cekemez; kompakt indeks okur."""

    def test_index_follows_isolated_dir(self, tmp_path, monkeypatch):
        """Indeks SURVIVOR_DIR'in yanina yazilmali.

        DATA_DIR'e sabitlenseydi test kosusu gercek data/survivors.json'i
        sifirlardi — bir kez oldu.
        """
        import json
        from src import scan
        surv = tmp_path / "survivors"
        surv.mkdir()
        (surv / "AAA.json").write_text(json.dumps({
            "ticker": "AAA", "name": "A Inc", "sector": "Yazilim", "track": "A",
            "metrics": {"rev_growth_ttm": 12.0}, "meta": {"market_cap_musd": 900.0}}))
        monkeypatch.setattr(scan, "SURVIVOR_DIR", surv)
        scan.write_survivors_index()

        out = json.loads((tmp_path / "survivors.json").read_text())
        assert out["count"] == 1
        assert out["survivors"][0]["ticker"] == "AAA"
        assert out["survivors"][0]["market_cap_musd"] == 900.0
        # gercek veri klasorune dokunulmadi
        assert not (tmp_path / "data").exists()


class TestAuditTolerance:
    """Denetim, yuvarlamayi hatadan ayirmali — ama gercek sapmayi kacirmamali."""

    def _audit(self):
        import importlib.util
        import pathlib
        spec = importlib.util.spec_from_file_location(
            "audit_cards", pathlib.Path("scripts/audit_cards.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_rounding_is_not_an_error(self):
        """ConEd: net kar 2,0 saklanmis, gercegi 2,02 — F/K farki hata degil."""
        m = self._audit()
        a = m.Audit()
        a.check({"ticker": "ED"}, "pe", 19158.8, 38758.3 / 2.0, den=2.0)
        assert not a.errors

    def test_real_drift_is_still_caught(self):
        """QLYS'de peg %13 kaymisti; tolerans bunu yutmamali."""
        m = self._audit()
        a = m.Audit()
        a.check({"ticker": "QLYS"}, "peg", 2.75, 25.176 / 10.35, den=10.35)
        assert a.errors

    def test_tolerance_scales_with_denominator_precision(self):
        m = self._audit()
        a = m.Audit()
        # Buyuk paydada yuvarlama onemsiz; ayni goreli sapma HATA olmali
        a.check({"ticker": "X"}, "oran", 10.0, 10.5, den=5000.0)
        assert a.errors


# ------------------------------------------------------ canli genel bakis
class TestMarketSnapshot:
    def test_risk_note_reads_vix(self):
        from src.sources import market
        assert "gergin" in market.risk_note([{"symbol": "^VIX", "value": 31.0}])
        assert "rehavet" in market.risk_note([{"symbol": "^VIX", "value": 11.0}])
        assert "normal" in market.risk_note([{"symbol": "^VIX", "value": 18.0}])
        assert market.risk_note([]) is None

    def test_one_broken_symbol_does_not_kill_the_strip(self, monkeypatch):
        """Tek endeks cekilemezse butun serit bos kalmamali."""
        import pandas as pd
        from src.sources import market

        def fake(symbol, days=40):
            if symbol == "BAD":
                raise RuntimeError("yok")
            return pd.DataFrame({"Close": [100.0, 102.0, 101.0, 105.0, 110.0, 108.0]},
                                index=pd.to_datetime(
                                    ["2026-09-08", "2026-09-09", "2026-09-10",
                                     "2026-09-11", "2026-09-12", "2026-09-15"]))
        monkeypatch.setattr(market, "_history", fake)
        rows = market.snapshot([("BAD", "Bozuk", "Hisse", "puan"),
                                ("OK", "Calisan", "Hisse", "puan")])
        assert [r["symbol"] for r in rows] == ["OK"]
        assert rows[0]["change_1d_pct"] == pytest.approx(-1.82, abs=0.01)
        assert rows[0]["change_5d_pct"] == pytest.approx(8.0, abs=0.01)


class TestCriticalDates:
    def _subs(self, forms, dates):
        return {"filings": {"recent": {
            "form": forms, "filingDate": dates,
            "accessionNumber": ["0001-24-000001"] * len(forms),
            "primaryDocument": ["a.htm"] * len(forms)}}}

    def test_form4_noise_is_excluded(self, monkeypatch):
        """Form 4 gunde onlarca geliyor ve yon tasimiyor; takvimi bogar."""
        from src.sources import calendar_src, edgar_api
        from src.util import today_iso
        today = today_iso()
        monkeypatch.setattr(edgar_api, "submissions",
                            lambda cik: self._subs(["4", "8-K", "4"], [today] * 3))
        out = calendar_src.sec_events({"AAA": 123})
        assert len(out) == 1
        assert out[0]["title"] == "AAA · 8-K"
        assert out[0]["detail"] == "Onemli olay bildirimi"

    def test_old_filings_are_not_listed(self, monkeypatch):
        from src.sources import calendar_src, edgar_api
        monkeypatch.setattr(edgar_api, "submissions",
                            lambda cik: self._subs(["8-K"], ["2020-01-01"]))
        assert calendar_src.sec_events({"AAA": 123}) == []

    def test_earnings_only_for_tracked_tickers(self):
        from datetime import date, timedelta
        from src.sources import calendar_src
        soon = (date.today() + timedelta(days=5)).isoformat()
        far = (date.today() + timedelta(days=400)).isoformat()
        out = calendar_src.earnings_events(
            {"AAA": soon, "BBB": soon, "CCC": far}, {"AAA", "CCC"})
        assert [e["ticker"] for e in out] == ["AAA"]   # BBB takipsiz, CCC cok uzak

    def test_build_splits_past_and_future(self, monkeypatch):
        from datetime import date, timedelta
        from src.sources import calendar_src
        monkeypatch.setattr(calendar_src, "macro_releases", lambda **kw: [
            {"date": (date.today() + timedelta(days=3)).isoformat(), "kind": "makro",
             "title": "TUFE", "detail": "enflasyon", "ticker": None},
            {"date": (date.today() - timedelta(days=3)).isoformat(), "kind": "makro",
             "title": "Eski", "detail": "x", "ticker": None}])
        monkeypatch.setattr(calendar_src, "sec_events", lambda *a, **k: [])
        out = calendar_src.build(earnings={}, tickers=set(), cik_by_ticker={})
        assert [e["title"] for e in out["upcoming"]] == ["TUFE"]
        assert [e["title"] for e in out["recent"]] == ["Eski"]


class TestMacroNotClobbered:
    def test_empty_fetch_keeps_existing_file(self, tmp_path, monkeypatch):
        """FRED cevap vermeyince calisan pano 'veri yok'a dusmemeli."""
        import json
        from src import pipeline
        from src.sources import fred_api
        path = tmp_path / "macro.json"
        path.write_text(json.dumps({"series": {"cpi_yoy": {"value": 3.3}}}))
        monkeypatch.setattr(pipeline, "DATA_DIR", tmp_path)
        monkeypatch.setattr(fred_api, "snapshot", lambda: {})
        pipeline.write_macro()
        assert json.loads(path.read_text())["series"]["cpi_yoy"]["value"] == 3.3
