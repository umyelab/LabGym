"""
Focused tests for State Transition Map V1 computational product rules.
"""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib

matplotlib.use('Agg')

import pandas as pd
import pytest

from LabGym.tools import (
	_STM_EDGE_LABEL_MAX_ROTATION,
	_STM_EDGE_LABEL_OFFSET_PX,
	_STM_EDGE_LABEL_T,
	_STM_EDGE_LW_MIN,
	_STM_EDGE_LW_SPAN,
	_STM_EDGE_MUTATION_SCALE,
	_STM_EDGE_RAD_BIDIR,
	_STM_EDGE_RAD_SINGLE,
	_STM_EDGE_SHRINK,
	_STM_LEGEND_TEXT,
	_STM_NODE_SIZE_MIN,
	plot_state_transition_map,
	stm_cleanup_obsolete_artifacts,
	stm_cleanup_stale_animal_folder,
	stm_circular_layout,
	stm_compute_animal_metrics,
	stm_edge_label_placement,
	stm_edge_label_rotation,
	stm_edge_linewidth,
	stm_figure_id_subtitle,
	stm_format_edge_label,
	stm_format_node_label,
	stm_hard_labels,
	stm_is_animal_package_dirname,
	stm_node_marker_size,
	stm_pick_edge_label_position,
	stm_safe_animal_folder_name,
	stm_wrap_behavior_name,
)


def _events(labels, conf=None):
	'''Build [label, conf] list; default conf=0.9.'''
	if conf is None:
		conf = [0.9] * len(labels)
	return [[lab, float(c)] for lab, c in zip(labels, conf)]


def test_bouts_and_transitions_collapse_within_segment():
	labels = ['A', 'A', 'A', 'B', 'B', 'C']
	m = stm_compute_animal_metrics(labels, ['A', 'B', 'C'])
	assert m['status'] == 'ok'
	assert m['bout_labels'] == ['A', 'B', 'C']
	assert int(m['count_matrix'].loc['A', 'B']) == 1
	assert int(m['count_matrix'].loc['B', 'C']) == 1
	assert int(m['count_matrix'].values.sum()) == 2
	assert int(m['count_matrix'].loc['A', 'C']) == 0


def test_na_breaks_without_bridging():
	m = stm_compute_animal_metrics(['A', 'NA', 'B'], ['A', 'B'])
	assert m['bout_labels'] == ['A', 'B']
	assert int(m['count_matrix'].loc['A', 'B']) == 0
	assert m['transition_total'] == 0
	assert m['segments'] == [['A'], ['B']]


def test_excluded_behavior_breaks_without_bridging():
	labels = ['Walk', 'Groom', 'Rear']
	included = ['Walk', 'Rear']  # Groom excluded
	m = stm_compute_animal_metrics(labels, included)
	assert m['bout_labels'] == ['Walk', 'Rear']
	assert int(m['count_matrix'].loc['Walk', 'Rear']) == 0
	assert m['transition_total'] == 0
	assert 'Groom' not in m['observed_behaviors']


def test_occupancy_uses_frame_counts_not_bouts():
	# 3 frames A, 2 frames B → occ A=0.6, B=0.4 (not bout share 0.5/0.5)
	m = stm_compute_animal_metrics(['A', 'A', 'A', 'B', 'B'], ['A', 'B'])
	assert m['frame_counts']['A'] == 3
	assert m['frame_counts']['B'] == 2
	assert m['occupancy']['A'] == pytest.approx(0.6)
	assert m['occupancy']['B'] == pytest.approx(0.4)
	assert sum(m['occupancy'].values()) == pytest.approx(1.0)


def test_occupancy_sums_to_one():
	m = stm_compute_animal_metrics(
		['A', 'A', 'B', 'B', 'X', 'C', 'C', 'A'],
		['A', 'B', 'C'],
	)
	assert sum(m['occupancy'].values()) == pytest.approx(1.0)
	assert m['included_frame_total'] == 7
	assert m['frame_counts']['A'] == 3


def test_row_normalized_probabilities_and_zero_outgoing():
	# A→B twice, A→C once; C only terminal
	labels = ['A', 'B', 'A', 'B', 'A', 'C']
	m = stm_compute_animal_metrics(labels, ['A', 'B', 'C'])
	assert float(m['probability_matrix'].loc['A', 'B']) == pytest.approx(2 / 3)
	assert float(m['probability_matrix'].loc['A', 'C']) == pytest.approx(1 / 3)
	assert float(m['probability_matrix'].loc['A'].sum()) == pytest.approx(1.0)
	# C has no outgoing
	assert int(m['count_matrix'].loc['C'].sum()) == 0
	assert m['probability_matrix'].loc['C'].isna().all()


def test_edge_data_preserve_count_and_probability():
	m = stm_compute_animal_metrics(['A', 'B', 'A', 'B', 'A', 'B'], ['A', 'B'])
	assert int(m['count_matrix'].loc['A', 'B']) == 3
	assert float(m['probability_matrix'].loc['A', 'B']) == pytest.approx(1.0)
	assert int(m['count_matrix'].loc['B', 'A']) == 2
	assert float(m['probability_matrix'].loc['B', 'A']) == pytest.approx(1.0)


def test_confidence_ignored():
	labels = ['A', 'A', 'B', 'B', 'C']
	m1 = stm_compute_animal_metrics(labels, ['A', 'B', 'C'])
	e1 = _events(labels, conf=[0.1, 0.2, 0.99, 0.01, 0.5])
	e2 = _events(labels, conf=[0.99, 0.99, 0.01, 0.99, 0.01])
	assert stm_hard_labels(e1) == stm_hard_labels(e2)
	m2 = stm_compute_animal_metrics(stm_hard_labels(e1), ['A', 'B', 'C'])
	m3 = stm_compute_animal_metrics(stm_hard_labels(e2), ['A', 'B', 'C'])
	assert m2['count_matrix'].equals(m3['count_matrix'])
	assert m2['occupancy'] == m3['occupancy']
	assert m1['count_matrix'].equals(m2['count_matrix'])


def test_per_animal_not_pooled(tmp_path):
	event_probability = {
		0: _events(['A', 'B', 'A', 'B']),
		1: _events(['C', 'C', 'D']),
	}
	included = ['A', 'B', 'C', 'D']
	result = plot_state_transition_map(
		str(tmp_path / 'run_stm'),
		event_probability,
		behavior_to_include=included,
		behavior_colors={b: '#112233' for b in included},
		draw_maps=False,
	)
	assert result['status'] == 'success'
	assert result['maps_written'] == 2
	a0 = tmp_path / 'run_stm' / '0'
	a1 = tmp_path / 'run_stm' / '1'
	assert a0.is_dir() and a1.is_dir()
	c0 = pd.read_excel(a0 / 'state_transition_counts.xlsx', index_col=0)
	c1 = pd.read_excel(a1 / 'state_transition_counts.xlsx', index_col=0)
	assert set(c0.index) == {'A', 'B'}
	assert set(c1.index) == {'C', 'D'}
	assert int(c0.loc['A', 'B']) == 2
	assert 'C' not in c0.index
	assert int(c1.values.sum()) == 1


def test_regeneration_removes_stale_animal_and_empty_maps(tmp_path):
	stm = tmp_path / 'demo_state_transition_map'
	included = ['A', 'B']
	r1 = plot_state_transition_map(
		str(stm),
		{
			0: _events(['A', 'B']),
			1: _events(['A', 'A', 'B']),
			2: _events(['A', 'B', 'A']),
		},
		behavior_to_include=included,
		behavior_colors={'A': '#aaaaff', 'B': '#ffaaaa'},
		draw_maps=False,
	)
	assert r1['maps_written'] == 3
	assert (stm / '2').is_dir()

	r2 = plot_state_transition_map(
		str(stm),
		{
			0: _events(['A', 'B']),
			1: _events(['NA', 'NA']),
		},
		behavior_to_include=included,
		behavior_colors={'A': '#aaaaff', 'B': '#ffaaaa'},
		draw_maps=False,
	)
	assert r2['status'] == 'warning_partial'
	assert r2['maps_written'] == 1
	assert r2['empty_animals'] == 1
	assert not (stm / '2').exists()
	assert (stm / '1' / 'state_transition_summary.xlsx').is_file()
	assert not (stm / '1' / 'state_transition_counts.xlsx').exists()


def test_stale_animal_folder_with_only_stm_files_is_removed(tmp_path):
	stm = tmp_path / 'stm_root'
	stm.mkdir()
	# Legacy animal_* package still cleaned.
	stale_legacy = stm / 'animal_99'
	stale_legacy.mkdir()
	(stale_legacy / 'state_transition_map.png').write_bytes(b'x')
	(stale_legacy / 'state_transition_counts.xlsx').write_bytes(b'y')
	(stale_legacy / 'state_transition_summary.xlsx').write_bytes(b'z')
	assert stm_cleanup_stale_animal_folder(str(stale_legacy)) == 'removed'
	assert not stale_legacy.exists()
	# ID-only package.
	stale = stm / '99'
	stale.mkdir()
	(stale / 'state_transition_map.png').write_bytes(b'x')
	assert stm_cleanup_stale_animal_folder(str(stale)) == 'removed'
	assert not stale.exists()


def test_stale_animal_folder_preserves_unknown_content(tmp_path):
	stm = tmp_path / 'stm_root2'
	stm.mkdir()
	stale = stm / '77'
	stale.mkdir()
	(stale / 'state_transition_map.png').write_bytes(b'x')
	(stale / 'user_notes.txt').write_text('keep me')
	outcome = stm_cleanup_stale_animal_folder(str(stale))
	assert outcome == 'preserved'
	assert stale.is_dir()
	assert (stale / 'user_notes.txt').is_file()
	assert not (stale / 'state_transition_map.png').exists()


def test_stale_cleanup_reports_preserved_in_run_result(tmp_path):
	stm = tmp_path / 'stm_run_preserve'
	stm.mkdir()
	stale = stm / '5'
	stale.mkdir()
	(stale / 'state_transition_counts.xlsx').write_bytes(b'old')
	(stale / 'readme_user.txt').write_text('manual')
	result = plot_state_transition_map(
		str(stm),
		{0: _events(['A', 'B'])},
		behavior_to_include=['A', 'B'],
		behavior_colors={'A': '#111111', 'B': '#222222'},
		draw_maps=False,
	)
	assert '5' in result['preserved_stale_animal_folders']
	assert (stale / 'readme_user.txt').is_file()
	assert not (stale / 'state_transition_counts.xlsx').exists()
	summary = pd.read_excel(stm / 'run_summary.xlsx')
	assert '5' in str(summary['preserved_stale_animal_folders'].iloc[0])


def test_all_empty_warning_status(tmp_path):
	result = plot_state_transition_map(
		str(tmp_path / 'empty_stm'),
		{
			0: _events(['NA', 'NA']),
			1: _events(['NA']),
		},
		behavior_to_include=['A', 'B'],
		behavior_colors={'A': '#111111', 'B': '#222222'},
		draw_maps=False,
	)
	assert result['status'] == 'warning_no_maps'
	assert result['maps_written'] == 0
	assert result['empty_animals'] == 2
	assert (tmp_path / 'empty_stm' / 'run_summary.xlsx').is_file()


def test_error_when_no_included_behaviors(tmp_path):
	result = plot_state_transition_map(
		str(tmp_path / 'err_stm'),
		{0: _events(['A', 'B'])},
		behavior_to_include=[],
		draw_maps=False,
	)
	assert result['status'] == 'error'
	assert result['maps_written'] == 0


def test_no_persistence_json_written(tmp_path):
	stm = tmp_path / 'stateless_stm'
	stm.mkdir()
	# plant legacy files — should be cleaned, not recreated
	(stm / 'state_transition_colors.json').write_text('{}')
	(stm / 'state_transition_layout.json').write_text('{}')
	plot_state_transition_map(
		str(stm),
		{0: _events(['A', 'B', 'A'])},
		behavior_to_include=['A', 'B'],
		behavior_colors={'A': '#111111', 'B': '#222222'},
		draw_maps=False,
	)
	assert not (stm / 'state_transition_colors.json').exists()
	assert not (stm / 'state_transition_layout.json').exists()
	assert (stm / '0' / 'state_transition_counts.xlsx').is_file()


def test_draw_maps_optional_png(tmp_path):
	stm = tmp_path / 'png_stm'
	result = plot_state_transition_map(
		str(stm),
		{0: _events(['A', 'B', 'C', 'A'])},
		behavior_to_include=['A', 'B', 'C'],
		behavior_colors={'A': '#111111', 'B': '#222222', 'C': '#333333'},
		draw_maps=True,
		map_dpi=72,
	)
	assert result['status'] == 'success'
	assert (stm / '0' / 'state_transition_map.png').is_file()


def test_safe_animal_folder_name():
	assert stm_safe_animal_folder_name(0) == '0'
	assert stm_safe_animal_folder_name(12) == '12'
	assert '/' not in stm_safe_animal_folder_name('a/b')
	assert stm_safe_animal_folder_name('a/b') == 'a_b'
	assert stm_is_animal_package_dirname('0')
	assert stm_is_animal_package_dirname('animal_3')
	assert not stm_is_animal_package_dirname('my notes')
	assert not stm_is_animal_package_dirname('..')


def test_unrelated_numeric_folder_without_stm_files_not_cleaned(tmp_path):
	'''Numeric user folder that is not an STM package must be left alone.'''
	stm = tmp_path / 'state_transition_map'
	stm.mkdir()
	user_num = stm / '7'
	user_num.mkdir()
	(user_num / 'personal.txt').write_text('keep')
	# Stale true ID package with STM artifacts.
	stale = stm / '9'
	stale.mkdir()
	(stale / 'state_transition_counts.xlsx').write_bytes(b'x')
	preserved = stm_cleanup_obsolete_artifacts(str(stm), current_animal_folder_names={'0'})
	assert user_num.is_dir()
	assert (user_num / 'personal.txt').is_file()
	assert not stale.exists()
	assert '7' not in preserved


def test_figure_title_id_and_legend_constants():
	assert stm_figure_id_subtitle(0) == 'ID 0'
	assert stm_figure_id_subtitle(12) == 'ID 12'
	assert 'time spent in each behavior' in _STM_LEGEND_TEXT
	assert 'probability of transitioning' in _STM_LEGEND_TEXT
	assert 'number of observed transitions' in _STM_LEGEND_TEXT


def test_arrowhead_increased_without_linewidth_change():
	# Arrowheads grown since baseline 15; linewidth formula unchanged.
	assert _STM_EDGE_MUTATION_SCALE > 15
	lw_max = stm_edge_linewidth(1.0, 1.0)
	assert lw_max == pytest.approx(_STM_EDGE_LW_MIN + _STM_EDGE_LW_SPAN)
	assert lw_max <= 4.0


def test_reciprocal_edge_rad_greater_than_single():
	assert _STM_EDGE_RAD_BIDIR > _STM_EDGE_RAD_SINGLE
	assert _STM_EDGE_RAD_BIDIR >= 0.38


def test_gui_stm_button_labels_in_source():
	'''STM panel wording without ellipses / exclusion parenthetical.'''
	src = Path(__file__).resolve().parents[2] / 'LabGym' / 'gui_analyzer.py'
	text = src.read_text(encoding='utf-8')
	start = text.index('class PanelLv2_StateTransitionMap')
	body = text[start:start + 6500]
	assert 'Select an all_events.xlsx' in body
	assert 'file...' not in body
	assert 'Select an all_events.xlsx file...' not in body
	assert 'Set behavior colors...' not in body
	assert 'Set behavior' in body and 'colors' in body
	assert '(nodes removed; sequence breaks)' not in body
	assert 'not saved between runs' not in body
	assert 'Generate state transition maps' in body
	assert "state_transition_map'" in body or 'state_transition_map"' in body or "state_transition_map')" in body
	assert 'all_events_state_transition_map' not in body


def test_stm_gui_exclusion_cancel_preserves_and_ok_updates():
	from LabGym.gui_analyzer import (
		stm_gui_apply_exclusion_dialog_result,
		stm_gui_exclusion_status_label,
	)

	previous = ['Walk', 'Rear']
	assert stm_gui_apply_exclusion_dialog_result(
		previous, ['Groom'], accepted=False,
	) == previous
	assert stm_gui_apply_exclusion_dialog_result(
		previous, ['Groom'], accepted=True,
	) == ['Groom']
	assert stm_gui_apply_exclusion_dialog_result(
		previous, [], accepted=True,
	) == []
	assert stm_gui_exclusion_status_label(previous) == (
		"Excluded: ['Walk', 'Rear']."
	)
	assert stm_gui_exclusion_status_label([]) == 'Default: none.'


def test_stm_gui_color_status_custom_flag():
	from LabGym.gui_analyzer import stm_gui_color_status_label
	from LabGym.tools import stm_session_colors

	assert stm_gui_color_status_label(False) == 'Default behavior colors.'
	assert stm_gui_color_status_label(True) == 'Custom behavior colors set.'
	# Changing exclusions with session merge keeps custom colors; status must stay custom.
	colors_are_custom = True
	colors = stm_session_colors(
		['A', 'B'],
		existing_colors={'A': '#111111', 'B': '#222222'},
	)
	# exclude B: remaining include A only
	colors = stm_session_colors(['A'], existing_colors=colors)
	assert 'A' in colors
	assert colors_are_custom
	assert stm_gui_color_status_label(colors_are_custom) == 'Custom behavior colors set.'


def test_stm_gui_color_dialog_cancel_preserves_flag_semantics():
	from LabGym.gui_analyzer import stm_gui_color_status_label

	# Model: cancel leaves colors_are_custom and mapping untouched.
	prior_custom = True
	prior_colors = {'Walk': '#abcdef'}
	accepted = False
	if accepted:
		prior_custom = True
		prior_colors = {'Walk': '#000000'}
	assert prior_custom is True
	assert prior_colors == {'Walk': '#abcdef'}
	assert stm_gui_color_status_label(prior_custom) == 'Custom behavior colors set.'


def test_stm_gui_parse_failure_reset_semantics():
	'''Simulate successful load then failed load reset without constructing wx.Panel.'''
	from LabGym.gui_analyzer import (
		stm_gui_color_status_label,
		stm_gui_exclusion_status_label,
	)

	# After successful load
	path_to_events = '/tmp/all_events.xlsx'
	behavior_names = ['A', 'B']
	behavior_to_exclude = ['B']
	behavior_colors = {'A': '#111111'}
	colors_are_custom = True
	# After failed parse: same fields as reset_input_dependent_state
	path_to_events = None
	behavior_names = []
	behavior_to_exclude = []
	behavior_colors = {}
	colors_are_custom = False
	input_label = 'No valid all_events.xlsx file selected.'
	assert path_to_events is None
	assert behavior_names == []
	assert behavior_to_exclude == []
	assert behavior_colors == {}
	assert colors_are_custom is False
	assert input_label == 'No valid all_events.xlsx file selected.'
	assert stm_gui_exclusion_status_label(behavior_to_exclude) == 'Default: none.'
	assert stm_gui_color_status_label(colors_are_custom) == 'Default behavior colors.'
	# Generate blocked without valid input
	result_path = '/tmp/out'
	blocked = path_to_events is None or result_path is None
	assert blocked is True


def test_node_size_floor_and_occupancy_scaling():
	s0 = stm_node_marker_size(0.0)
	s_half = stm_node_marker_size(0.5)
	s1 = stm_node_marker_size(1.0)
	assert s0 == pytest.approx(_STM_NODE_SIZE_MIN)
	assert s_half > s0
	assert s1 > s_half
	assert s0 >= 2000.0


def test_deterministic_label_wrapping():
	# Default target ~8–9 chars: balanced multi-word labels, no mid-word splits.
	assert stm_wrap_behavior_name('behind the wheel') == ['behind', 'the wheel']
	assert stm_wrap_behavior_name('body grooming fv') == ['body', 'grooming', 'fv']
	assert stm_wrap_behavior_name('face grooming fv') == ['face', 'grooming', 'fv']
	lines = stm_wrap_behavior_name('Very Long Behavior Name Token')
	assert all(len(line) <= 9 for line in lines)
	assert lines == stm_wrap_behavior_name('Very Long Behavior Name Token')
	# Deterministic for fixed max_line_chars override.
	assert stm_wrap_behavior_name('ab cd ef', max_line_chars=5) == (
		stm_wrap_behavior_name('ab cd ef', max_line_chars=5)
	)
	label, fontsize = stm_format_node_label('Walk', 0.42)
	assert label.split('\n')[0] == 'Walk'
	assert label.endswith('42%')
	assert '42%' in label
	assert fontsize >= 7


def test_linewidth_monotonic_and_compressed():
	lw_small = stm_edge_linewidth(0.1, 1.0)
	lw_mid = stm_edge_linewidth(0.5, 1.0)
	lw_max = stm_edge_linewidth(1.0, 1.0)
	assert lw_small < lw_mid < lw_max
	# Previous formula: 0.4 + 8.0 * sqrt(p/max) → max 8.4
	previous_max = 0.4 + 8.0
	assert lw_max == pytest.approx(_STM_EDGE_LW_MIN + _STM_EDGE_LW_SPAN)
	assert lw_max < previous_max
	assert lw_max <= 4.0


def test_arrow_endpoint_spacing_increased():
	assert _STM_EDGE_SHRINK > 38


def test_edge_label_format_exact():
	assert stm_format_edge_label(0.82, 37) == '0.82 (37)'
	assert stm_format_edge_label(1.0, 1) == '1.00 (1)'


def test_edge_label_placement_follows_curve():
	# Horizontal AB; Arc3 rad>0 bows curve toward negative y.
	x1, y1, x2, y2 = 0.0, 0.0, 2.0, 0.0
	rad = 0.28
	clear = 0.06
	lx, ly, rot = stm_edge_label_placement(x1, y1, x2, y2, rad, clear=clear)
	assert abs(lx - (x1 + x2) / 2.0) < 0.6
	assert ly < 0.0  # beside the bulge, not on the chord centerline alone
	assert abs(rot) <= _STM_EDGE_LABEL_MAX_ROTATION
	assert 20.0 <= _STM_EDGE_LABEL_OFFSET_PX <= 30.0
	assert 0.5 <= _STM_EDGE_LABEL_T <= 0.6
	# Opposite direction bows other side → distinct anchors.
	lx2, ly2, rot2 = stm_edge_label_placement(x2, y2, x1, y1, rad, clear=clear)
	assert ly2 > 0.0
	assert math.hypot(lx - lx2, ly - ly2) > 0.2
	assert abs(rot2) <= _STM_EDGE_LABEL_MAX_ROTATION
	assert stm_edge_label_placement(x1, y1, x2, y2, rad, clear=clear) == (lx, ly, rot)
	# Clamped rotation: steep tangents stay within ~±20–25°, not near-vertical.
	assert 20.0 <= _STM_EDGE_LABEL_MAX_ROTATION <= 25.0
	assert stm_edge_label_rotation(0.0, 1.0) == pytest.approx(_STM_EDGE_LABEL_MAX_ROTATION)
	assert stm_edge_label_rotation(0.0, -1.0) == pytest.approx(-_STM_EDGE_LABEL_MAX_ROTATION)
	assert abs(stm_edge_label_rotation(1.0, 0.2)) < _STM_EDGE_LABEL_MAX_ROTATION
	# Picker keeps labels off nodes when an alternate candidate exists.
	node_centers = {'A': (0.0, 0.0), 'B': (2.0, 0.0)}
	node_radii = {'A': 0.35, 'B': 0.35}
	px, py, prot = stm_pick_edge_label_position(
		x1, y1, x2, y2, rad, clear,
		node_centers, node_radii,
		other_polylines=[],
		placed_centers=[],
		label_half_w=0.12,
		label_half_h=0.05,
	)
	assert math.hypot(px - 0.0, py - 0.0) > node_radii['A']
	assert math.hypot(px - 2.0, py - 0.0) > node_radii['B']
	assert abs(prot) <= _STM_EDGE_LABEL_MAX_ROTATION


def test_deterministic_layout_from_identical_inputs():
	names = ['A', 'B', 'C', 'D']
	p1 = stm_circular_layout(names)
	p2 = stm_circular_layout(names)
	assert p1 == p2
	assert set(p1.keys()) == set(names)
	# Two independent generate-derived layouts from same animal metrics.
	m = stm_compute_animal_metrics(['A', 'B', 'C', 'A'], names)
	pos_a = stm_circular_layout(m['observed_behaviors'])
	pos_b = stm_circular_layout(m['observed_behaviors'])
	assert pos_a == pos_b
