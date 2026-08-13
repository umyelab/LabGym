"""Pure helpers for Triage Plan package naming and H1 collision preflight."""

from pathlib import Path

from LabGym import mywx  # noqa: F401

from LabGym.gui_categorizer import (
	collect_h1_filename_collisions,
	next_versioned_triage_package_name,
	sanitize_triage_package_base,
	validate_triage_package_name,
)


def test_sanitize_source_test_becomes_test():
	assert sanitize_triage_package_base('test') == 'test'


def test_sanitize_strips_existing_trailing_triage_version():
	assert sanitize_triage_package_base('test_triage_v3') == 'test'
	assert sanitize_triage_package_base('demo_triage_v12') == 'demo'


def test_sanitize_spaces_punctuation_and_collapses_underscores():
	assert sanitize_triage_package_base('my test!!set') == 'my_test_set'
	assert sanitize_triage_package_base('a___b') == 'a_b'
	assert sanitize_triage_package_base('a/b\\c:d*e') == 'a_b_c_d_e'


def test_sanitize_preserves_unicode_letters_and_digits():
	assert sanitize_triage_package_base('données_αβ_42') == 'données_αβ_42'


def test_sanitize_empty_falls_back():
	assert sanitize_triage_package_base('!!!') == 'sorted_test_examples'
	assert sanitize_triage_package_base('   ') == 'sorted_test_examples'


def test_sanitize_truncates_to_eighty_before_suffix():
	long_name = 'x' * 100
	base = sanitize_triage_package_base(long_name)
	assert len(base) == 80
	assert base == 'x' * 80


def test_sanitize_windows_reserved_appends_data():
	assert sanitize_triage_package_base('CON') == 'CON_data'
	assert sanitize_triage_package_base('com1') == 'com1_data'
	assert sanitize_triage_package_base('LPT9') == 'LPT9_data'


def test_next_version_empty_parent_is_v1(tmp_path):
	src = tmp_path / 'test'
	src.mkdir()
	assert next_versioned_triage_package_name(str(tmp_path), 'test') == 'test_triage_v1'


def test_next_version_increments_from_existing_v1(tmp_path):
	(tmp_path / 'test_triage_v1').mkdir()
	assert next_versioned_triage_package_name(str(tmp_path), 'test') == 'test_triage_v2'


def test_next_version_uses_max_plus_one_skips_gaps(tmp_path):
	(tmp_path / 'test_triage_v1').mkdir()
	(tmp_path / 'test_triage_v3').mkdir()
	assert next_versioned_triage_package_name(str(tmp_path), 'test') == 'test_triage_v4'


def test_next_version_ignores_files_and_malformed_prefixes(tmp_path):
	(tmp_path / 'test_triage_v1.txt').write_text('file')
	(tmp_path / 'test_triage_vX').mkdir()
	(tmp_path / 'test_triage').mkdir()
	(tmp_path / 'other_triage_v1').mkdir()
	(tmp_path / 'Test_triage_v1').mkdir()
	assert next_versioned_triage_package_name(str(tmp_path), 'test') == 'test_triage_v1'


def test_next_version_does_not_create_or_overwrite(tmp_path):
	existing = tmp_path / 'test_triage_v1'
	existing.mkdir()
	marker = existing / 'keep.txt'
	marker.write_text('safe')
	name = next_versioned_triage_package_name(str(tmp_path), 'test')
	assert name == 'test_triage_v2'
	assert marker.read_text() == 'safe'
	assert not (tmp_path / name).exists()


def test_validate_rejects_invalid_user_names(tmp_path):
	cases = [
		'',
		'   ',
		'.',
		'..',
		'/abs/path',
		'has/slash',
		'has\\slash',
		'bad:name',
		'trail.',
		'CON',
		'con.txt',
		'NUL',
	]
	for name in cases:
		ok, err = validate_triage_package_name(name)
		assert ok is False, name
		assert err


def test_validate_accepts_simple_basename():
	ok, err = validate_triage_package_name('test_triage_v1')
	assert ok is True
	assert err is None


def test_h1_collision_none(tmp_path):
	src = tmp_path / 'src'
	(src / 'a').mkdir(parents=True)
	(src / 'b').mkdir()
	(src / 'a' / 'x.avi').write_bytes(b'a')
	(src / 'b' / 'y.avi').write_bytes(b'b')
	collisions, missing = collect_h1_filename_collisions(str(src), [('a', 'b')])
	assert collisions == []
	assert missing == []


def test_h1_file_collision_collected(tmp_path):
	src = tmp_path / 'src'
	(src / 'a').mkdir(parents=True)
	(src / 'b').mkdir()
	(src / 'a' / 'same.avi').write_bytes(b'a')
	(src / 'b' / 'same.avi').write_bytes(b'b')
	collisions, missing = collect_h1_filename_collisions(str(src), [('a', 'b')])
	assert missing == []
	assert len(collisions) == 1
	assert collisions[0]['pair'] == ('a', 'b')
	assert collisions[0]['filenames'] == ['same.avi']


def test_h1_directory_collision_collected(tmp_path):
	src = tmp_path / 'src'
	(src / 'a' / 'subdir').mkdir(parents=True)
	(src / 'b' / 'subdir').mkdir(parents=True)
	collisions, missing = collect_h1_filename_collisions(str(src), [('a', 'b')])
	assert missing == []
	assert collisions[0]['filenames'] == ['subdir']


def test_h1_multiple_collisions_sorted(tmp_path):
	src = tmp_path / 'src'
	for cls in ('a', 'b', 'c', 'd'):
		(src / cls).mkdir(parents=True)
	(src / 'a' / 'z.avi').write_bytes(b'1')
	(src / 'b' / 'z.avi').write_bytes(b'2')
	(src / 'c' / 'm.avi').write_bytes(b'3')
	(src / 'd' / 'm.avi').write_bytes(b'4')
	(src / 'c' / 'a.avi').write_bytes(b'5')
	(src / 'd' / 'a.avi').write_bytes(b'6')
	collisions, missing = collect_h1_filename_collisions(str(src), [('c', 'd'), ('a', 'b')])
	assert missing == []
	assert [c['pair'] for c in collisions] == [('a', 'b'), ('c', 'd')]
	assert collisions[1]['filenames'] == ['a.avi', 'm.avi']


def test_h1_missing_class_reported(tmp_path):
	src = tmp_path / 'src'
	(src / 'a').mkdir(parents=True)
	collisions, missing = collect_h1_filename_collisions(str(src), [('a', 'b')])
	assert ('target', 'b') in missing
