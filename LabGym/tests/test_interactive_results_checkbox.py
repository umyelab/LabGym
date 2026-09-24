"""Interactive-results checkbox on Test Categorizers."""

from unittest.mock import patch

import pytest

from LabGym import mywx  # noqa: F401
import wx


@pytest.fixture(scope='module')
def wx_app():
	app = wx.App(False)
	yield app
	wx.CallAfter(app.ExitMainLoop)
	app.MainLoop()
	del app
	wx.App._instance = None


def _make_test_panel(wx_app, display=True):
	from LabGym.gui_categorizer import PanelLv2_TestCategorizers

	frame = wx.Frame(None)
	if display:
		with patch('LabGym.gui_categorizer.config.get_config', return_value={'models': '/tmp'}):
			panel = PanelLv2_TestCategorizers(frame)
	else:
		with patch.object(PanelLv2_TestCategorizers, 'display_window', lambda self: None):
			with patch('LabGym.gui_categorizer.config.get_config', return_value={'models': '/tmp'}):
				panel = PanelLv2_TestCategorizers(frame)
				panel.checkbox_open_interactive = wx.CheckBox(
					frame,
					label='Show interactive results after testing',
				)
				panel.checkbox_open_interactive.SetValue(True)
	return frame, panel


def test_checkbox_exists_with_exact_label_and_defaults_checked(wx_app):
	frame, panel = _make_test_panel(wx_app, display=True)
	assert panel.checkbox_open_interactive.GetLabel() == (
		'Show interactive results after testing'
	)
	assert panel.checkbox_open_interactive.GetValue() is True
	frame.Destroy()


def test_checked_path_opens_diagnostics_dialog(wx_app):
	frame, panel = _make_test_panel(wx_app, display=False)
	panel.file_path = '/tmp/gt'
	panel.path_to_categorizer = '/tmp/model'
	panel.out_path = None
	panel.checkbox_open_interactive.SetValue(True)

	fake_report = {
		'walk': {'support': 10, 'f1-score': 0.9},
		'accuracy': 0.9,
		'macro avg': {},
		'weighted avg': {},
	}
	with patch('LabGym.gui_categorizer.Categorizers') as CA:
		CA.return_value.test_categorizer.return_value = (
			fake_report,
			[[1]],
			{},
			{},
		)
		with patch('LabGym.gui_categorizer.AutomatedDiagnosticsDialog') as Dialog:
			instance = Dialog.return_value
			with patch('LabGym.gui_categorizer.wx.MessageBox') as mb:
				panel.test_categorizer(None)
				Dialog.assert_called_once()
				instance.ShowModal.assert_called_once()
				instance.Destroy.assert_called_once()
				mb.assert_not_called()
	frame.Destroy()


def test_unchecked_path_skips_dialog_and_passes_export_path(wx_app):
	frame, panel = _make_test_panel(wx_app, display=False)
	panel.file_path = '/tmp/gt'
	panel.path_to_categorizer = '/tmp/model'
	panel.out_path = '/tmp/export'
	panel.checkbox_open_interactive.SetValue(False)

	fake_report = {
		'walk': {'support': 10, 'f1-score': 0.9},
		'accuracy': 0.9,
		'macro avg': {},
		'weighted avg': {},
	}
	with patch('LabGym.gui_categorizer.Categorizers') as CA:
		CA.return_value.test_categorizer.return_value = (
			fake_report,
			[[1]],
			{},
			{},
		)
		with patch('LabGym.gui_categorizer.AutomatedDiagnosticsDialog') as Dialog:
			with patch('LabGym.gui_categorizer.wx.MessageBox') as mb:
				panel.test_categorizer(None)
				CA.return_value.test_categorizer.assert_called_once_with(
					'/tmp/gt',
					'/tmp/model',
					result_path='/tmp/export',
				)
				Dialog.assert_not_called()
				mb.assert_not_called()
	assert panel.checkbox_open_interactive.GetValue() is False
	frame.Destroy()


def test_unchecked_without_export_passes_none_result_path(wx_app):
	frame, panel = _make_test_panel(wx_app, display=False)
	panel.file_path = '/tmp/gt'
	panel.path_to_categorizer = '/tmp/model'
	panel.out_path = None
	panel.checkbox_open_interactive.SetValue(False)

	fake_report = {
		'walk': {'support': 10, 'f1-score': 0.9},
		'accuracy': 0.9,
		'macro avg': {},
		'weighted avg': {},
	}
	with patch('LabGym.gui_categorizer.Categorizers') as CA:
		CA.return_value.test_categorizer.return_value = (
			fake_report,
			[[1]],
			{},
			{},
		)
		with patch('LabGym.gui_categorizer.AutomatedDiagnosticsDialog') as Dialog:
			with patch('LabGym.gui_categorizer.wx.MessageBox') as mb:
				panel.test_categorizer(None)
				CA.return_value.test_categorizer.assert_called_once_with(
					'/tmp/gt',
					'/tmp/model',
					result_path=None,
				)
				Dialog.assert_not_called()
				mb.assert_not_called()
	frame.Destroy()
