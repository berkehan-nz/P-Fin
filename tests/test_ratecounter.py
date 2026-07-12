import pytest

from pfin.data.ratecounter import RateCounter, RateLimitExceeded
from pfin.memory.schema import RateLimitState


def test_minute_limit():
    rc = RateCounter(RateLimitState(), per_minute=8, per_day=800)
    for _ in range(8):
        assert rc.can_call()
        rc.record()
    assert not rc.can_call()
    with pytest.raises(RateLimitExceeded):
        rc.record()


def test_minute_reset():
    rc = RateCounter(RateLimitState(), per_minute=2, per_day=800)
    rc.record(); rc.record()
    assert not rc.can_call()
    rc.state.minute_bucket = "2000-01-01T00:00"   # farklı dakika → sıfırlanır
    assert rc.can_call()


def test_day_limit():
    st = RateLimitState()
    rc = RateCounter(st, per_minute=1000, per_day=3)
    for _ in range(3):
        rc.record()
    assert rc.remaining_today() == 0
    with pytest.raises(RateLimitExceeded):
        rc.record()
