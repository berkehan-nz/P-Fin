"""funnel.py — asama mantigi ve eleme sebepleri."""

from src import funnel
from tests import fixtures


def row_for(name):
    f = fixtures.ALL[name]()
    r = funnel.evaluate(f)
    r["avg_dollar_volume_30d"] = 50e6      # likidite testi gecsin
    return r


def clean_row(name="KVYO"):
    """Asama 1'i gecen bir satir. KVYO gercekte seyrelme ve SBC/FCF
    esiklerine takilir (bkz. test_kvyo_fails_on_dilution); tek bir esigi
    izole etmek icin bunlari notr degere cekiyoruz."""
    r = row_for(name)
    r["metrics"]["share_count_change_1y"] = 1.0
    r["metrics"]["sbc_to_fcf"] = 0.5
    return r


class TestStage0:
    def test_seed_companies_pass_universe(self):
        for name in ("DBX", "LSCC", "KVYO"):
            assert funnel.stage0(row_for(name)) is None, name

    def test_financials_excluded_by_sic(self):
        r = row_for("DBX")
        r["sic"] = 6022      # ticari banka
        assert "6000-6799" in funnel.stage0(r)

    def test_market_cap_floor(self):
        r = row_for("DBX")
        r["meta"]["market_cap_musd"] = 100
        assert "Piyasa degeri <" in funnel.stage0(r)

    def test_market_cap_ceiling(self):
        r = row_for("DBX")
        r["meta"]["market_cap_musd"] = 80_000
        assert "Piyasa degeri >" in funnel.stage0(r)

    def test_penny_stock_excluded(self):
        r = row_for("DBX")
        r["meta"]["price"] = 3.0
        assert "Fiyat <" in funnel.stage0(r)

    def test_illiquid_excluded(self):
        r = row_for("DBX")
        r["avg_dollar_volume_30d"] = 1e6
        assert "dolar hacmi" in funnel.stage0(r)

    def test_revenueless_biotech_excluded(self):
        r = row_for("DBX")
        r["sic"] = 2836
        r["meta"]["revenue_ttm_musd"] = 2.0
        assert "biyoteknoloji" in funnel.stage0(r)

    def test_biotech_with_revenue_passes(self):
        r = row_for("DBX")
        r["sic"] = 2836      # hasilat 2470M, esik 10M
        assert funnel.stage0(r) is None


class TestStage1:
    def test_kvyo_fails_on_dilution_and_sbc(self):
        """Klaviyo tipi yuksek SBC'li buyume hissesi Asama 1'de elenir.

        Seyreltilmis hisse sayisi %6.9 artmis (esik %5) ve SBC/FCF 1.51
        (esik 1.0). Sartnamenin kastettigi davranis budur: buyume ne kadar
        guclu olursa olsun, uretilen nakdin tamami calisana hisse olarak
        gidiyorsa hissedar bundan pay almiyor demektir.
        """
        reason = funnel.stage1(row_for("KVYO"))
        assert "Hisse sayisi artisi" in reason

    def test_clean_growth_company_passes(self):
        assert funnel.stage1(clean_row()) is None

    def test_dbx_fails_on_growth(self):
        # DBX hasilati daraliyor (-%3.1) -> %5 esigini gecemez
        reason = funnel.stage1(row_for("DBX"))
        assert "Hasilat buyumesi" in reason

    def test_low_gross_margin_rejected(self):
        r = clean_row()
        r["metrics"]["gross_margin"] = 25.0
        assert "Brut marj" in funnel.stage1(r)

    def test_negative_fcf_without_exemption_rejected(self):
        r = clean_row()
        r["meta"]["fcf_ttm_musd"] = -50
        r["metrics"]["rule_of_40"] = 20.0     # istisna saglanmaz
        assert "FCF negatif" in funnel.stage1(r)

    def test_negative_fcf_with_exemption_passes(self):
        r = clean_row()
        r["meta"]["fcf_ttm_musd"] = -50
        r["metrics"]["rev_growth_ttm"] = 30.0
        r["metrics"]["rule_of_40"] = 45.0
        assert funnel.stage1(r) is None

    def test_leveraged_balance_sheet_rejected(self):
        r = clean_row()
        r["metrics"]["net_debt_to_ebitda"] = 4.5
        assert "Net borc/FAVOK" in funnel.stage1(r)

    def test_dilution_rejected(self):
        r = clean_row()
        r["metrics"]["share_count_change_1y"] = 8.0
        assert "Hisse sayisi artisi" in funnel.stage1(r)

    def test_sbc_eating_all_cash_rejected(self):
        r = clean_row()
        r["metrics"]["sbc_to_fcf"] = 1.4
        assert "SBC/FCF" in funnel.stage1(r)


class TestStage2:
    def test_manipulation_suspect_killed(self):
        r = row_for("LSCC")
        r["metrics"]["beneish_m"] = -1.5
        assert "Beneish" in funnel.stage2(r, "A")

    def test_distress_zone_killed(self):
        r = row_for("LSCC")
        r["metrics"]["altman_z"] = 0.8
        assert "Altman" in funnel.stage2(r, "A")

    def test_negative_equity_skips_altman(self):
        """Ozkaynak negatifse Z'' anlamsiz — bu testle ELEME yapilmamali."""
        r = row_for("DBX")
        r["metrics"]["altman_z"] = 0.5
        assert r["flags"]["z_unreliable"] is True
        assert funnel.stage2(r, "A") is None

    def test_piotroski_floor_only_applies_to_track_a(self):
        r = clean_row()
        r["metrics"]["piotroski_f"] = 3
        assert "Piotroski" in funnel.stage2(r, "A")
        assert funnel.stage2(r, "B") is None      # Kol B'de esik yok

    def test_maturity_wall_with_negative_fcf(self):
        r = row_for("LSCC")
        r["metrics"]["maturity_wall_2y"] = 2.0
        r["meta"]["fcf_ttm_musd"] = -10
        assert "Vade duvari" in funnel.stage2(r, "A")

    def test_maturity_wall_alone_is_not_fatal(self):
        r = row_for("LSCC")
        r["metrics"]["maturity_wall_2y"] = 2.0    # FCF pozitif kaliyor
        assert funnel.stage2(r, "A") is None

    def test_recent_ipo_flagged(self):
        from datetime import date, timedelta
        r = clean_row()
        r["ipo_date"] = (date.today() - timedelta(days=120)).isoformat()
        assert "kilit suresi" in funnel.stage2(r, "B")


class TestFullRun:
    def test_run_produces_log_with_every_stage(self):
        rows = [row_for(n) for n in ("DBX", "LSCC", "KVYO")]
        result = funnel.run(rows)
        stages = [s["stage"] for s in result["log"]["stages"]]
        assert stages == [0, 1, 2, 3, 4]
        for s in result["log"]["stages"]:
            assert "input" in s and "output" in s

    def test_killed_rows_carry_reason(self):
        rows = [row_for(n) for n in ("DBX", "LSCC", "KVYO")]
        result = funnel.run(rows)
        for r in result["all_rows"]:
            if r["killed_at"] is not None:
                assert r["kill_reason"], r["ticker"]

    def test_sector_quota_enforced(self):
        rows = []
        for i in range(15):
            r = clean_row()
            r["ticker"] = f"T{i}"
            rows.append(r)
        result = funnel.run(rows, max_per_sector=3)
        assert len(result["candidates"]) <= 3

    def test_diagnose_reports_first_failing_stage(self):
        d = funnel.diagnose(row_for("DBX"))
        # DBX hasilati daraliyor -> Asama 1'de elenir
        assert d["would_fail_at"] == 1
        assert d["passed_stages"] == [0]
        assert "Hasilat buyumesi" in d["kill_reason"]

    def test_diagnose_reports_dilution_for_kvyo(self):
        d = funnel.diagnose(row_for("KVYO"))
        assert d["would_fail_at"] == 1
        assert "Hisse sayisi artisi" in d["kill_reason"]

    def test_diagnose_passing_company_reaches_stage_2(self):
        d = funnel.diagnose(clean_row())
        assert d["would_fail_at"] is None
        assert 2 in d["passed_stages"]
