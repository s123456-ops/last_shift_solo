import pytest

from core.gauge import Gauge


def test_new_gauge_is_full():
    gauge = Gauge(capacity=50)
    assert gauge.value == 50
    assert gauge.ratio == 1


def test_drain_never_goes_below_zero():
    gauge = Gauge(capacity=50)
    gauge.drain(80)
    assert gauge.value == 0
    assert gauge.is_empty


def test_fill_never_exceeds_capacity():
    gauge = Gauge(capacity=50)
    gauge.drain(10)
    gauge.fill(30)
    assert gauge.value == 50


def test_ratio_reflects_value():
    gauge = Gauge(capacity=50)
    gauge.drain(10)
    assert gauge.ratio == 0.8


def test_invalid_capacity_raises():
    with pytest.raises(ValueError):
        Gauge(capacity=0)
