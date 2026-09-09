"""scan.py — kademeli tarama: durum, parti, anlik goruntu, tur sonu."""

import json

import pytest

from src import funnel, scan
from tests import fixtures


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    """Gercek data/ klasorune dokunmadan calis."""
    monkeypatch.setattr(scan, "STATE_PATH", tmp_path / "scan_state.json")
    monkeypatch.setattr(scan, "SURVIVOR_DIR", tmp_path / "survivors")
    (tmp_path / "survivors").mkdir()
    return tmp_path


def row_for(name):
    r = funnel.evaluate(fixtures.ALL[name]())
    r["avg_dollar_volume_30d"] = 50e6
    return r


class TestState:
    def test_empty_state_shape(self):
        s = scan.empty_state()
        assert s["cycle"] == 0 and s["cursor"] == 0
        assert s["queue"] == []
        assert set(s["stage_counts"]) == {"0", "1", "2"}

    def test_load_returns_empty_when_missing(self, isolated):
        assert scan.load_state()["cycle"] == 0

    def test_save_and_load_roundtrip(self, isolated):
        s = scan.empty_state()
        s["queue"] = ["AAA", "BBB"]
        s["cycle"] = 3
        scan.save_state(s)
        assert scan.load_state()["cycle"] == 3
        assert scan.load_state()["queue"] == ["AAA", "BBB"]

    def test_progress_math(self):
        s = scan.empty_state()
        s.update({"queue": ["A"] * 200, "cursor": 50, "survivor_count": 7, "cycle": 2})
        p = scan.progress(s)
        assert p == {"cycle": 2, "done": 50, "total": 200, "pct": 25.0,
                     "remaining": 150, "survivors": 7}

    def test_progress_handles_empty_queue(self):
        assert scan.progress(scan.empty_state())["pct"] == 0.0


class TestCycle:
    def test_start_cycle_increments_and_fills_queue(self, isolated):
        s = scan.start_cycle(scan.empty_state(), tickers=["AAA", "BBB", "CCC"])
        assert s["cycle"] == 1
        assert s["queue"] == ["AAA", "BBB", "CCC"]
        assert s["cursor"] == 0

    def test_new_cycle_clears_old_survivors(self, isolated):
        scan.survivor_path("ZZZZ").write_text('{"ticker":"ZZZZ"}', encoding="utf-8")
        assert scan.survivor_path("ZZZZ").exists()
        scan.start_cycle(scan.empty_state(), tickers=["AAA"])
        assert not scan.survivor_path("ZZZZ").exists()

    def test_keep_survivors_option(self, isolated):
        scan.survivor_path("ZZZZ").write_text('{"ticker":"ZZZZ"}', encoding="utf-8")
        scan.start_cycle(scan.empty_state(), tickers=["AAA"], keep_survivors=True)
        assert scan.survivor_path("ZZZZ").exists()


class TestSnapshot:
    def test_roundtrip_preserves_funnel_inputs(self):
        row = row_for("KVYO")
        row["own_pct"] = {"ev_sales": 30.0}
        snap = scan.to_snapshot(row)
        back = scan.from_snapshot(snap)

        assert back["ticker"] == "KVYO"
        assert back["sector"] == row["sector"]
        assert back["metrics"]["rule_of_40"] == pytest.approx(row["metrics"]["rule_of_40"])
        assert back["own_pct"]["ev_sales"] == 30.0
        assert back["track"] == row.get("track") or back["track"] in ("A", "B")

    def test_snapshot_is_json_serializable(self):
        """Diske yazilacak; Fundamentals nesnesi tasimamali."""
        snap = scan.to_snapshot(row_for("DBX"))
        text = json.dumps(snap, ensure_ascii=False)
        assert "fundamentals" not in snap
        assert len(text) > 200

    def test_snapshot_keeps_annuals_for_stage2(self):
        """Asama 2'nin nakit donusumu ve dusus testleri yillik veri ister."""
        snap = scan.to_snapshot(row_for("DBX"))
        assert len(snap["annuals"]) == 2
        assert snap["annuals"][-1]["cfo"] == 880.0
        assert snap["annuals"][-1]["net_income"] == 490.0

    def test_restored_row_supports_stage3(self):
        rows = [scan.from_snapshot(scan.to_snapshot(row_for(n)))
                for n in ("DBX", "LSCC", "KVYO")]
        from src import percentiles
        table = percentiles.build_sector_table(rows)
        # cokmemeli; sebep dondurse de olur
        for r in rows:
            result = funnel.stage3(r, r["track"], table)
            assert result is None or isinstance(result, str)

    def test_snapshot_is_small(self):
        """Ham companyfacts (2-20 MB) saklanmamali."""
        snap = scan.to_snapshot(row_for("DBX"))
        assert len(json.dumps(snap)) < 20_000


class TestEarlyStages:
    def test_survivor_passes_all_three(self):
        row = row_for("KVYO")
        row["metrics"]["share_count_change_1y"] = 1.0   # seyrelme esigini gec
        row["metrics"]["sbc_to_fcf"] = 0.5
        counts = scan.empty_state()["stage_counts"]
        stage, reason = scan._run_early_stages(row, counts)
        assert stage is None and reason is None
        assert row["passed_stages"] == [0, 1, 2]
        assert counts["2"]["out"] == 1

    def test_kill_at_stage1_records_reason(self):
        row = row_for("DBX")     # hasilati daraliyor
        counts = scan.empty_state()["stage_counts"]
        stage, reason = scan._run_early_stages(row, counts)
        assert stage == 1
        assert "Hasilat buyumesi" in reason
        assert counts["0"]["out"] == 1
        assert counts["1"]["out"] == 0

    def test_kill_at_stage0(self):
        row = row_for("DBX")
        row["sic"] = 6022
        counts = scan.empty_state()["stage_counts"]
        stage, reason = scan._run_early_stages(row, counts)
        assert stage == 0
        assert counts["0"]["out"] == 0


class TestBatch:
    def test_batch_advances_cursor_and_writes_survivors(self, isolated, monkeypatch):
        universe = ["KVYO", "DBX", "LSCC"]

        def fake_load(ticker, **kw):
            key = {"KVYO": "KVYO", "DBX": "DBX", "LSCC": "LSCC"}[ticker]
            f = fixtures.ALL[key]()
            f.avg_dollar_volume_30d = 50e6
            # KVYO'yu seyrelme esiginden gecir ki hayatta kalan olsun
            if key == "KVYO":
                f.annuals[-1].shares_diluted = 264
            return f

        from src import pipeline
        monkeypatch.setattr(pipeline, "load_company", fake_load)

        state = scan.start_cycle(scan.empty_state(), tickers=universe)
        state = scan.run_batch(state, size=2)

        assert state["cursor"] == 2
        assert state["processed"] == 2
        assert state["stage_counts"]["0"]["in"] == 2

        state = scan.run_batch(state, size=2)
        assert state["cursor"] == 3          # kuyruk bitti
        assert state["processed"] == 3

    def test_batch_on_empty_queue_is_noop(self, isolated):
        state = scan.start_cycle(scan.empty_state(), tickers=[])
        out = scan.run_batch(state, size=10)
        assert out["cursor"] == 0

    def test_failed_load_is_recorded_not_fatal(self, isolated, monkeypatch):
        from src import pipeline
        monkeypatch.setattr(pipeline, "load_company", lambda t, **kw: None)
        state = scan.start_cycle(scan.empty_state(), tickers=["AAA", "BBB"])
        state = scan.run_batch(state, size=2)
        assert state["failed"] == ["AAA", "BBB"]
        assert state["cursor"] == 2


class TestFinalize:
    def test_finalize_without_survivors_is_safe(self, isolated):
        state = scan.start_cycle(scan.empty_state(), tickers=["AAA"])
        out = scan.finalize(state, build_cards=False)
        assert out["last_finalized"]

    def test_finalize_runs_stages_3_and_4(self, isolated, monkeypatch):
        rows = []
        for name in ("DBX", "LSCC", "KVYO"):
            r = row_for(name)
            r["own_pct"] = {}
            rows.append(r)
        for r in rows:
            scan.survivor_path(r["ticker"]).write_text(
                json.dumps(scan.to_snapshot(r)), encoding="utf-8")

        state = scan.start_cycle(scan.empty_state(), tickers=["X"],
                                 keep_survivors=True)
        state["stage_counts"] = {"0": {"in": 100, "out": 60},
                                 "1": {"in": 60, "out": 10},
                                 "2": {"in": 10, "out": 3}}
        state["kill_counts"] = {"Brut marj dusuk": 40}

        # data/ yazimlarini engelle
        from src import pipeline
        for fn in ("write_thresholds", "write_universe", "append_funnel_log",
                   "refresh_candidates_from_disk"):
            monkeypatch.setattr(pipeline, fn, lambda *a, **k: False)

        out = scan.finalize(state, build_cards=False)
        stages = [s["stage"] for s in out["last_log"]["stages"]]
        assert stages == [0, 1, 2, 3, 4]
        assert out["last_log"]["kill_reasons"] == {"Brut marj dusuk": 40}


class TestDurability:
    def _patch_pipeline(self, monkeypatch):
        from src import pipeline
        monkeypatch.setattr(pipeline, "load_company", lambda t, **kw: fixtures.dbx())
        monkeypatch.setattr(pipeline, "benchmarks", lambda: {"QQQ": []})
        monkeypatch.setattr(pipeline, "context", lambda t: {"earnings": {}, "shorts": {}})
        for fn in ("write_thresholds", "write_universe", "append_funnel_log",
                   "refresh_candidates_from_disk"):
            monkeypatch.setattr(pipeline, fn, lambda *a, **k: False)
        return pipeline

    def test_finalize_survives_failure_to_build_next_queue(self, isolated, monkeypatch):
        """Yeni kuyruk kurulurken ag koparsa biten tur kaybolmamali.

        Tur sonu saatlerce suren isin sonucudur; ondan sonraki
        universe_tickers() cagrisi cokerse o is cope gitmemeli.
        """
        pipeline = self._patch_pipeline(monkeypatch)

        def boom(*a, **kw):
            raise RuntimeError("SEC erisilemedi")
        monkeypatch.setattr(pipeline, "universe_tickers", boom)

        # Kuyrugu hazir bir tur kur; bu partide bitecek
        state = scan.empty_state()
        state.update({"cycle": 1, "queue": ["DBX"], "cursor": 0})
        scan.save_state(state)

        out = scan.run(batch_size=5, build_cards=False)   # tickers=None -> boom

        assert out["last_finalized"], "tur sonu isaretlenmedi"
        assert out["queue"] == [], "bos kuyruk beklenirdi"
        # diskteki durum da tur sonunu tasimali
        assert scan.load_state()["last_finalized"] == out["last_finalized"]

    def test_next_run_rebuilds_queue_after_failure(self, isolated, monkeypatch):
        """Kuyruk bos kaldiysa sonraki kosu yeni tur kurmali."""
        self._patch_pipeline(monkeypatch)

        state = scan.empty_state()
        state.update({"cycle": 1, "queue": [], "cursor": 0,
                      "last_finalized": "2026-09-09"})
        scan.save_state(state)

        out = scan.run(batch_size=1, tickers=["AAA", "BBB"], build_cards=False)
        assert out["queue"] == ["AAA", "BBB"]
        assert out["cycle"] == 2, "tur sayaci ilerlemeliydi"
        assert out["cursor"] == 1, "bir sirket islenmeliydi"
