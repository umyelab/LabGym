"""AC Training Module single-column structure and diagnostic copy contracts."""

from pathlib import Path

from LabGym import mywx  # noqa: F401

from LabGym.gui_categorizer import (
	AC_DIAGNOSTIC_BUTTON_LABELS,
	collect_insufficient_support_entries,
	insufficient_support_threshold,
)


APPROVED_ORDER = (
	'Generate Image Examples',
	'Annotate images with EZannot',
	'Train Detectors',
	'Test Detectors',
	'Generate Behavior Examples',
	'Sort Behavior Examples',
	'Train Categorizers',
	'Test Categorizers',
)


def test_training_module_source_has_single_column_bindings():
	src = Path(__file__).resolve().parents[2] / 'LabGym' / 'gui_main.py'
	text = src.read_text(encoding='utf-8')
	start = text.index('class PanelLv1_TrainingModule')
	end = text.index('class PanelLv1_AnalysisModule')
	body = text[start:end]
	assert 'ACTION_LABELS' not in body
	assert 'Detector Pipeline' not in body
	assert 'Categorizer Pipeline' not in body
	assert 'divider_line' not in body
	assert 'columns_sizer' not in body
	for label in APPROVED_ORDER:
		if label.startswith('Annotate'):
			assert 'Annotate images with EZannot' in body
		else:
			assert f"label='{label}'" in body
	for handler in (
		'generate_images',
		'train_detectors',
		'test_detectors',
		'generate_behaviorexamples',
		'sort_behaviorexamples',
		'train_categorizers',
		'test_categorizers',
	):
		assert f'self.{handler}' in body


def test_ac_diagnostic_labels_have_no_emoji_and_overview_first():
	assert AC_DIAGNOSTIC_BUTTON_LABELS[0] == 'Overview'
	assert AC_DIAGNOSTIC_BUTTON_LABELS == (
		'Overview',
		'Major Confusions',
		'Minor Confusions',
		'Successes',
		'Build Triage Plan',
	)
	joined = ' '.join(AC_DIAGNOSTIC_BUTTON_LABELS)
	for ch in ('🔴', '🟡', '🟢', '🔵', '📝', '⚠️', '⚠'):
		assert ch not in joined


def test_diagnostic_button_construction_uses_label_constant():
	src = Path(__file__).resolve().parents[2] / 'LabGym' / 'gui_categorizer.py'
	text = src.read_text(encoding='utf-8')
	start = text.index('def init_ui(self):')
	# Limit to AutomatedDiagnosticsDialog.init_ui (first init_ui after that class).
	class_start = text.index('class AutomatedDiagnosticsDialog')
	start = text.index('def init_ui(self):', class_start)
	end = text.index('\tdef update_grid_data', start)
	body = text[start:end]
	assert 'AC_DIAGNOSTIC_BUTTON_LABELS' in body
	assert 'label="Overview"' not in body
	assert 'label="🔴' not in body


def test_diagnostic_copy_rejects_overconfident_phrases_and_uses_new_low_support():
	src = Path(__file__).resolve().parents[2] / 'LabGym' / 'gui_categorizer.py'
	text = src.read_text(encoding='utf-8')
	banned = (
		'Model looks great!',
		'Statistically Meaningless',
		'successfully and consistently',
		'Everything looks great!',
		'Keep Tuning!',
		'<b>Diagnosis:</b>',
		'Insufficient sample support for automated interpretation',
		'⚠️',
	)
	for phrase in banned:
		assert phrase not in text, phrase
	assert 'Too few examples for automated analysis' in text
	assert ": {mc['support']} examples; " in text
	assert "at least {mc['min_support']} required" in text
	assert '(fewer than 100 examples)' in text
	assert 'Possible pattern (advisory)' in text
	assert 'H1 — Merge hypothesis (advisory)' in text
	assert 'LabGym does not create the new class or move examples' in text
	assert 'revised_sorted_test_examples' in text
	assert 'H3_Variance_References' in text
	assert 'Hypothesis 1: Merge on revised sorted test examples (advisory)' in text
	assert 'Package layout and remediation' in text
	assert 'select <b>revised_sorted_test_examples</b>, not the package root' in text
	assert 'do not copy evaluation examples into training' in text
	assert 'Triage Plan: You are reviewing confusion patterns' in text
	assert 'Build Triage Plan' in text
	assert 'scientific decisions remain yours' in text
	assert 'Open interactive results when testing finishes' not in text
	assert 'Show interactive results after testing' in text
	assert 'Triage_Action_Plan.pdf' not in text
	assert 'dataset_v2' not in text
	assert 'next_versioned_pdf_path' in text
	assert 'next_versioned_triage_package_name' in text
	assert 'sanitize_triage_package_base' in text
	assert 'validate_triage_package_name' in text
	assert 'collect_h1_filename_collisions' in text
	assert 'fit_dialog_client_size' in text
	assert 'NOMINAL_CLIENT_SIZE = (960, 720)' in text
	assert 'wx.RESIZE_BORDER' not in text.split('class TriageBuilderDialog')[1].split('def move_items')[0]
	assert 'ops_help_html' in text
	assert 'self.intro_lbl' in text
	assert '&#8594;' in text
	assert '≥' in text
	assert 'Paragraph(f"• ' in text
	assert 'LabGym Triage Action Plan' in text
	assert 'source_dataset_root' in text


def test_zero_and_positive_low_support_entries():
	report = {
		'absent': {'support': 0, 'f1-score': 0.0},
		'sparse': {'support': 5, 'f1-score': 0.2},
		'enough': {'support': 100, 'f1-score': 0.5},
	}
	classnames = ['absent', 'sparse', 'enough']
	# total support = 105; threshold = max(20, 1.05) = 20
	assert insufficient_support_threshold(105) == 20
	entries = collect_insufficient_support_entries(classnames, report)
	by_class = {e['class']: e for e in entries}
	assert 'absent' in by_class
	assert by_class['absent']['support'] == 0
	assert by_class['absent']['min_support'] == 20
	assert 'sparse' in by_class
	assert by_class['sparse']['support'] == 5
	assert by_class['sparse']['min_support'] == 20
	assert 'enough' not in by_class
