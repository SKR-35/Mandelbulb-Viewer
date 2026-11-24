import numpy as np
import pytest

from mandelbulb_viewer.palettes import DEFAULT_PALETTE, ORDER, PALETTES, colorize


def test_default_palette():
    assert DEFAULT_PALETTE == "Yikique"
    values = np.array([[0.25, 0.75]])
    np.testing.assert_array_equal(colorize(values), colorize(values, "Yikique"))


def test_palette_catalogue():
    assert len(ORDER) == len(set(ORDER)) == 18
    assert tuple(PALETTES) == ORDER
    assert ORDER[-1] == "Geoz"


@pytest.mark.parametrize("palette", ORDER)
def test_colorize_endpoints(palette):
    result = colorize(np.array([[0.0, 1.0]]), palette)
    assert result.shape == (1, 2, 3)
    assert result.dtype == np.uint8
    np.testing.assert_array_equal(result[0], [PALETTES[palette][0], PALETTES[palette][-1]])


@pytest.mark.parametrize("gamma", [0, -1, np.nan, np.inf])
def test_invalid_gamma(gamma):
    with pytest.raises(ValueError):
        colorize(np.zeros((1, 1)), gamma=gamma)


def test_invalid_palette():
    with pytest.raises(ValueError):
        colorize(np.zeros((1, 1)), "unknown")


@pytest.mark.parametrize("values", [np.zeros(3), np.array([[np.nan]])])
def test_invalid_values(values):
    with pytest.raises(ValueError):
        colorize(values)
