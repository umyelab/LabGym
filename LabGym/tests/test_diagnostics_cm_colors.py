"""Matrix correct-cell color endpoint and CM width refresh."""

import inspect
from unittest.mock import patch

import pytest

from LabGym import mywx  # noqa: F401  # must precede wx-dependent LabGym imports
import wx

from LabGym.gui_categorizer import (
	CM_CORRECT_RGB_MAX,
	CM_CORRECT_RGB_MIN,
	AutomatedDiagnosticsDialog,
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


@pytest.fixture(scope='module')
def wx_app():
	app = wx.App(False)
	yield app
	wx.CallAfter(app.ExitMainLoop)
	app.MainLoop()
	del app
	wx.App._instance = None


def _padded_100_pct_min_width(grid):
	dc = wx.ClientDC(grid)
	dc.SetFont(grid.GetDefaultCellFont())
	text_w, _text_h = dc.GetTextExtent('100.0%')
	return text_w + 16


def _make_diagnostics_dialog(wx_app, classnames, cm):
	parent = wx.Frame(None)
	report = {
		name: {
			'support': sum(cm[i]),
			'precision': 0.5,
			'recall': 0.5,
			'f1-score': 0.5,
		}
		for i, name in enumerate(classnames)
	}
	report['accuracy'] = 0.5
	report['macro avg'] = {'f1-score': 0.5, 'precision': 0.5, 'recall': 0.5}
	report['weighted avg'] = {'f1-score': 0.5, 'precision': 0.5, 'recall': 0.5}
	with patch.object(AutomatedDiagnosticsDialog, 'Maximize'):
		dlg = AutomatedDiagnosticsDialog(
			parent,
			report,
			cm,
			classnames,
			{},
			{},
			None,
		)
	return parent, dlg


def test_diagnostics_cm_raw_first_toggle_refreshes_column_widths(wx_app):
	# 198/250 == 79.2%; short labels exercise the padded floor.
	classnames = ['idle', 'a', 'walk']
	cm = [
		[198, 52, 0],
		[0, 10, 0],
		[0, 0, 10],
	]
	parent, dlg = _make_diagnostics_dialog(wx_app, classnames, cm)
	try:
		assert dlg.is_normalized is False
		assert dlg.toggle_btn.GetLabel() == 'Show Normalized (%)'
		assert dlg.cm_grid.GetCellValue(0, 0) == '198'
		helper_src = inspect.getsource(AutomatedDiagnosticsDialog.refresh_cm_column_widths)
		assert 'idle' not in helper_src

		refresh_calls = []
		original_refresh = dlg.refresh_cm_column_widths

		def tracking_refresh():
			refresh_calls.append(True)
			return original_refresh()

		dlg.refresh_cm_column_widths = tracking_refresh

		dlg.toggle_btn.SetValue(True)
		dlg.on_toggle_cm(None)

		assert dlg.is_normalized is True
		assert dlg.toggle_btn.GetLabel() == 'Show Raw Counts'
		assert dlg.cm_grid.GetCellValue(0, 0) == '79.2%'
		assert dlg.cm_grid.GetCellValue(1, 1) == '100.0%'
		assert len(refresh_calls) >= 1

		min_w = _padded_100_pct_min_width(dlg.cm_grid)
		for col in range(dlg.cm_grid.GetNumberCols()):
			assert dlg.cm_grid.GetColSize(col) >= min_w

		# Generic short label (not idle) still meets the floor after refresh.
		idle_w = dlg.cm_grid.GetColSize(0)
		short_w = dlg.cm_grid.GetColSize(1)
		assert short_w >= min_w
		assert idle_w >= min_w
	finally:
		dlg.Destroy()
		parent.Destroy()


def test_diagnostics_cm_column_width_helper_is_label_agnostic(wx_app):
	classnames = ['z', 'yy']
	cm = [[5, 0], [0, 5]]
	parent, dlg = _make_diagnostics_dialog(wx_app, classnames, cm)
	try:
		dlg.is_normalized = True
		dlg.update_grid_data()
		assert dlg.cm_grid.GetCellValue(0, 0) == '100.0%'
		min_w = _padded_100_pct_min_width(dlg.cm_grid)
		for col in range(dlg.cm_grid.GetNumberCols()):
			assert dlg.cm_grid.GetColSize(col) >= min_w
	finally:
		dlg.Destroy()
		parent.Destroy()
