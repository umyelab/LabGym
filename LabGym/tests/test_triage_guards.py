"""Triage empty-plan, PDF preflight, package wrapper, and outcome helpers."""

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


# --- CI #38: deferred analyzer imports ---

_ANALYZER_MSG = (
	'LabGym could not load the analysis components required for this Generate '
	'Examples workflow. Verify that the LabGym environment and its required '
	'dependencies are installed correctly, then try again.'
)
_ANALYZER_TITLE = 'Analysis dependency unavailable'


def test_gui_categorizer_import_does_not_load_analyzer_detector_stack():
	"""Fresh interpreter: importing gui_categorizer must not newly load analyzer stack."""
	import os
	import subprocess
	import sys
	from pathlib import Path

	script = (
		"import sys\n"
		"before = set(sys.modules)\n"
		"import LabGym.gui_categorizer  # noqa: F401\n"
		"after = set(sys.modules)\n"
		"newly = after - before\n"
		"forbidden = {\n"
		"    'LabGym.analyzebehavior',\n"
		"    'LabGym.analyzebehavior_dt',\n"
		"    'LabGym.detector',\n"
		"    'LabGym.detectron2.model_zoo',\n"
		"    'torch',\n"
		"}\n"
		"hit = sorted(name for name in forbidden if name in newly)\n"
		"if hit:\n"
		"    raise SystemExit('unexpected newly loaded: ' + ','.join(hit))\n"
		"print('ok')\n"
	)
	env = dict(os.environ)
	env['PYTHONDONTWRITEBYTECODE'] = '1'
	repo = str(Path(__file__).resolve().parents[2])
	proc = subprocess.run(
		[sys.executable, '-c', script],
		capture_output=True,
		text=True,
		env=env,
		cwd=repo,
	)
	assert proc.returncode == 0, proc.stdout + '\n' + proc.stderr
	assert 'ok' in proc.stdout


def _analyzer_module_keys():
	return (
		'LabGym.analyzebehavior',
		'LabGym.analyzebehavior_dt',
	)


def _stash_analyzer_modules():
	import sys
	import LabGym

	stashed = {k: sys.modules.get(k) for k in _analyzer_module_keys()}
	attrs = {
		'analyzebehavior': getattr(LabGym, 'analyzebehavior', _MISSING),
		'analyzebehavior_dt': getattr(LabGym, 'analyzebehavior_dt', _MISSING),
	}
	return stashed, attrs


_MISSING = object()


def _restore_analyzer_modules(stashed, attrs):
	import sys
	import LabGym

	for k, v in stashed.items():
		if v is None and k not in sys.modules:
			continue
		if v is None:
			sys.modules.pop(k, None)
		else:
			sys.modules[k] = v
	for name, val in attrs.items():
		if val is _MISSING:
			if hasattr(LabGym, name):
				delattr(LabGym, name)
		else:
			setattr(LabGym, name, val)


def _install_fake_analyzer(module_name, class_name, cls):
	import sys
	import types
	import LabGym

	mod = types.ModuleType(module_name)
	setattr(mod, class_name, cls)
	sys.modules[module_name] = mod
	short = module_name.rsplit('.', 1)[-1]
	setattr(LabGym, short, mod)
	return mod


def _install_bomb_analyzer(module_name):
	"""Module that fails loudly if imported for from-import of analyzer classes."""
	import sys
	import types
	import LabGym

	class Bomb(types.ModuleType):
		def __getattr__(self, name):
			raise AssertionError(f'unexpected attribute {module_name}.{name}')

	mod = Bomb(module_name)
	sys.modules[module_name] = mod
	short = module_name.rsplit('.', 1)[-1]
	setattr(LabGym, short, mod)
	return mod


def _raise_on_analyzer_import(exc):
	"""Make relative analyzer imports raise ImportError or OSError."""
	import builtins

	orig = builtins.__import__

	def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
		if level > 0 and name in ('analyzebehavior', 'analyzebehavior_dt'):
			raise exc
		if name in ('LabGym.analyzebehavior', 'LabGym.analyzebehavior_dt'):
			raise exc
		return orig(name, globals, locals, fromlist, level)

	return patch('builtins.__import__', side_effect=fake_import)


def test_import_generate_examples_analyzer_import_error_shows_messagebox_once():
	from LabGym.gui_categorizer import import_generate_examples_analyzer

	with _raise_on_analyzer_import(ImportError('simulated missing analyzer')):
		with patch('LabGym.gui_categorizer.logger') as log:
			with patch('LabGym.gui_categorizer.wx.MessageBox') as mb:
				result = import_generate_examples_analyzer('animal')
	assert result is None
	assert mb.call_count == 1
	assert mb.call_args[0][0] == _ANALYZER_MSG
	assert mb.call_args[0][1] == _ANALYZER_TITLE
	assert log.exception.called


def test_import_generate_examples_analyzer_oserror_shows_messagebox():
	from LabGym.gui_categorizer import import_generate_examples_analyzer

	with _raise_on_analyzer_import(OSError('simulated native library failure')):
		with patch('LabGym.gui_categorizer.logger') as log:
			with patch('LabGym.gui_categorizer.wx.MessageBox') as mb:
				result = import_generate_examples_analyzer('detector')
	assert result is None
	assert mb.call_count == 1
	assert mb.call_args[0][0] == _ANALYZER_MSG
	assert mb.call_args[0][1] == _ANALYZER_TITLE
	assert log.exception.called


def test_import_generate_examples_analyzer_invalid_kind_raises():
	"""Unknown kind must fail loudly without importing analyzers or showing UI."""
	import builtins

	from LabGym.gui_categorizer import import_generate_examples_analyzer

	seen = []
	orig_import = builtins.__import__

	def spy_import(name, globals=None, locals=None, fromlist=(), level=0):
		if level > 0 and name in ('analyzebehavior', 'analyzebehavior_dt'):
			seen.append(name)
		if name in ('LabGym.analyzebehavior', 'LabGym.analyzebehavior_dt'):
			seen.append(name)
		return orig_import(name, globals, locals, fromlist, level)

	with patch('builtins.__import__', side_effect=spy_import):
		with patch('LabGym.gui_categorizer.logger') as log:
			with patch('LabGym.gui_categorizer.wx.MessageBox') as mb:
				with pytest.raises(ValueError, match='animal.*detector'):
					import_generate_examples_analyzer('not-a-valid-kind')
	assert seen == []
	assert mb.call_count == 0
	assert not log.exception.called


def _make_generate_panel(wx_app):
	from LabGym.gui_categorizer import PanelLv2_GenerateExamples

	parent = wx.Frame(None)
	with patch.object(PanelLv2_GenerateExamples, 'display_window', lambda self: None):
		with patch(
			'LabGym.gui_categorizer.config.get_config',
			return_value={'detectors': '/tmp', 'models': '/tmp'},
		):
			panel = PanelLv2_GenerateExamples(parent)
	panel.path_to_videos = ['/tmp/v.avi']
	panel.result_path = '/tmp/out'
	panel.behavior_mode = 0
	panel.use_detector = False
	panel.path_to_detector = '/tmp/det'
	panel.animal_kinds = ['a']
	panel.animal_number = 1
	panel.framewidth = None
	panel.detection_threshold = 0.5
	panel.background_free = True
	panel.black_background = True
	panel.include_bodyparts = False
	panel.std = 0
	panel.delta = 1.2
	panel.stable_illumination = True
	panel.background_path = None
	panel.autofind_t = False
	panel.t = 0
	panel.duration = 0
	panel.ex_start = 0
	panel.ex_end = None
	panel.length = 15
	panel.animal_vs_bg = 1
	panel.skip_redundant = 0
	panel.social_distance = 0
	panel.decode_animalnumber = False
	panel.decode_t = False
	panel.decode_extraction = False
	panel.color_costar = False
	return parent, panel


def _patch_generate_dialogs():
	def factory(*a, **k):
		d = MagicMock()
		d.ShowModal.return_value = wx.ID_YES
		d.GetValue.return_value = 0
		d.Destroy = MagicMock()
		return d

	return (
		patch('LabGym.gui_categorizer.wx.MessageDialog', side_effect=factory),
		patch('LabGym.gui_categorizer.wx.NumberEntryDialog', side_effect=factory),
	)


def test_generate_data_background_branch_imports_animal_only(wx_app):
	"""Background path imports AnalyzeAnimal from a test-scoped fake; detector stays unused."""
	from LabGym.gui_categorizer import import_generate_examples_analyzer

	parent, panel = _make_generate_panel(wx_app)
	panel.use_detector = False
	panel.behavior_mode = 0
	constructed = []

	class FakeAnimal:
		def __init__(self):
			constructed.append('animal')

		def prepare_analysis(self, *a, **k):
			pass

		def generate_data(self, **k):
			pass

		def generate_data_interact_basic(self, **k):
			pass

	stashed, attrs = _stash_analyzer_modules()
	md, nd = _patch_generate_dialogs()
	try:
		_install_fake_analyzer('LabGym.analyzebehavior', 'AnalyzeAnimal', FakeAnimal)
		_install_bomb_analyzer('LabGym.analyzebehavior_dt')
		with md, nd:
			with patch('LabGym.gui_categorizer.wx.MessageBox') as mb:
				# Prove helper returns the real symbol from the fake module.
				cls = import_generate_examples_analyzer('animal')
				assert cls is FakeAnimal
				panel.generate_data(None)
		assert constructed == ['animal']
		assert mb.call_count == 0
	finally:
		_restore_analyzer_modules(stashed, attrs)
	parent.Destroy()


def test_generate_data_video_detector_branch_imports_detector_only(wx_app):
	parent, panel = _make_generate_panel(wx_app)
	panel.use_detector = True
	panel.behavior_mode = 0
	constructed = []

	class FakeDet:
		def __init__(self):
			constructed.append('detector')

		def prepare_analysis(self, *a, **k):
			pass

		def generate_data(self, **k):
			pass

		def generate_data_interact_basic(self, **k):
			pass

		def generate_data_interact_advance(self, **k):
			pass

	stashed, attrs = _stash_analyzer_modules()
	md, nd = _patch_generate_dialogs()
	try:
		_install_bomb_analyzer('LabGym.analyzebehavior')
		_install_fake_analyzer('LabGym.analyzebehavior_dt', 'AnalyzeAnimalDetector', FakeDet)
		with md, nd:
			panel.generate_data(None)
		assert constructed == ['detector']
	finally:
		_restore_analyzer_modules(stashed, attrs)
	parent.Destroy()


def test_generate_data_static_detector_branch_imports_detector(wx_app):
	parent, panel = _make_generate_panel(wx_app)
	panel.behavior_mode = 3
	panel.path_to_detector = '/tmp/det'
	constructed = []

	class FakeDet:
		def __init__(self):
			constructed.append('detector')

		def analyze_images_individuals(self, *a, **k):
			pass

	stashed, attrs = _stash_analyzer_modules()
	md, nd = _patch_generate_dialogs()
	try:
		_install_bomb_analyzer('LabGym.analyzebehavior')
		_install_fake_analyzer('LabGym.analyzebehavior_dt', 'AnalyzeAnimalDetector', FakeDet)
		with md, nd:
			panel.generate_data(None)
		assert constructed == ['detector']
	finally:
		_restore_analyzer_modules(stashed, attrs)
	parent.Destroy()


def test_generate_data_import_failure_returns_without_construct_or_repeat(wx_app):
	parent, panel = _make_generate_panel(wx_app)
	panel.use_detector = False
	panel.path_to_videos = ['/tmp/a.avi', '/tmp/b.avi']
	constructed = []

	md, nd = _patch_generate_dialogs()
	with md, nd:
		with _raise_on_analyzer_import(ImportError('simulated missing analyzer')):
			with patch('LabGym.gui_categorizer.logger') as log:
				with patch('LabGym.gui_categorizer.wx.MessageBox') as mb:
					panel.generate_data(None)
	assert constructed == []
	assert mb.call_count == 1
	assert mb.call_args[0][0] == _ANALYZER_MSG
	assert mb.call_args[0][1] == _ANALYZER_TITLE
	assert log.exception.called
	parent.Destroy()


def test_pyproject_declares_reportlab_min_5():
	from pathlib import Path

	text = (Path(__file__).resolve().parents[2] / 'pyproject.toml').read_text(encoding='utf-8')
	assert "'reportlab>=5.0.0'" in text
	assert text.count('reportlab') == 1


def test_gui_categorizer_has_no_module_level_analyzer_imports():
	from pathlib import Path
	import re

	text = (Path(__file__).resolve().parents[2] / 'LabGym' / 'gui_categorizer.py').read_text(encoding='utf-8')
	# Imports before the deferred-import helper are module-level.
	head = text.split('def import_generate_examples_analyzer', 1)[0]
	assert 'from .analyzebehavior import AnalyzeAnimal' not in head
	assert 'from .analyzebehavior_dt import AnalyzeAnimalDetector' not in head
	# Helper performs both imports; Generate Examples has three call sites.
	assert text.count("import_generate_examples_analyzer('detector')") == 2
	assert text.count("import_generate_examples_analyzer('animal')") == 1
	assert len(re.findall(r'from \.analyzebehavior(?:_dt)? import ', text)) == 2
