"""AC matrix correct-cell color endpoint and ordering."""

from LabGym import mywx  # noqa: F401  # must precede wx-dependent LabGym imports

from LabGym.gui_categorizer import (
	CM_CORRECT_RGB_MAX,
	CM_CORRECT_RGB_MIN,
	cm_correct_cell_rgb,
)


def _srgb_channel_to_linear(c):
	c = c / 255.0
	if c <= 0.04045:
		return c / 12.92
	return ((c + 0.055) / 1.055) ** 2.4


def relative_luminance(rgb):
	r, g, b = rgb
	return (
		0.2126 * _srgb_channel_to_linear(r)
		+ 0.7152 * _srgb_channel_to_linear(g)
		+ 0.0722 * _srgb_channel_to_linear(b)
	)


def contrast_ratio(fg_rgb, bg_rgb):
	l1 = relative_luminance(fg_rgb)
	l2 = relative_luminance(bg_rgb)
	lighter = max(l1, l2)
	darker = min(l1, l2)
	return (lighter + 0.05) / (darker + 0.05)


def test_cm_correct_max_endpoint_is_approved_green():
	assert CM_CORRECT_RGB_MAX == (46, 125, 50)
	assert cm_correct_cell_rgb(1.0) == (46, 125, 50)


def test_cm_correct_min_endpoint_is_darker():
	lo = cm_correct_cell_rgb(0.0)
	hi = cm_correct_cell_rgb(1.0)
	assert lo == CM_CORRECT_RGB_MIN
	assert sum(lo) < sum(hi)


def test_cm_correct_scale_is_monotonic_in_green():
	prev_g = -1
	for step in range(0, 11):
		r, g, b = cm_correct_cell_rgb(step / 10)
		assert g >= prev_g
		prev_g = g
		assert 0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255


def test_white_text_contrast_at_max_green():
	"""Approved max green must meet WCAG AA contrast for white text (>= 4.5:1)."""
	rgb = cm_correct_cell_rgb(1.0)
	assert rgb == (46, 125, 50)
	ratio = contrast_ratio((255, 255, 255), rgb)
	assert ratio >= 4.5
	assert abs(ratio - 5.13) < 0.05
