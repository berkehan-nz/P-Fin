"""prices.py — fiyat kaynaklari ISTEGE BAGLIDIR ve partiyi bekletmemeli."""

import pytest

from src import config
from src.sources import prices
from src.util import FetchError


@pytest.fixture(autouse=True)
def fresh_breakers():
    """Devre kesiciler modul duzeyinde; testler birbirini kirletmesin."""
    prices.STOOQ_BREAKER.reset()
    prices.YF_BREAKER.reset()
    yield
    prices.STOOQ_BREAKER.reset()
    prices.YF_BREAKER.reset()


class TestRetryPolicy:
    def test_price_retries_are_far_shorter_than_sec(self):
        """SEC tek dogru kaynak oldugu icin sabirli; fiyat oyle degil."""
        assert config.PRICE_MAX_RETRIES < config.HTTP_MAX_RETRIES
        assert config.PRICE_TIMEOUT_SEC < config.HTTP_TIMEOUT_SEC

    def test_stooq_uses_the_impatient_policy(self, monkeypatch):
        seen = {}

        def fake_get(url, **kw):
            seen.update(kw)
            raise FetchError("kapali")

        monkeypatch.setattr(prices, "http_get", fake_get)
        with pytest.raises(FetchError):
            prices.from_stooq("AAA")

        assert seen["timeout"] == config.PRICE_TIMEOUT_SEC
        assert seen["max_retries"] == config.PRICE_MAX_RETRIES


class TestBreakerIntegration:
    def test_dead_stooq_is_dropped_after_threshold(self, monkeypatch, tmp_path):
        monkeypatch.setattr(prices, "CACHE_DIR", tmp_path)
        monkeypatch.setattr(prices, "from_yfinance", lambda t: None)

        calls = []

        def dead(ticker):
            calls.append(ticker)
            raise FetchError("stooq kapali")

        monkeypatch.setattr(prices, "from_stooq", dead)

        limit = config.SOURCE_BREAKER_THRESHOLD
        for i in range(limit + 25):
            prices.history(f"T{i}", allow_cache=False)

        # Esige kadar denendi, sonrasinda HIC denenmedi
        assert len(calls) == limit
        assert not prices.STOOQ_BREAKER.ok()

    def test_missing_symbol_does_not_open_the_breaker(self, monkeypatch, tmp_path):
        """'Bu sembol yok' gecerli bir yanittir — kaynak saglikli."""
        monkeypatch.setattr(prices, "CACHE_DIR", tmp_path)
        monkeypatch.setattr(prices, "from_stooq", lambda t: None)
        monkeypatch.setattr(prices, "from_yfinance", lambda t: None)

        for i in range(config.SOURCE_BREAKER_THRESHOLD + 5):
            prices.history(f"T{i}", allow_cache=False)

        assert prices.STOOQ_BREAKER.ok()

    def test_working_source_is_never_dropped(self, monkeypatch, tmp_path):
        monkeypatch.setattr(prices, "CACHE_DIR", tmp_path)
        rows = [{"date": f"2026-01-{d:02d}", "close": 10.0, "high": 11.0,
                 "low": 9.0, "volume": 1000.0} for d in range(1, 26)]
        monkeypatch.setattr(prices, "from_stooq", lambda t: rows)

        for i in range(config.SOURCE_BREAKER_THRESHOLD + 5):
            out = prices.history(f"T{i}", allow_cache=False)
            assert out

        assert prices.STOOQ_BREAKER.ok()
