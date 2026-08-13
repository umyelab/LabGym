"""AC categorizer class-mismatch contract."""

from unittest.mock import patch

import pandas as pd
import pytest

from LabGym import mywx  # noqa: F401
import wx

from LabGym.categorizer import CategorizerClassMismatchError, Categorizers


@pytest.fixture(scope='module')
def wx_app():
	app = wx.App(False)
	yield app
	wx.CallAfter(app.ExitMainLoop)
	app.MainLoop()
	del app
	wx.App._instance = None


def test_mismatch_error_lists_are_sorted_and_message_is_explicit():
	err = CategorizerClassMismatchError(['b_extra', 'a_extra'], ['missing_z', 'missing_a'])
	assert err.unrecognized_folders == ['a_extra', 'b_extra']
	assert err.missing_classes == ['missing_a', 'missing_z']
	text = str(err)
	assert 'exactly match' in text
	assert 'a_extra' in text
	assert 'missing_a' in text


def test_test_categorizer_raises_before_model_load_on_mismatch(tmp_path):
	ground = tmp_path / 'gt'
	(ground / 'walk').mkdir(parents=True)
	(ground / 'extra').mkdir(parents=True)
	model = tmp_path / 'model'
	model.mkdir(parents=True)
	pd.DataFrame(
		{
			'network': [0, None],
			'time_step': [15, None],
			'inner_code': [1, None],
			'background_free': [0, None],
			'dim_conv': [8, None],
			'level_conv': [1, None],
			'channel': [1, None],
			'classnames': ['walk', 'run'],
		}
	).to_csv(model / 'model_parameters.txt', index=False)

	ca = Categorizers()
	with patch('LabGym.categorizer.load_model') as load_model:
		with pytest.raises(CategorizerClassMismatchError) as caught:
			ca.test_categorizer(str(ground), str(model), result_path=str(tmp_path / 'out'))
		load_model.assert_not_called()
		assert 'extra' in caught.value.unrecognized_folders
		assert 'run' in caught.value.missing_classes


def test_gui_mismatch_handler_does_not_unpack_none(wx_app):
	from LabGym.gui_categorizer import PanelLv2_TestCategorizers

	with patch.object(PanelLv2_TestCategorizers, 'display_window', lambda self: None):
		with patch('LabGym.gui_categorizer.config.get_config', return_value={'models': '/tmp'}):
			frame = wx.Frame(None)
			panel = PanelLv2_TestCategorizers(frame)
			panel.file_path = '/tmp/gt'
			panel.path_to_categorizer = '/tmp/model'
			panel.out_path = None
			panel.checkbox_open_interactive = wx.CheckBox(frame)
			panel.checkbox_open_interactive.SetValue(True)

			err = CategorizerClassMismatchError(['extra'], ['missing'])
			with patch('LabGym.gui_categorizer.Categorizers') as CA:
				CA.return_value.test_categorizer.side_effect = err
				with patch('LabGym.gui_categorizer.wx.MessageBox') as mb:
					panel.test_categorizer(None)
					mb.assert_called_once()
					args, kwargs = mb.call_args
					assert args[1] == 'Class name mismatch'
					assert 'Unrecognized behavior folders' in args[0]
					assert 'Model classes absent' in args[0]
			frame.Destroy()
