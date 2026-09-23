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
    # interim() huni gunlugunu ve aday dosyasini DATA_DIR'e yazar; yamalanmazsa
    # testler gercek data/funnel_log.json'u kirletir.
    from src import pipeline
    monkeypatch.setattr(pipeline, "DATA_DIR", tmp_path)
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
        assert {k: p[k] for k in ("cycle", "done", "total", "pct",
                                  "remaining", "survivors")} == {
            "cycle": 2, "done": 50, "total": 200, "pct": 25.0,
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


class TestCycleProtection:
    """Haftalik kosu her pazar --new-cycle cagiriyordu. Bir tur 5-10 gun
    surdugu icin (GitHub zamanlanmis kosulari saatte bir degil, gunde 6-7
    kez tetikliyor) tur her seferinde sifirlaniyor ve SONUC HIC URETILMIYORDU.
    """

    def test_cycle_in_progress_detection(self):
        s = scan.empty_state()
        assert scan.cycle_in_progress(s) is False          # kuyruk yok
        s.update({"queue": ["A", "B", "C"], "cursor": 1})
        assert scan.cycle_in_progress(s) is True
        s["cursor"] = 3
        assert scan.cycle_in_progress(s) is False          # bitmis

    def test_new_cycle_refused_while_in_progress(self, isolated, monkeypatch):
        from src import pipeline
        monkeypatch.setattr(pipeline, "load_company", lambda t, **kw: None)
        monkeypatch.setattr(pipeline, "benchmarks", lambda: {"QQQ": []})

        state = scan.empty_state()
        state.update({"cycle": 1, "queue": ["A"] * 100, "cursor": 40,
                      "batch_size": 10})
        scan.save_state(state)

        out = scan.run(new_cycle=True, build_cards=False)
        assert out["cycle"] == 1, "yarim tur cope atilmamaliydi"
        assert out["cursor"] >= 40, "imlec geri sarmamaliydi"

    def test_force_allows_reset(self, isolated, monkeypatch):
        from src import pipeline
        monkeypatch.setattr(pipeline, "load_company", lambda t, **kw: None)
        monkeypatch.setattr(pipeline, "benchmarks", lambda: {"QQQ": []})

        state = scan.empty_state()
        state.update({"cycle": 1, "queue": ["A"] * 100, "cursor": 40})
        scan.save_state(state)

        out = scan.run(new_cycle=True, force=True, tickers=["X", "Y"],
                       batch_size=1, build_cards=False)
        assert out["cycle"] == 2

    def test_one_off_batch_does_not_persist(self, isolated, monkeypatch):
        """weekly --batch 60 kalici olarak parti boyutunu yariya
        indiriyordu ve sonraki tum kosular yavasliyordu."""
        from src import pipeline
        monkeypatch.setattr(pipeline, "load_company", lambda t, **kw: None)
        monkeypatch.setattr(pipeline, "benchmarks", lambda: {"QQQ": []})

        state = scan.empty_state()
        state.update({"cycle": 1, "queue": ["A"] * 500, "cursor": 0,
                      "batch_size": 120})
        scan.save_state(state)

        out = scan.run(batch_size=20, build_cards=False)
        assert out["batch_size"] == 120, "kayitli parti boyutu degismemeliydi"
        assert out["cursor"] == 20, "bu kosuda 20 islenmeliydi"


class TestInterimResults:
    """Tur 5-10 gun surerken kullanici hicbir yeni sirket gormemeliydi.
    Biriken hayatta kalanlar uzerinden gecici siralama uretilir."""

    def _seed_survivors(self, n):
        import json
        rows = []
        for i in range(n):
            r = row_for("KVYO")
            r["ticker"] = f"T{i:03d}"
            r["metrics"] = dict(r["metrics"])
            r["metrics"]["ev_gross_profit"] = 3.0 + i * 0.1
            r["own_pct"] = {}
            snap = scan.to_snapshot(r)
            snap["ticker"] = r["ticker"]
            scan.survivor_path(r["ticker"]).write_text(
                json.dumps(snap), encoding="utf-8")
            rows.append(r)
        return rows

    def test_below_threshold_produces_nothing(self, isolated):
        self._seed_survivors(5)
        state = scan.empty_state()
        state.update({"queue": ["A"] * 100, "cursor": 10})
        assert scan.interim(state, build_cards=False) is None

    def test_above_threshold_ranks_survivors(self, isolated, monkeypatch):
        from src import pipeline
        captured = {}
        monkeypatch.setattr(pipeline, "refresh_candidates_from_disk",
                            lambda partial=None: captured.update(partial or {}))
        self._seed_survivors(20)
        state = scan.empty_state()
        state.update({"cycle": 1, "queue": ["A"] * 100, "cursor": 25})

        out = scan.interim(state, build_cards=False)
        assert out is not None
        assert captured["is_partial"] is True
        assert captured["scanned"] == 25
        assert captured["survivors"] == 20

    def test_partial_flag_reaches_candidates_file(self, tmp_path, monkeypatch):
        """Pano 'bu liste gecici' diyebilmek icin bayragi gormeli."""
        from src import pipeline
        monkeypatch.setattr(pipeline, "CARDS_DIR", tmp_path / "cards")
        (tmp_path / "cards").mkdir()
        monkeypatch.setattr(pipeline, "DATA_DIR", tmp_path)
        written = {}
        monkeypatch.setattr(pipeline, "write_json",
                            lambda path, payload, **kw: written.update(payload) or True)
        pipeline.write_candidates([], [], [], partial={"is_partial": True, "pct": 12.5})
        assert written["partial"]["is_partial"] is True


class TestHangProtection:
    """22 Eylul 2026 kilitlenmesi — tek sirket tum partiyi durdurmasin.

    Borsadan cikmis bir sembolde yfinance sonsuza kadar asildi. Parti
    50 dakikalik is akisi sinirina carpti, "Commit" adimi atlandi ve
    imlec 1920'de dondu; her saat ayni yere takildi. Uc savunma:
    sirket basina zaman siniri, parti sure butcesi, tekrar eden
    sembolu atlama. Ucu de ILERLEME ASLA DURMAZ ilkesine hizmet eder.
    """

    def test_hanging_company_does_not_stall_batch(self, isolated, monkeypatch):
        import time as _t

        from src import config, pipeline

        monkeypatch.setattr(config, "COMPANY_TIMEOUT_SEC", 1)

        def maybe_hang(ticker, **kw):
            if ticker == "HANG":
                _t.sleep(30)          # bekci devreye girmezse test kilitlenir
            f = fixtures.ALL["DBX"]()
            f.avg_dollar_volume_30d = 50e6
            return f

        monkeypatch.setattr(pipeline, "load_company", maybe_hang)

        state = scan.start_cycle(scan.empty_state(),
                                 tickers=["DBX", "HANG", "LSCC"])
        started = _t.monotonic()
        state = scan.run_batch(state, size=3)

        assert _t.monotonic() - started < 10      # 30 sn beklemedi
        assert state["cursor"] == 3               # kuyruk sonuna kadar ilerledi
        assert state["timeouts"]["HANG"] == 1
        assert "HANG" in state["failed"]

    def test_repeated_timeouts_skip_the_symbol(self, isolated, monkeypatch):
        from src import config, pipeline

        calls = []

        def counted(ticker, **kw):
            calls.append(ticker)
            raise AssertionError("bu sembol hic denenmemeliydi")

        monkeypatch.setattr(pipeline, "load_company", counted)
        monkeypatch.setattr(config, "COMPANY_TIMEOUT_SKIP_AFTER", 2)

        state = scan.start_cycle(scan.empty_state(), tickers=["BAD"])
        state["timeouts"] = {"BAD": 2}
        state = scan.run_batch(state, size=1)

        assert calls == []                # hic denenmedi
        assert state["cursor"] == 1       # yine de ilerledi

    def test_deadline_ends_batch_cleanly(self, isolated, monkeypatch):
        import time as _t

        from src import pipeline

        def quick(ticker, **kw):
            f = fixtures.ALL["DBX"]()
            f.avg_dollar_volume_30d = 50e6
            return f

        monkeypatch.setattr(pipeline, "load_company", quick)

        state = scan.start_cycle(scan.empty_state(),
                                 tickers=[f"T{i}" for i in range(20)])
        # Butce ZATEN dolmus: tek sirket bile islenmeden duzgun donmeli
        state = scan.run_batch(state, size=20, deadline=_t.monotonic() - 1)

        assert state["cursor"] == 0
        assert state["processed"] == 0

    def test_cursor_is_saved_after_every_company(self, isolated, monkeypatch):
        """Surec parti ortasinda olurse diskteki imlec o ana kadar ilerlemis olmali."""
        from src import config, pipeline

        monkeypatch.setattr(config, "STATE_FLUSH_EVERY", 1)

        seen = []

        def quick(ticker, **kw):
            # Her sirketten sonra diskteki duruma bak
            on_disk = json.loads(scan.STATE_PATH.read_text()) \
                if scan.STATE_PATH.exists() else {"cursor": 0}
            seen.append(on_disk.get("cursor", 0))
            f = fixtures.ALL["DBX"]()
            f.avg_dollar_volume_30d = 50e6
            return f

        monkeypatch.setattr(pipeline, "load_company", quick)

        state = scan.start_cycle(scan.empty_state(), tickers=["A", "B", "C"])
        scan.run_batch(state, size=3)

        # 1. sirkette disk bos (0), 2.'de 1, 3.'te 2 olmali
        assert seen == [0, 1, 2]
        assert json.loads(scan.STATE_PATH.read_text())["cursor"] == 3


class TestStallDetection:
    """Duraklama GORUNUR olmali.

    22 Eylul 2026'da tarama iki gun boyunca ayni sirkette takildi ve
    hicbir yerde "en son ne zaman ilerledi" yazmadigi icin fark edilmedi.
    """

    def _state(self, hours_ago, *, cursor=10, total=100):
        from datetime import datetime, timedelta, timezone

        st = scan.empty_state()
        st["queue"] = [f"T{i}" for i in range(total)]
        st["cursor"] = cursor
        if hours_ago is not None:
            stamp = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
            st["last_batch_at"] = stamp.isoformat()
        return st

    def test_fresh_batch_is_not_stalled(self):
        p = scan.progress(self._state(0.5))
        assert p["stalled"] is False
        assert p["idle_hours"] < 1

    def test_old_batch_is_stalled(self):
        p = scan.progress(self._state(33))
        assert p["stalled"] is True
        assert p["idle_hours"] > 32

    def test_finished_cycle_is_never_stalled(self):
        """Kuyruk bittiyse beklemek normaldir; alarm verme."""
        p = scan.progress(self._state(48, cursor=100, total=100))
        assert p["stalled"] is False

    def test_missing_timestamp_is_not_an_alarm(self):
        p = scan.progress(self._state(None))
        assert p["idle_hours"] is None
        assert p["stalled"] is False

    def test_naive_timestamp_is_treated_as_utc(self):
        from datetime import datetime, timedelta, timezone

        st = self._state(1)
        naive = (datetime.now(timezone.utc) - timedelta(hours=5)).replace(tzinfo=None)
        st["last_batch_at"] = naive.isoformat()
        p = scan.progress(st)
        assert 4.5 < p["idle_hours"] < 5.5


class TestCorruptState:
    """Bozuk durum dosyasi SESSIZCE turu sifirlamamali."""

    def test_missing_file_is_a_fresh_start(self, isolated):
        assert scan.load_state()["cursor"] == 0

    def test_corrupt_file_raises_instead_of_resetting(self, isolated):
        # 1920 sirketlik ilerlemeyi sessizce cope atmak yerine dur.
        scan.STATE_PATH.write_text('{"cursor": 1920, "queue": ["A", "B"', encoding="utf-8")
        with pytest.raises(scan.CorruptStateError):
            scan.load_state()

    def test_valid_file_loads_normally(self, isolated):
        state = scan.empty_state()
        state.update({"cursor": 5, "queue": ["A"] * 10})
        scan.save_state(state)
        assert scan.load_state()["cursor"] == 5


class TestBatchSizeCeiling:
    """Parti boyutu bir TAVAN; gercek sinirlayici sure butcesi.

    GitHub saatlik cron'u bu repoda 3-5 saatte bir tetikliyor. Durum
    dosyasinda kalmis eski 120 degeri, kosu basina isi gereksiz kisitliyordu.
    """

    def test_legacy_stored_value_does_not_throttle(self, isolated, monkeypatch):
        seen = {}

        def spy(state, *, size=None, **kw):
            seen["size"] = size
            state["cursor"] = len(state["queue"])
            return state

        monkeypatch.setattr(scan, "run_batch", spy)
        monkeypatch.setattr(scan, "interim", lambda *a, **k: None)
        monkeypatch.setattr(scan, "write_survivors_index", lambda: False)
        monkeypatch.setattr(scan, "finalize", lambda st, **k: st)
        from src import pipeline
        monkeypatch.setattr(pipeline, "benchmarks", lambda: {})
        # context() FINRA/Finnhub'a gider; testte ag beklemesin.
        monkeypatch.setattr(pipeline, "context", lambda *a, **k: {})
        monkeypatch.setattr(scan, "start_cycle",
                            lambda st, **k: dict(st, queue=["A"], cursor=0))

        state = scan.empty_state()
        state.update({"queue": ["A"] * 50, "batch_size": scan.LEGACY_BATCH_SIZE})
        scan.save_state(state)
        scan.run(build_cards=False)

        assert seen["size"] == scan.DEFAULT_BATCH_SIZE

    def test_explicit_batch_still_wins(self, isolated, monkeypatch):
        seen = {}

        def spy(state, *, size=None, **kw):
            seen["size"] = size
            state["cursor"] = len(state["queue"])
            return state

        monkeypatch.setattr(scan, "run_batch", spy)
        monkeypatch.setattr(scan, "interim", lambda *a, **k: None)
        monkeypatch.setattr(scan, "write_survivors_index", lambda: False)
        monkeypatch.setattr(scan, "finalize", lambda st, **k: st)
        from src import pipeline
        monkeypatch.setattr(pipeline, "benchmarks", lambda: {})
        # context() FINRA/Finnhub'a gider; testte ag beklemesin.
        monkeypatch.setattr(pipeline, "context", lambda *a, **k: {})
        monkeypatch.setattr(scan, "start_cycle",
                            lambda st, **k: dict(st, queue=["A"], cursor=0))

        state = scan.empty_state()
        state.update({"queue": ["A"] * 50})
        scan.save_state(state)
        scan.run(batch_size=25, build_cards=False)

        assert seen["size"] == 25      # kullanici acikca istedi, saygi goster

    def test_deliberate_stored_value_is_respected(self, isolated, monkeypatch):
        """Goc YALNIZCA eski varsayilani (120) yukseltir.

        Bilincli konmus bir deger (ornegin --batch 10 --new-cycle ile
        kaydedilmis) aynen korunmali; yoksa kullanicinin karari sessizce
        eziliyor demektir.
        """
        seen = {}

        def spy(state, *, size=None, **kw):
            seen["size"] = size
            return state

        monkeypatch.setattr(scan, "run_batch", spy)
        monkeypatch.setattr(scan, "interim", lambda *a, **k: None)
        monkeypatch.setattr(scan, "write_survivors_index", lambda: False)
        from src import pipeline
        monkeypatch.setattr(pipeline, "benchmarks", lambda: {})
        monkeypatch.setattr(pipeline, "context", lambda *a, **k: {})

        state = scan.empty_state()
        state.update({"queue": ["A"] * 500, "cursor": 0, "batch_size": 10})
        scan.save_state(state)
        scan.run(build_cards=False)

        assert seen["size"] == 10
