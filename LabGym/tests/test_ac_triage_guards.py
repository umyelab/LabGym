"""AC triage empty-plan, PDF preflight, package wrapper, and outcome helpers."""

from unittest.mock import MagicMock, patch

import pytest

from LabGym import mywx  # noqa: F401
import wx

from LabGym.gui_categorizer import (
	reportlab_importable,
	triage_assignment_counts,
	TriageBuilderDialog,
)


@pytest.fixture(scope='module')
def wx_app():
	app = wx.App(False)
	yield app
	wx.CallAfter(app.ExitMainLoop)
	app.MainLoop()
	del app
	wx.App._instance = None


def test_triage_assignment_counts_require_at_least_one():
	assert triage_assignment_counts(0, 0, 0) is False
	assert triage_assignment_counts(1, 0, 0) is True
	assert triage_assignment_counts(0, 2, 0) is True
	assert triage_assignment_counts(0, 0, 3) is True


def test_reportlab_importable_true_in_review_env():
	ok, err = reportlab_importable()
	assert ok is True
	assert err is None


def _make_triage_dialog(wx_app, source_dataset_root=None, example_map=None):
	parent = wx.Frame(None)
	with patch.object(TriageBuilderDialog, 'init_ui', lambda self: None):
		dlg = TriageBuilderDialog(
			parent,
			confusions_list=['a -> b (1 errors)'],
			example_map=example_map or {('a', 'b'): ['/tmp/ds/a/x.avi']},
			report={'accuracy': 0.5, 'macro avg': {'f1-score': 0.5}},
			cm=[[1, 0], [0, 1]],
			classnames=['a', 'b'],
			embedding_map={},
			source_dataset_root=source_dataset_root,
		)
		dlg.lb_h1 = MagicMock()
		dlg.lb_h2 = MagicMock()
		dlg.lb_h3 = MagicMock()
		dlg.lb_h1.GetCount.return_value = 0
		dlg.lb_h2.GetCount.return_value = 0
		dlg.lb_h3.GetCount.return_value = 0
	return parent, dlg


def _src_with_classes(tmp_path, classes=('a', 'b')):
	src = tmp_path / 'test'
	for cls in classes:
		(src / cls).mkdir(parents=True)
		(src / cls / f'{cls}_only.avi').write_bytes(b'avi')
	return src


def test_empty_plan_returns_before_name_dialog_and_copytree(wx_app):
	parent, dlg = _make_triage_dialog(wx_app)
	with patch('LabGym.gui_categorizer.wx.TextEntryDialog') as name_dlg:
		with patch('LabGym.gui_categorizer.shutil.copytree') as copytree:
			with patch('LabGym.gui_categorizer.wx.MessageBox') as mb:
				dlg.on_finish(None)
				mb.assert_called_once()
				assert mb.call_args[0][1] == 'Empty triage plan'
				name_dlg.assert_not_called()
				copytree.assert_not_called()
	parent.Destroy()


def test_missing_reportlab_returns_before_clone(wx_app):
	parent, dlg = _make_triage_dialog(wx_app)
	dlg.lb_h1.GetCount.return_value = 1
	with patch('LabGym.gui_categorizer.reportlab_importable', return_value=(False, 'no module')):
		with patch('LabGym.gui_categorizer.wx.TextEntryDialog') as name_dlg:
			with patch('LabGym.gui_categorizer.shutil.copytree') as copytree:
				with patch('LabGym.gui_categorizer.wx.MessageBox') as mb:
					dlg.on_finish(None)
					assert mb.call_args[0][1] == 'Missing Dependency'
					name_dlg.assert_not_called()
					copytree.assert_not_called()
	parent.Destroy()


def test_h1_file_collision_blocks_before_makedirs(wx_app, tmp_path):
	src = _src_with_classes(tmp_path)
	(src / 'a' / 'same.avi').write_bytes(b'a')
	(src / 'b' / 'same.avi').write_bytes(b'b')
	parent, dlg = _make_triage_dialog(wx_app, source_dataset_root=str(src))
	dlg.lb_h1.GetCount.return_value = 1
	dlg.lb_h1.GetString.return_value = 'a -> b (1 errors)'

	name_dlg = MagicMock()
	name_dlg.ShowModal.return_value = wx.ID_OK
	name_dlg.GetValue.return_value = 'pkg_out'

	with patch('LabGym.gui_categorizer.reportlab_importable', return_value=(True, None)):
		with patch('LabGym.gui_categorizer.wx.TextEntryDialog', return_value=name_dlg):
			with patch('LabGym.gui_categorizer.os.makedirs') as makedirs:
				with patch('LabGym.gui_categorizer.shutil.copytree') as copytree:
					with patch('LabGym.gui_categorizer.wx.MessageBox') as mb:
						dlg.on_finish(None)
	assert mb.call_args[0][1] == 'H1 filename collision'
	makedirs.assert_not_called()
	copytree.assert_not_called()
	assert not (tmp_path / 'pkg_out').exists()
	parent.Destroy()


def test_h1_missing_class_blocks_before_mutation(wx_app, tmp_path):
	src = tmp_path / 'test'
	(src / 'a').mkdir(parents=True)
	(src / 'a' / 'x.avi').write_bytes(b'a')
	parent, dlg = _make_triage_dialog(wx_app, source_dataset_root=str(src))
	dlg.lb_h1.GetCount.return_value = 1
	dlg.lb_h1.GetString.return_value = 'a -> b (1 errors)'

	name_dlg = MagicMock()
	name_dlg.ShowModal.return_value = wx.ID_OK
	name_dlg.GetValue.return_value = 'pkg_out'

	with patch('LabGym.gui_categorizer.reportlab_importable', return_value=(True, None)):
		with patch('LabGym.gui_categorizer.wx.TextEntryDialog', return_value=name_dlg):
			with patch('LabGym.gui_categorizer.shutil.copytree') as copytree:
				with patch('LabGym.gui_categorizer.wx.MessageBox') as mb:
					dlg.on_finish(None)
	assert mb.call_args[0][1] == 'H1 class folder missing'
	copytree.assert_not_called()
	assert not (tmp_path / 'pkg_out').exists()
	parent.Destroy()


def test_invalid_package_name_creates_no_package(wx_app, tmp_path):
	src = _src_with_classes(tmp_path)
	parent, dlg = _make_triage_dialog(wx_app, source_dataset_root=str(src))
	dlg.lb_h1.GetCount.return_value = 1
	dlg.lb_h1.GetString.return_value = 'a -> b (1 errors)'

	name_dlg = MagicMock()
	name_dlg.ShowModal.return_value = wx.ID_OK
	name_dlg.GetValue.return_value = 'bad/name'

	with patch('LabGym.gui_categorizer.reportlab_importable', return_value=(True, None)):
		with patch('LabGym.gui_categorizer.wx.TextEntryDialog', return_value=name_dlg):
			with patch('LabGym.gui_categorizer.shutil.copytree') as copytree:
				with patch('LabGym.gui_categorizer.wx.MessageBox') as mb:
					dlg.on_finish(None)
	assert mb.call_args[0][1] == 'Invalid Package Name'
	copytree.assert_not_called()
	parent.Destroy()


def test_pdf_failure_after_package_suppresses_full_success(wx_app, tmp_path):
	src = _src_with_classes(tmp_path)
	parent, dlg = _make_triage_dialog(
		wx_app,
		source_dataset_root=str(src),
		example_map={('a', 'b'): [str(src / 'a' / 'a_only.avi')]},
	)
	dlg.lb_h1.GetCount.return_value = 1
	dlg.lb_h1.GetString.return_value = 'a -> b (1 errors)'

	name_dlg = MagicMock()
	name_dlg.ShowModal.return_value = wx.ID_OK
	name_dlg.GetValue.return_value = 'pkg_out'

	with patch('LabGym.gui_categorizer.reportlab_importable', return_value=(True, None)):
		with patch('LabGym.gui_categorizer.wx.TextEntryDialog', return_value=name_dlg):
			with patch.object(dlg, 'generate_pdf_report', return_value=(False, 'boom')):
				with patch('LabGym.gui_categorizer.wx.BeginBusyCursor'):
					with patch('LabGym.gui_categorizer.wx.EndBusyCursor'):
						with patch('LabGym.gui_categorizer.wx.MessageBox') as mb:
							with patch.object(dlg, '_open_folder_safely') as open_folder:
								dlg.on_finish(None)
	titles = [c[0][1] for c in mb.call_args_list]
	assert 'Partial triage outcome' in titles
	assert 'Triage Complete' not in titles
	open_folder.assert_not_called()
	pkg = tmp_path / 'pkg_out'
	assert pkg.is_dir()
	assert (pkg / 'revised_sorted_test_examples').is_dir()
	assert (pkg / 'LabGym_Diagnostics').is_dir()
	assert (src / 'a' / 'a_only.avi').exists()
	parent.Destroy()


def test_existing_destination_fails_without_overwrite(wx_app, tmp_path):
	src = _src_with_classes(tmp_path)
	parent, dlg = _make_triage_dialog(wx_app, source_dataset_root=str(src))
	dlg.lb_h1.GetCount.return_value = 1
	dlg.lb_h1.GetString.return_value = 'a -> b (1 errors)'
	existing = tmp_path / 'pkg_out'
	existing.mkdir()
	marker = existing / 'keep.txt'
	marker.write_text('safe')

	name_dlg = MagicMock()
	name_dlg.ShowModal.return_value = wx.ID_OK
	name_dlg.GetValue.return_value = 'pkg_out'

	with patch('LabGym.gui_categorizer.reportlab_importable', return_value=(True, None)):
		with patch('LabGym.gui_categorizer.wx.TextEntryDialog', return_value=name_dlg):
			with patch('LabGym.gui_categorizer.wx.BeginBusyCursor'):
				with patch('LabGym.gui_categorizer.wx.EndBusyCursor'):
					with patch('LabGym.gui_categorizer.wx.MessageBox') as mb:
						dlg.on_finish(None)
	assert marker.read_text() == 'safe'
	assert mb.call_args[0][1] == 'Package Exists'
	assert 'Triage Complete' not in [c[0][1] for c in mb.call_args_list]
	parent.Destroy()


def test_full_success_package_layout_and_opens_package_root(wx_app, tmp_path):
	src = _src_with_classes(tmp_path)
	parent, dlg = _make_triage_dialog(
		wx_app,
		source_dataset_root=str(src),
		example_map={('a', 'b'): [str(src / 'a' / 'a_only.avi')]},
	)
	dlg.lb_h1.GetCount.return_value = 1
	dlg.lb_h1.GetString.return_value = 'a -> b (1 errors)'
	dlg.lb_h2.GetCount.return_value = 0
	dlg.lb_h3.GetCount.return_value = 0

	name_dlg = MagicMock()
	name_dlg.ShowModal.return_value = wx.ID_OK
	name_dlg.GetValue.return_value = 'pkg_out'

	def fake_pdf(path, name):
		from pathlib import Path
		Path(path).write_bytes(b'%PDF')
		return True, None

	with patch('LabGym.gui_categorizer.reportlab_importable', return_value=(True, None)):
		with patch('LabGym.gui_categorizer.wx.TextEntryDialog', return_value=name_dlg):
			with patch.object(dlg, 'generate_pdf_report', side_effect=fake_pdf):
				with patch('LabGym.gui_categorizer.wx.BeginBusyCursor'):
					with patch('LabGym.gui_categorizer.wx.EndBusyCursor'):
						with patch('LabGym.gui_categorizer.wx.MessageBox') as mb:
							with patch.object(dlg, 'EndModal'):
								with patch.object(dlg, '_open_folder_safely', return_value=(True, None)) as open_folder:
									dlg.on_finish(None)

	pkg = tmp_path / 'pkg_out'
	revised = pkg / 'revised_sorted_test_examples'
	diagnostics = pkg / 'LabGym_Diagnostics'
	assert revised.is_dir()
	assert diagnostics.is_dir()
	assert not (revised / 'LabGym_Diagnostics').exists()
	assert not (revised / 'a').exists()
	assert (revised / 'b' / 'a_only.avi').exists()
	assert (revised / 'b' / 'b_only.avi').exists()
	assert (src / 'a' / 'a_only.avi').exists()
	assert list(pkg.iterdir())  # package root opened, not diagnostics alone
	open_folder.assert_called_once_with(str(pkg))
	success_msgs = [c[0][0] for c in mb.call_args_list if c[0][1] == 'Triage Complete']
	assert success_msgs
	body = success_msgs[0]
	assert str(pkg) in body
	assert str(revised) in body
	assert 'select this folder in LabGym' in body
	assert 'categorizer_diagnostics_v1.pdf' in body
	assert 'original source fixture was not modified' in body
	parent.Destroy()


def test_copy_failure_reports_partial_package(wx_app, tmp_path):
	src = _src_with_classes(tmp_path)
	parent, dlg = _make_triage_dialog(wx_app, source_dataset_root=str(src))
	dlg.lb_h1.GetCount.return_value = 1
	dlg.lb_h1.GetString.return_value = 'a -> b (1 errors)'

	name_dlg = MagicMock()
	name_dlg.ShowModal.return_value = wx.ID_OK
	name_dlg.GetValue.return_value = 'pkg_out'

	with patch('LabGym.gui_categorizer.reportlab_importable', return_value=(True, None)):
		with patch('LabGym.gui_categorizer.wx.TextEntryDialog', return_value=name_dlg):
			with patch('LabGym.gui_categorizer.shutil.copytree', side_effect=OSError('disk full')):
				with patch('LabGym.gui_categorizer.wx.BeginBusyCursor'):
					with patch('LabGym.gui_categorizer.wx.EndBusyCursor'):
						with patch('LabGym.gui_categorizer.wx.MessageBox') as mb:
							dlg.on_finish(None)
	assert (tmp_path / 'pkg_out').is_dir()
	assert mb.call_args[0][1] == 'System Error'
	assert 'partial Triage Plan package' in mb.call_args[0][0]
	assert 'Triage Complete' not in [c[0][1] for c in mb.call_args_list]
	parent.Destroy()


def test_open_failure_after_success_does_not_delete_package(wx_app, tmp_path):
	src = _src_with_classes(tmp_path)
	parent, dlg = _make_triage_dialog(wx_app, source_dataset_root=str(src))
	dlg.lb_h1.GetCount.return_value = 1
	dlg.lb_h1.GetString.return_value = 'a -> b (1 errors)'

	name_dlg = MagicMock()
	name_dlg.ShowModal.return_value = wx.ID_OK
	name_dlg.GetValue.return_value = 'pkg_out'

	def fake_pdf(path, name):
		from pathlib import Path
		Path(path).write_bytes(b'%PDF')
		return True, None

	with patch('LabGym.gui_categorizer.reportlab_importable', return_value=(True, None)):
		with patch('LabGym.gui_categorizer.wx.TextEntryDialog', return_value=name_dlg):
			with patch.object(dlg, 'generate_pdf_report', side_effect=fake_pdf):
				with patch('LabGym.gui_categorizer.wx.BeginBusyCursor'):
					with patch('LabGym.gui_categorizer.wx.EndBusyCursor'):
						with patch('LabGym.gui_categorizer.wx.MessageBox') as mb:
							with patch.object(dlg, 'EndModal'):
								with patch.object(dlg, '_open_folder_safely', return_value=(False, 'denied')):
									dlg.on_finish(None)
	titles = [c[0][1] for c in mb.call_args_list]
	assert 'Triage Complete' in titles
	assert 'Folder Open Failed' in titles
	assert (tmp_path / 'pkg_out' / 'revised_sorted_test_examples').is_dir()
	parent.Destroy()


def test_h2_does_not_create_class_or_move_examples(wx_app, tmp_path):
	src = _src_with_classes(tmp_path)
	parent, dlg = _make_triage_dialog(wx_app, source_dataset_root=str(src))
	dlg.lb_h1.GetCount.return_value = 0
	dlg.lb_h2.GetCount.return_value = 1
	dlg.lb_h2.GetString.return_value = 'a -> b (1 errors) [NEW: novel]'
	dlg.lb_h3.GetCount.return_value = 0

	name_dlg = MagicMock()
	name_dlg.ShowModal.return_value = wx.ID_OK
	name_dlg.GetValue.return_value = 'pkg_out'

	def fake_pdf(path, name):
		from pathlib import Path
		Path(path).write_bytes(b'%PDF')
		return True, None

	with patch('LabGym.gui_categorizer.reportlab_importable', return_value=(True, None)):
		with patch('LabGym.gui_categorizer.wx.TextEntryDialog', return_value=name_dlg):
			with patch.object(dlg, 'generate_pdf_report', side_effect=fake_pdf):
				with patch('LabGym.gui_categorizer.wx.BeginBusyCursor'):
					with patch('LabGym.gui_categorizer.wx.EndBusyCursor'):
						with patch('LabGym.gui_categorizer.wx.MessageBox'):
							with patch.object(dlg, 'EndModal'):
								with patch.object(dlg, '_open_folder_safely', return_value=(True, None)):
									dlg.on_finish(None)
	revised = tmp_path / 'pkg_out' / 'revised_sorted_test_examples'
	assert (revised / 'a' / 'a_only.avi').exists()
	assert (revised / 'b' / 'b_only.avi').exists()
	assert not (revised / 'novel').exists()
	parent.Destroy()


def test_h3_references_go_to_diagnostics_only(wx_app, tmp_path):
	src = _src_with_classes(tmp_path)
	avi = src / 'a' / 'a_only.avi'
	jpg = src / 'a' / 'a_only.jpg'
	jpg.write_bytes(b'jpg')
	parent, dlg = _make_triage_dialog(
		wx_app,
		source_dataset_root=str(src),
		example_map={('a', 'b'): [str(avi)]},
	)
	dlg.lb_h1.GetCount.return_value = 0
	dlg.lb_h2.GetCount.return_value = 0
	dlg.lb_h3.GetCount.return_value = 1
	dlg.lb_h3.GetString.return_value = 'a -> b (1 errors)'

	name_dlg = MagicMock()
	name_dlg.ShowModal.return_value = wx.ID_OK
	name_dlg.GetValue.return_value = 'pkg_out'

	def fake_pdf(path, name):
		from pathlib import Path
		Path(path).write_bytes(b'%PDF')
		return True, None

	with patch('LabGym.gui_categorizer.reportlab_importable', return_value=(True, None)):
		with patch('LabGym.gui_categorizer.wx.TextEntryDialog', return_value=name_dlg):
			with patch.object(dlg, 'generate_pdf_report', side_effect=fake_pdf):
				with patch('LabGym.gui_categorizer.wx.BeginBusyCursor'):
					with patch('LabGym.gui_categorizer.wx.EndBusyCursor'):
						with patch('LabGym.gui_categorizer.wx.MessageBox'):
							with patch.object(dlg, 'EndModal'):
								with patch.object(dlg, '_open_folder_safely', return_value=(True, None)):
									with patch('random.sample', side_effect=lambda seq, k: list(seq)[:k]):
										dlg.on_finish(None)
	pkg = tmp_path / 'pkg_out'
	h3 = pkg / 'LabGym_Diagnostics' / 'H3_Variance_References'
	assert h3.is_dir()
	assert list(h3.glob('*.avi'))
	assert not (pkg / 'revised_sorted_test_examples' / 'H3_Variance_References').exists()
	assert avi.exists()
	parent.Destroy()
