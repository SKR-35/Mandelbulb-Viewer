import math

import pytest

from mandelbulb_viewer.core import distance_estimate, estimate


def test_origin():
    assert estimate(0, 0, 0) == (0.0, 20, False)


def test_immediate_escape():
    assert estimate(5, 0, 0) == pytest.approx((2.5 * math.log(5), 0, True))


def test_one_update_on_positive_z_axis():
    # Power 2, c=(0,0,2): z becomes 6, derivative becomes 5.
    distance, updates, escaped = estimate(0, 0, 2, power=2, max_iterations=1)
    assert escaped
    assert updates == 1
    assert distance == pytest.approx(0.5 * 6 * math.log(6) / 5)


def test_non_escape_at_iteration_limit():
    assert estimate(0, 0, 0.1, max_iterations=1) == (0.0, 1, False)


@pytest.mark.parametrize("point", [(1, 0, 0), (0, 0, -1), (0.7, -0.4, 0.9), (0, 0, 1e-12)])
@pytest.mark.parametrize("power", [2.0, 3.5, 8.0, 16.0])
def test_finite_nonnegative_distance(point, power):
    distance, updates, escaped = estimate(*point, power=power)
    assert math.isfinite(distance)
    assert distance >= 0
    assert 0 <= updates <= 20
    assert escaped == (distance > 0)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"power": 1},
        {"power": 17},
        {"power": math.nan},
        {"max_iterations": 0},
        {"max_iterations": 1.5},
        {"max_iterations": True},
        {"max_iterations": 257},
        {"bailout": 1},
        {"bailout": math.inf},
    ],
)
def test_invalid_parameters(kwargs):
    with pytest.raises(ValueError):
        estimate(0, 0, 0, **kwargs)


@pytest.mark.parametrize("x", [math.nan, math.inf, -math.inf, 1e7])
def test_invalid_coordinates(x):
    with pytest.raises(ValueError):
        estimate(x, 0, 0)


def test_distance_wrapper():
    assert distance_estimate(2, 1, 0) == estimate(2, 1, 0)[0]
