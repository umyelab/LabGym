"""AF regression: prepared/sorted behavior-count helpers (no live GUI)."""

import os
from pathlib import Path

from LabGym.gui_utils import (
	behavior_label_from_filename,
	count_prepared_examples,
	count_sorted_examples,
	counts_enable_diagnostics,
)


def _touch(path: Path):
	path.parent.mkdir(parents=True, exist_ok=True)
	path.write_bytes(b'')


def test_behavior_label_final_underscore_segment():
	assert behavior_label_from_filename('0_grooming.avi') == 'grooming'
	assert behavior_label_from_filename('0_approach_partner.jpg') == 'partner'
	assert behavior_label_from_filename('nounderscore.jpg') is None
	assert behavior_label_from_filename('plain.jpg') is None


def test_flat_avi_examples(tmp_path):
	_touch(tmp_path / '0_grooming.avi')
	_touch(tmp_path / '1_rearing.avi')
	_touch(tmp_path / '2_grooming.avi')
	assert count_prepared_examples(str(tmp_path)) == {
		'grooming': 2,
		'rearing': 1,
	}


def test_filenames_without_underscore_ignored(tmp_path):
	_touch(tmp_path / 'orphan.avi')
	_touch(tmp_path / '1_valid.avi')
	assert count_prepared_examples(str(tmp_path)) == {'valid': 1}


def test_avi_over_jpg_no_double_count(tmp_path):
	_touch(tmp_path / '0_grooming.avi')
	_touch(tmp_path / '0_grooming.jpg')
	_touch(tmp_path / '1_grooming.jpg')
	# Any AVI present in the directory: count only AVI, not JPG.
	assert count_prepared_examples(str(tmp_path)) == {'grooming': 1}


def test_jpg_only_when_no_avi(tmp_path):
	_touch(tmp_path / '0_grooming.jpg')
	_touch(tmp_path / '1_rearing.jpg')
	assert count_prepared_examples(str(tmp_path)) == {
		'grooming': 1,
		'rearing': 1,
	}


def test_train_validation_aggregation(tmp_path):
	_touch(tmp_path / 'train' / '0_a.avi')
	_touch(tmp_path / 'train' / '1_b.avi')
	_touch(tmp_path / 'validation' / '2_a.avi')
	_touch(tmp_path / 'validation' / '3_c.avi')
	assert count_prepared_examples(str(tmp_path)) == {'a': 2, 'b': 1, 'c': 1}


def test_train_vadilation_compatibility(tmp_path):
	_touch(tmp_path / 'train' / '0_x.avi')
	_touch(tmp_path / 'vadilation' / '1_x.avi')
	_touch(tmp_path / 'vadilation' / '2_y.avi')
	assert count_prepared_examples(str(tmp_path)) == {'x': 2, 'y': 1}


def test_incomplete_split_falls_back_to_flat_root(tmp_path):
	# train/ only — not split mode; flat-root scan ignores nested files.
	_touch(tmp_path / 'train' / '0_hidden.avi')
	_touch(tmp_path / '0_root.avi')
	assert count_prepared_examples(str(tmp_path)) == {'root': 1}


def test_empty_and_unreadable(tmp_path):
	assert count_prepared_examples(str(tmp_path)) == {}
	assert count_prepared_examples(str(tmp_path / 'missing')) == {}
	assert count_prepared_examples('') == {}
	assert counts_enable_diagnostics({}) is False


def test_one_populated_category_enables_diagnostics(tmp_path):
	_touch(tmp_path / '0_only.avi')
	counts = count_prepared_examples(str(tmp_path))
	assert counts == {'only': 1}
	assert counts_enable_diagnostics(counts) is True


def test_sorted_multiple_folders_and_empty_zero(tmp_path):
	_touch(tmp_path / 'grooming' / 'a.avi')
	_touch(tmp_path / 'grooming' / 'b.avi')
	_touch(tmp_path / 'rearing' / 'c.jpg')
	(tmp_path / 'empty_behavior').mkdir()
	counts = count_sorted_examples(str(tmp_path))
	assert counts == {'grooming': 2, 'rearing': 1, 'empty_behavior': 0}
	assert counts_enable_diagnostics(counts) is True


def test_sorted_per_folder_avi_jpg_precedence(tmp_path):
	_touch(tmp_path / 'mixed' / '0.avi')
	_touch(tmp_path / 'mixed' / '0.jpg')
	_touch(tmp_path / 'mixed' / '1.jpg')
	_touch(tmp_path / 'jpg_only' / 'x.jpg')
	counts = count_sorted_examples(str(tmp_path))
	assert counts['mixed'] == 1  # avis only
	assert counts['jpg_only'] == 1


def test_sorted_unreadable_root(tmp_path):
	assert count_sorted_examples(str(tmp_path / 'nope')) == {}
