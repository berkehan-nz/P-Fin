"""config.py butunlugu — esiklerin, tohum listenin ve dashboard sozlesmesinin
kendi icinde tutarli olmasi.

Bu testler "sihirli sayi yok" kuralini korur: dashboard'un ihtiyac duydugu
her metrigin config'de bir esik tanimi olmali, yoksa hucre sessizce gri
kalir ve kimse fark etmez.
"""

import json

import pytest

from src import config, percentiles, scoring
from src.config import (HEADLINE_METRICS, METRIC_BLOCKS, SCORE_COMPONENTS,
                        SCORE_WEIGHTS, SEED_TICKERS, THRESHOLDS, color_for,
                        sector_for_sic, thresholds_payload)


class TestThresholds:
    def test_every_block_metric_has_threshold(self):
        for block, metrics in METRIC_BLOCKS.items():
            for m in metrics:
                assert m in THRESHOLDS, f"{block} icindeki {m} icin esik yok"

    def test_every_headline_metric_has_threshold(self):
        for track, metrics in HEADLINE_METRICS.items():
            for m in metrics:
                assert m in THRESHOLDS, f"Kol {track} basligindaki {m} icin esik yok"

    def test_every_threshold_is_well_formed(self):
        for name, spec in THRESHOLDS.items():
            assert spec["direction"] in ("low_good", "high_good"), name
            assert spec.get("label"), f"{name} etiketsiz"
            assert spec.get("help"), f"{name} icin aciklama yok"
            assert spec.get("formula"), f"{name} icin formul yok"
            if spec["direction"] == "low_good":
                assert spec["green_max"] <= spec["yellow_max"], name
            else:
                assert spec["green_min"] >= spec["yellow_min"], name

    def test_payload_is_json_serializable(self):
        """Dashboard bu sozlugu JSON olarak okur; serialize edilemezse cokerdi."""
        text = json.dumps(thresholds_payload(), ensure_ascii=False, default=str)
        assert len(text) > 1000

    def test_payload_carries_dashboard_contract(self):
        p = thresholds_payload()
        for key in ("thresholds", "metric_blocks", "headline_metrics",
                    "score_weights", "stage1", "stage2", "stage3", "seed"):
            assert key in p, key


class TestColorFor:
    def test_low_good_boundaries(self):
        assert color_for("ev_ebit", 11.9) == "green"
        assert color_for("ev_ebit", 12.0) == "green"     # sinir dahil
        assert color_for("ev_ebit", 12.1) == "yellow"
        assert color_for("ev_ebit", 18.0) == "yellow"
        assert color_for("ev_ebit", 18.1) == "red"

    def test_high_good_boundaries(self):
        assert color_for("fcf_yield_ev", 6.0) == "green"
        assert color_for("fcf_yield_ev", 5.9) == "yellow"
        assert color_for("fcf_yield_ev", 3.0) == "yellow"
        assert color_for("fcf_yield_ev", 2.9) == "red"

    def test_missing_data_is_gray_not_red(self):
        """Veri yoklugu KOTU HABER DEGILDIR — gri, kirmizi degil."""
        assert color_for("ev_ebit", None) == "gray"
        assert color_for("ev_ebit", float("nan")) == "gray"
        assert color_for("bilinmeyen_metrik", 5) == "gray"


class TestScoring:
    def test_weights_sum_to_100(self):
        assert sum(SCORE_WEIGHTS.values()) == 100

    def test_component_weights_sum_to_one(self):
        for block, comps in SCORE_COMPONENTS.items():
            total = sum(c["weight"] for c in comps)
            assert total == pytest.approx(1.0), f"{block} agirliklari {total}"

    def test_every_score_component_is_percentile_ranked(self):
        """Puanlamada kullanilan her metrik icin sektor yuzdeligi hesaplanmali."""
        for block, comps in SCORE_COMPONENTS.items():
            for c in comps:
                assert c["metric"] in percentiles.SECTOR_PERCENTILE_METRICS, \
                    f"{block}/{c['metric']} yuzdelik listesinde yok"

    def test_missing_block_is_renormalized_not_zeroed(self):
        s = scoring.total_score({"value": 80.0, "quality": 60.0, "safety": None,
                                 "momentum": None, "earnings_quality": None})
        # 80*25 + 60*20 = 3200; agirlik 45 -> 71.1
        assert s["total"] == pytest.approx(71.1, abs=0.1)
        assert s["weight_coverage"] == pytest.approx(0.45, abs=0.01)

    def test_no_data_gives_none_not_zero(self):
        s = scoring.total_score({k: None for k in
                                 ("value", "quality", "safety", "momentum",
                                  "earnings_quality")})
        assert s["total"] is None

    def test_inverted_component_flips_percentile(self):
        cheap, _ = scoring.score_block("value", {"ev_ebit": 5.0})    # ucuz
        rich, _ = scoring.score_block("value", {"ev_ebit": 95.0})    # pahali
        assert cheap > rich


class TestSeedList:
    def test_thirty_six_companies(self):
        assert len(SEED_TICKERS) == 36

    def test_track_split(self):
        assert len(config.SEED_TRACK_A) == 24
        assert len(config.SEED_TRACK_B) == 12

    def test_both_tracks_are_in_both_lists(self):
        for t in config.SEED_BOTH_TRACKS:
            assert t in config.SEED_TRACK_A or t in config.SEED_TRACK_B

    def test_no_duplicates_within_a_track(self):
        assert len(config.SEED_TRACK_A) == len(set(config.SEED_TRACK_A))
        assert len(config.SEED_TRACK_B) == len(set(config.SEED_TRACK_B))

    def test_prewarned_companies_are_in_seed_list(self):
        for ticker in config.SEED_PREWARNINGS:
            assert ticker in SEED_TICKERS, f"{ticker} tohum listesinde yok"

    def test_acquisition_suspects_flagged(self):
        for t in ("CPAY", "GPN", "NTAP"):
            assert t in config.SEED_FORCE_ORGANIC_SUSPECT
            assert t in config.SEED_PREWARNINGS

    def test_lyft_and_brze_have_warnings(self):
        assert "LYFT" in config.SEED_PREWARNINGS
        assert "BRZE" in config.SEED_PREWARNINGS


class TestSectors:
    def test_software_maps_to_business_services(self):
        assert sector_for_sic(7372) == "Is hizmetleri ve yazilim"

    def test_semiconductors(self):
        assert sector_for_sic(3674) == "Elektronik ve elektrikli ekipman"

    def test_financials_excluded(self):
        assert config.is_excluded_sic(6022) is True
        assert config.is_excluded_sic(6500) is True
        assert config.is_excluded_sic(7372) is False

    def test_unknown_sic_is_safe(self):
        assert sector_for_sic(None) == "Bilinmiyor"
        assert sector_for_sic("") == "Bilinmiyor"
        assert sector_for_sic("abc") == "Bilinmiyor"
        assert config.is_excluded_sic(None) is False


class TestDataFiles:
    def test_thresholds_json_matches_config(self):
        """data/thresholds.json config.py'den uretilmis olmali."""
        path = config.DATA_DIR / "thresholds.json"
        if not path.exists():
            pytest.skip("thresholds.json henuz uretilmedi")
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert set(payload["thresholds"]) == set(THRESHOLDS), \
            "thresholds.json bayat — `python scripts/init_data.py` calistir"
