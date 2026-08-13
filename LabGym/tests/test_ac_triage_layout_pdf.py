"""Pure helpers for Triage Builder sizing, PDF allocation, and package naming."""

from pathlib import Path

from LabGym import mywx  # noqa: F401

from LabGym.gui_categorizer import (
	fit_dialog_client_size,
	next_versioned_pdf_path,
)


def test_fit_dialog_preserves_nominal_on_large_work_area():
	assert fit_dialog_client_size(960, 720, 1920, 1080) == (960, 720)


def test_fit_dialog_clamps_to_margin_and_max_frac():
	w, h = fit_dialog_client_size(960, 720, 1000, 700, margin=40, max_frac=0.92)
	assert w == min(960, 1000 - 80, int(1000 * 0.92))
	assert h == min(720, 700 - 80, int(700 * 0.92))
	assert w <= int(1000 * 0.92)
	assert h <= int(700 * 0.92)
	assert w <= 1000 - 80
	assert h <= 700 - 80


def test_fit_dialog_returns_positive_integers_on_tiny_work_area():
	w, h = fit_dialog_client_size(960, 720, 50, 40, margin=40, max_frac=0.92)
	assert isinstance(w, int) and isinstance(h, int)
	assert w >= 1 and h >= 1
	assert w <= 50 and h <= 40


def test_next_versioned_pdf_empty_directory_is_v1(tmp_path):
	path = next_versioned_pdf_path(str(tmp_path))
	assert path == str(tmp_path / 'categorizer_diagnostics_v1.pdf')


def test_next_versioned_pdf_increments_from_existing_v1(tmp_path):
	(tmp_path / 'categorizer_diagnostics_v1.pdf').write_bytes(b'pdf')
	path = next_versioned_pdf_path(str(tmp_path))
	assert path.endswith('categorizer_diagnostics_v2.pdf')
	assert not Path(path).exists()


def test_next_versioned_pdf_uses_max_plus_one_and_skips_gaps(tmp_path):
	(tmp_path / 'categorizer_diagnostics_v1.pdf').write_bytes(b'a')
	(tmp_path / 'categorizer_diagnostics_v3.pdf').write_bytes(b'b')
	path = next_versioned_pdf_path(str(tmp_path))
	assert path.endswith('categorizer_diagnostics_v4.pdf')


def test_next_versioned_pdf_ignores_unrelated_and_case_mismatches(tmp_path):
	(tmp_path / 'categorizer_diagnostics.pdf').write_bytes(b'x')
	(tmp_path / 'categorizer_diagnostics_notes.pdf').write_bytes(b'x')
	(tmp_path / 'categorizer_diagnostics_vx.pdf').write_bytes(b'x')
	(tmp_path / 'Categorizer_diagnostics_v1.pdf').write_bytes(b'x')
	(tmp_path / 'categorizer_diagnostics_v1').mkdir()
	path = next_versioned_pdf_path(str(tmp_path))
	assert path.endswith('categorizer_diagnostics_v1.pdf')


def test_next_versioned_pdf_does_not_overwrite_existing(tmp_path):
	existing = tmp_path / 'categorizer_diagnostics_v1.pdf'
	existing.write_bytes(b'keep')
	path = Path(next_versioned_pdf_path(str(tmp_path)))
	assert path != existing
	assert existing.read_bytes() == b'keep'
	assert path.parent == tmp_path


def test_triage_builder_source_is_fixed_and_anchored():
	src = Path(__file__).resolve().parents[2] / 'LabGym' / 'gui_categorizer.py'
	text = src.read_text()
	start = text.index('class TriageBuilderDialog')
	body = text[start:text.index('def move_items', start)]
	assert 'wx.RESIZE_BORDER' not in body
	assert 'NOMINAL_CLIENT_SIZE = (960, 720)' in body
	assert 'fit_dialog_client_size' in body
	assert 'self.intro_lbl' in body
	assert 'ops_help_html' in body
	assert 'Finish and Generate Report' in body
	assert 'wx.ID_CANCEL' in body
	assert 'scientific decisions remain yours.' in body
	ops_page_start = body.index('self.ops_help_html.SetPage')
	assert 'scientific decisions remain yours' not in body[ops_page_start:]
	assert 'next_versioned_pdf_path(diagnostics_dir)' in text
	assert 'revised_sorted_test_examples' in text
	assert 'source_dataset_root' in text
	assert 'dataset_v2' not in text
	assert 'Triage_Action_Plan.pdf' not in text
	assert 'LabGym Triage Action Plan' in text
