"""edgar_api XBRL ayristirma — gercek EDGAR verisinde yasanan tuzaklar.

Bu testler ag GEREKTIRMEZ; companyfacts JSON yapisi elle kurulur.
"""

import pytest

from src.sources import edgar_api as ea


def fact(start, end, val, filed="2026-01-01", accn="a-1"):
    return {"start": start, "end": end, "val": val, "filed": filed, "accn": accn}


def facts_doc(tag, entries, ns="us-gaap", unit="USD"):
    return {"facts": {ns: {tag: {"units": {unit: entries}}}}}


class TestCumulativeCashFlow:
    """10-Q'larda nakit akis tablosu YIL BASINDAN ITIBAREN kumulatiftir.

    DOCU'da gorulen: 12 ceyregin yalnizca 3'unde FCF vardi, cunku Q2 dosyasi
    6 aylik, Q3 dosyasi 9 aylik rakam veriyor ve ceyrek filtresi (80-100 gun)
    bunlari eliyordu.
    """

    def _ytd_doc(self):
        # Mali yil 2025-01-01 baslangicli, kumulatif CFO: 100 / 250 / 420 / 600
        return facts_doc("NetCashProvidedByUsedInOperatingActivities", [
            fact("2025-01-01", "2025-03-31", 100),
            fact("2025-01-01", "2025-06-30", 250),
            fact("2025-01-01", "2025-09-30", 420),
            fact("2025-01-01", "2025-12-31", 600),
        ])

    def test_quarterly_values_derived_by_differencing(self):
        out = ea._collect_cumulative_quarterly(
            self._ytd_doc(), ["NetCashProvidedByUsedInOperatingActivities"])
        assert out["2025-03-31"] == 100      # Q1 = kumulatif 3 ay
        assert out["2025-06-30"] == 150      # 250 - 100
        assert out["2025-09-30"] == 170      # 420 - 250
        assert out["2025-12-31"] == 180      # 600 - 420

    def test_quarterly_sum_equals_annual(self):
        out = ea._collect_cumulative_quarterly(
            self._ytd_doc(), ["NetCashProvidedByUsedInOperatingActivities"])
        assert sum(out.values()) == 600

    def test_separate_fiscal_years_do_not_mix(self):
        doc = facts_doc("NetCashProvidedByUsedInOperatingActivities", [
            fact("2024-01-01", "2024-03-31", 90),
            fact("2024-01-01", "2024-06-30", 200),
            fact("2025-01-01", "2025-03-31", 100),
            fact("2025-01-01", "2025-06-30", 250),
        ])
        out = ea._collect_cumulative_quarterly(
            doc, ["NetCashProvidedByUsedInOperatingActivities"])
        assert out["2024-06-30"] == 110      # 200 - 90, onceki yila bulasmaz
        assert out["2025-06-30"] == 150

    def test_missing_middle_period_skips_that_quarter(self):
        """9 aylik rakam yoksa Q3 turetilemez; uydurma yapilmaz."""
        doc = facts_doc("NetCashProvidedByUsedInOperatingActivities", [
            fact("2025-01-01", "2025-03-31", 100),
            fact("2025-01-01", "2025-06-30", 250),
            fact("2025-01-01", "2025-12-31", 600),
        ])
        out = ea._collect_cumulative_quarterly(
            doc, ["NetCashProvidedByUsedInOperatingActivities"])
        assert "2025-12-31" not in out       # 9 aylik yok -> Q4 turetilemez
        assert out["2025-06-30"] == 150

    def test_period_buckets(self):
        assert ea._period_bucket(fact("2025-01-01", "2025-03-31", 1)) == 1
        assert ea._period_bucket(fact("2025-01-01", "2025-06-30", 1)) == 2
        assert ea._period_bucket(fact("2025-01-01", "2025-09-30", 1)) == 3
        assert ea._period_bucket(fact("2025-01-01", "2025-12-31", 1)) == 4
        # anlik (instant) kayit
        assert ea._period_bucket({"end": "2025-12-31", "val": 1}) is None


class TestSharesOutstanding:
    """Cok sinifli hisselerde kapak sayfasi tek sinif tasiyabilir."""

    def test_cover_page_summed_across_classes(self):
        doc = {"facts": {"dei": {"EntityCommonStockSharesOutstanding": {"units": {"shares": [
            fact(None, "2026-06-30", 40_000_000, accn="x"),
            fact(None, "2026-06-30", 20_000_000, accn="x"),
        ]}}}}}
        assert ea._cover_page_shares(doc) == pytest.approx(60.0)

    def test_duplicate_class_not_double_counted(self):
        doc = {"facts": {"dei": {"EntityCommonStockSharesOutstanding": {"units": {"shares": [
            fact(None, "2026-06-30", 40_000_000, accn="x"),
            fact(None, "2026-06-30", 40_000_000, accn="x"),
        ]}}}}}
        assert ea._cover_page_shares(doc) == pytest.approx(40.0)

    def test_single_class_cover_falls_back_to_diluted(self):
        """MNTN'de gorulen: kapak 16,4M gosterdi, gercek ~78M idi."""
        doc = {"facts": {
            "dei": {"EntityCommonStockSharesOutstanding": {"units": {"shares": [
                fact(None, "2026-06-30", 16_400_000, accn="x")]}}},
            "us-gaap": {"WeightedAverageNumberOfDilutedSharesOutstanding": {
                "units": {"shares": [fact("2026-04-01", "2026-06-30", 78_600_000)]}}},
        }}
        shares, source = ea._shares_outstanding(doc)
        assert shares == pytest.approx(78.6)
        assert "tek sinif" in source

    def test_consistent_cover_page_is_trusted(self):
        doc = {"facts": {
            "dei": {"EntityCommonStockSharesOutstanding": {"units": {"shares": [
                fact(None, "2026-06-30", 100_000_000, accn="x")]}}},
            "us-gaap": {"WeightedAverageNumberOfDilutedSharesOutstanding": {
                "units": {"shares": [fact("2026-04-01", "2026-06-30", 98_000_000)]}}},
        }}
        shares, source = ea._shares_outstanding(doc)
        assert shares == pytest.approx(100.0)
        assert source == "kapak_sayfasi"

    def test_no_cover_page_uses_diluted(self):
        doc = {"facts": {"us-gaap": {
            "WeightedAverageNumberOfDilutedSharesOutstanding": {
                "units": {"shares": [fact("2026-04-01", "2026-06-30", 50_000_000)]}}}}}
        shares, source = ea._shares_outstanding(doc)
        assert shares == pytest.approx(50.0)
        assert source == "seyreltilmis_agirlikli_ortalama"

    def test_nothing_available(self):
        assert ea._shares_outstanding({"facts": {}}) == (None, "yok")


class TestQuarterDetection:
    def test_quarter_and_annual_ranges(self):
        assert ea._is_quarter(fact("2025-01-01", "2025-03-31", 1))
        assert not ea._is_quarter(fact("2025-01-01", "2025-06-30", 1))
        assert ea._is_annual(fact("2025-01-01", "2025-12-31", 1))
        assert not ea._is_annual(fact("2025-01-01", "2025-09-30", 1))

    def test_latest_filing_wins_on_restatement(self):
        entries = [fact("2025-01-01", "2025-03-31", 100, filed="2025-05-01"),
                   fact("2025-01-01", "2025-03-31", 105, filed="2025-11-01")]
        assert ea._pick_best(entries)["val"] == 105


class TestQ4SanityCheck:
    """Turetilmis Q4 (yillik - Q1 - Q2 - Q3) makul olmali.

    GPN'de gorulen: bir ceyrek ~1.900 yerine 159 gorunuyordu, cunku yillik
    rakam bir etiketten, ceyrekler baska bir etiketten geliyordu ve cikarma
    iki farkli olcegi birbirinden cikardi.
    """

    def test_sane_q4_is_written(self):
        annual = {"2025-12-31": 4000.0}
        quarterly = {"2025-03-31": 950.0, "2025-06-30": 1000.0, "2025-09-30": 1050.0}
        ea._derive_q4(annual, quarterly,
                      {"2025-12-31": ["2025-03-31", "2025-06-30", "2025-09-30"]})
        assert quarterly["2025-12-31"] == pytest.approx(1000.0)

    def test_absurd_q4_is_discarded(self):
        """Yillik rakam ceyreklerle ayni olcekte degilse Q4 yazilmaz."""
        annual = {"2025-12-31": 4000.0}
        quarterly = {"2025-03-31": 50.0, "2025-06-30": 55.0, "2025-09-30": 60.0}
        ea._derive_q4(annual, quarterly,
                      {"2025-12-31": ["2025-03-31", "2025-06-30", "2025-09-30"]})
        assert "2025-12-31" not in quarterly

    def test_negative_q4_beyond_tolerance_discarded(self):
        annual = {"2025-12-31": 100.0}
        quarterly = {"2025-03-31": 900.0, "2025-06-30": 950.0, "2025-09-30": 1000.0}
        ea._derive_q4(annual, quarterly,
                      {"2025-12-31": ["2025-03-31", "2025-06-30", "2025-09-30"]})
        assert "2025-12-31" not in quarterly

    def test_seasonal_q4_still_allowed(self):
        """SONO gibi mevsimsel sirketlerde buyuk Q4 GERCEKTIR, elenmemeli."""
        annual = {"2025-12-31": 1600.0}
        quarterly = {"2025-03-31": 260.0, "2025-06-30": 290.0, "2025-09-30": 300.0}
        ea._derive_q4(annual, quarterly,
                      {"2025-12-31": ["2025-03-31", "2025-06-30", "2025-09-30"]})
        assert quarterly["2025-12-31"] == pytest.approx(750.0)   # ~2.6x medyan, gecerli


class TestTagConsistency:
    def test_same_tag_used_for_annual_and_quarterly(self):
        doc = {"facts": {"us-gaap": {
            "Revenues": {"units": {"USD": [
                fact("2025-01-01", "2025-12-31", 4000)]}},           # sadece yillik
            "RevenueFromContractWithCustomerExcludingAssessedTax": {"units": {"USD": [
                fact("2025-01-01", "2025-03-31", 950),
                fact("2025-01-01", "2025-12-31", 4000)]}},           # ikisi de var
        }}}
        annual, quarterly, tag = ea._collect_field(
            doc, ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues"])
        assert tag == "RevenueFromContractWithCustomerExcludingAssessedTax"
        assert annual and quarterly

    def test_falls_back_when_no_tag_has_both(self):
        doc = {"facts": {"us-gaap": {
            "Revenues": {"units": {"USD": [fact("2025-01-01", "2025-12-31", 4000)]}},
        }}}
        annual, quarterly, tag = ea._collect_field(doc, ["Revenues"])
        assert tag == "Revenues"
        assert annual and not quarterly

    def test_no_data_returns_empty(self):
        assert ea._collect_field({"facts": {}}, ["Revenues"]) == ({}, {}, None)
