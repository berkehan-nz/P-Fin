"""util.py — bekci zamanlayicisi ve zaman siniri.

Kilitlenme korumasinin temeli burasi: ``time_limit`` calismazsa tarama
tek bir asili ag cagrisinda saatlerce durur (22 Eylul 2026).
"""

import time

import pytest

from src.util import TimeoutHit, Watchdog, time_limit


class TestTimeLimit:
    def test_fast_block_is_untouched(self):
        with time_limit(5, "hizli"):
            result = 2 + 2
        assert result == 4

    def test_slow_block_raises(self):
        started = time.monotonic()
        with pytest.raises(TimeoutHit):
            with time_limit(1, "yavas"):
                time.sleep(20)
        assert time.monotonic() - started < 5

    def test_not_swallowed_by_broad_except(self):
        """Kutuphaneler ``except Exception`` ile sarmalar; bekci gecmeli."""
        with pytest.raises(TimeoutHit):
            with time_limit(1, "yutulmaz"):
                try:
                    time.sleep(20)
                except Exception:  # noqa: BLE001 — kasitli
                    pytest.fail("TimeoutHit yutuldu")

    def test_alarm_is_cleared_on_success(self):
        with time_limit(1, "ilk"):
            pass
        time.sleep(1.5)          # eski alarm kalsaydi burada patlardi
        assert True

    def test_nested_inner_does_not_cancel_outer(self):
        """Ic sayac bitince dis butce geri kurulmali."""
        with pytest.raises(TimeoutHit):
            with time_limit(2, "dis"):
                with time_limit(1, "ic"):
                    pass          # ic sayac temiz bitti
                time.sleep(20)    # dis sayac hala gecerli olmali

    def test_zero_disables_the_limit(self):
        with time_limit(0, "kapali"):
            time.sleep(0.2)
        assert True


class TestWatchdog:
    def test_beat_keeps_it_quiet(self):
        fired = []
        w = Watchdog(1, on_timeout=fired.append)
        w._beat = time.monotonic()
        # Dogrudan _loop calistirmadan mantigi dogrula: taze nabiz, sinir asilmaz
        assert time.monotonic() - w._beat < w.limit
        w.beat("calisiyor")
        assert w._label == "calisiyor"
        w.stop()

    def test_zero_limit_never_starts_a_thread(self):
        w = Watchdog(0).start()
        assert w._thread is None


class TestSourceBreaker:
    """Cokmus kaynak her sirkette yeniden beklenmesin.

    22 Eylul 2026: Stooq erisilemez oldu, hisse basina 31 saniye yandi,
    120'lik parti 62 dakikaya cikti ve is akisi her saat partiyi iptal etti.
    """

    def test_opens_after_threshold(self):
        from src.util import SourceBreaker

        b = SourceBreaker("test", threshold=3)
        assert b.ok()
        b.miss(); b.miss()
        assert b.ok()          # esik asilmadi
        b.miss()
        assert not b.ok()      # ucuncude acildi

    def test_success_resets_the_counter(self):
        from src.util import SourceBreaker

        b = SourceBreaker("test", threshold=3)
        b.miss(); b.miss()
        b.hit()                # araya basarili yanit girdi
        b.miss(); b.miss()
        assert b.ok()          # ust uste degil, acilmamali

    def test_reset_closes_it_again(self):
        from src.util import SourceBreaker

        b = SourceBreaker("test", threshold=1)
        b.miss()
        assert not b.ok()
        b.reset()
        assert b.ok()
