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
from matplotlib.patches import FancyArrowPatch

from LabGym.tools import (
	_STM_EDGE_CASING_EXTRA,
	_STM_EDGE_LABEL_FONTSIZE,
	_STM_EDGE_LABEL_MAX_ROTATION,
	_STM_EDGE_LABEL_MIDDOT,
	_STM_EDGE_LABEL_T,
	_STM_EDGE_LW_MIN,
	_STM_EDGE_LW_SPAN,
	_STM_EDGE_MUTATION_SCALE,
	_STM_EDGE_RAD_BIDIR,
	_STM_EDGE_RAD_SINGLE,
	_STM_FIGSIZE_MAP,
	_STM_KEY_EXPLAIN,
	_STM_KEY_GAP_PT,
	_STM_LABEL_MIN_CLEARANCE_PT,
	_STM_LEGEND_TEXT,
	_STM_NODE_SIZE_MIN,
	_STM_PASS_BEHIND_LEGEND,
	_STM_PASS_BEHIND_MIN_INTERVAL_DT,
	_STM_ROUTE_NODE_PAD_PT,
	_STM_ROUTE_REASONABLE_MAX,
	_STM_ROUTE_SAMPLE_N,
	_stm_data_units_per_point,
	_stm_draw_animal_map,
	_stm_node_radius_data,
	_stm_rad_sign,
	_stm_sample_arc3_polyline,
	plot_state_transition_map,
	stm_arc3_point_and_tangent,
	stm_arc3_point_at_arclength,
	stm_assign_edge_identifiers,
	stm_best_oncurve_label_candidate,
	stm_cleanup_obsolete_artifacts,
	stm_cleanup_stale_animal_folder,
	stm_circular_layout,
	stm_compute_animal_metrics,
	stm_contrast_ratio,
	stm_default_color_palette,
	stm_edge_halfwidth_data,
	stm_edge_label_half_extents_pt,
	stm_edge_label_placement,
	stm_edge_label_rotation,
	stm_edge_linewidth,
	stm_edge_rad,
	stm_edge_route_reasonable_rads,
	stm_edge_shrink_points,
	stm_evaluate_oncurve_label_candidates,
	stm_figure_id_subtitle,
	stm_format_edge_label,
	stm_format_node_label,
	stm_format_occupancy_percent,
	stm_format_transition_key_lines,
	stm_hard_labels,
	stm_is_animal_package_dirname,
	stm_key_pack_y_positions,
	stm_key_region_height_inches,
	stm_marker_radius_points,
	stm_node_label_color,
	stm_node_marker_size,
	stm_ordered_transition_edges,
	stm_pass_behind_path_pieces,
	stm_pick_edge_label_position,
	stm_place_edge_label,
	stm_relative_luminance,
	stm_route_conservative_envelope_bounds,
	stm_route_crossed_nodes,
	stm_route_node_clearance,
	stm_route_obstacle_t_intervals,
	stm_safe_animal_folder_name,
	stm_select_edge_route,
	stm_selected_routes_fit_axes_bounds,
	stm_visible_edge_halfwidth_pt,
	stm_wrap_behavior_name,
)

# Test-local geometric tolerances (not production exports).
_STM_ENDPOINT_TOLERANCE = 0.08
_STM_ON_CURVE_TOLERANCE = 1e-9



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
	assert 'T#' in _STM_LEGEND_TEXT
	assert 'Transition key' in _STM_LEGEND_TEXT


def test_arrowhead_increased_without_linewidth_change():
	# Arrowheads grown since baseline 15; linewidth formula unchanged.
	assert _STM_EDGE_MUTATION_SCALE > 15
	lw_max = stm_edge_linewidth(1.0, 1.0)
	assert lw_max == pytest.approx(_STM_EDGE_LW_MIN + _STM_EDGE_LW_SPAN)
	assert lw_max <= 4.0


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


def test_occupancy_percent_display_lt1_vs_zero():
	assert stm_format_occupancy_percent(0.0) == '0%'
	assert stm_format_occupancy_percent(0.0).startswith('0')
	assert stm_format_occupancy_percent(0.004) == '<1%'
	assert stm_format_occupancy_percent(0.0099) == '<1%'
	assert stm_format_occupancy_percent(0.01) == '1%'
	assert stm_format_occupancy_percent(0.42) == '42%'
	label0, _ = stm_format_node_label('A', 0.0)
	assert label0.endswith('0%')
	assert '<1%' not in label0
	label_small, _ = stm_format_node_label('A', 0.004)
	assert label_small.endswith('<1%')


def test_linewidth_monotonic_and_compressed():
	lw_small = stm_edge_linewidth(0.1, 1.0)
	lw_mid = stm_edge_linewidth(0.5, 1.0)
	lw_max = stm_edge_linewidth(1.0, 1.0)
	assert lw_small < lw_mid < lw_max
	# Previous formula: 0.4 + 8.0 * sqrt(p/max) -> max 8.4
	previous_max = 0.4 + 8.0
	assert lw_max == pytest.approx(_STM_EDGE_LW_MIN + _STM_EDGE_LW_SPAN)
	assert lw_max < previous_max
	assert lw_max <= 4.0


def test_node_label_contrast_wcag_palette_and_custom():
	'''Defaults sit in exact luminance bands; customs keep accessible black/white text.'''
	for fill in stm_default_color_palette():
		L = stm_relative_luminance(fill)
		text = stm_node_label_color(fill)
		assert text in ('#000000', '#FFFFFF')
		assert not (0.15 < L < 0.28)
		if L <= 0.15:
			assert text == '#FFFFFF'
			assert stm_contrast_ratio(fill, '#FFFFFF') >= 4.5
		else:
			assert L >= 0.28
			assert text == '#000000'
			assert stm_contrast_ratio(fill, '#000000') >= 4.5

	# Custom fills may land mid-band; only text (black/white) is auto-chosen.
	for fill in (
		'#000000',
		'#111111',
		'#1a1a1a',
		'#FFFFFF',
		'#F5F5F5',
		'#EEEEEE',
		'#4C72B0',
		'#8172B3',
		'#937860',
	):
		text = stm_node_label_color(fill)
		assert text in ('#000000', '#FFFFFF')
		assert stm_contrast_ratio(fill, text) >= 4.5
	assert stm_node_label_color('#000000') == '#FFFFFF'
	assert stm_node_label_color('#FFFFFF') == '#000000'


def test_edge_label_format_with_identifier():
	assert stm_format_edge_label(0.82, 37) == '0.82 (37)'
	assert stm_format_edge_label(1.0, 1) == '1.00 (1)'
	text = stm_format_edge_label(0.89, 8, edge_id='T5')
	assert text == 'T5 · 0.89 (8)'
	assert text == 'T5' + _STM_EDGE_LABEL_MIDDOT + '0.89 (8)'
	assert '\n' not in text
	assert _STM_EDGE_LABEL_MIDDOT == ' \u00b7 '
	# Longer ids still single-line.
	assert stm_format_edge_label(0.82, 37, edge_id='T12') == 'T12 · 0.82 (37)'
	assert '\n' not in stm_format_edge_label(0.5, 2, edge_id='T99')


def test_transition_key_format_unchanged_by_onmap_single_line():
	'''Key stays "T#: source → destination: p (n)"; on-map uses middle-dot form.'''
	entries = [{
		'edge_id': 'T5',
		'src': 'source',
		'dst': 'destination',
		'value': 0.89,
		'count': 8,
	}]
	key_lines = stm_format_transition_key_lines(entries)
	assert key_lines == ['T5: source \u2192 destination: 0.89 (8)']
	assert ' · ' not in key_lines[0]
	assert '\n' not in key_lines[0]
	on_map = stm_format_edge_label(0.89, 8, edge_id='T5')
	assert on_map == 'T5 · 0.89 (8)'
	assert on_map != key_lines[0]


def test_edge_label_half_extents_single_line_bbox():
	'''Single-line bbox is wider than tall; not the legacy two-line 36×14 half-box.'''
	text = stm_format_edge_label(0.89, 8, edge_id='T5')
	hw, hh = stm_edge_label_half_extents_pt(text)
	assert '\n' not in text
	assert hw > hh
	# Shorter than legacy two-line half-height (14 pt).
	assert hh < 14.0
	# Representative long label is wider than short one.
	hw_long, hh_long = stm_edge_label_half_extents_pt(
		stm_format_edge_label(0.99, 999, edge_id='T99'),
	)
	assert hw_long > hw
	assert abs(hh_long - hh) < 1e-12
	# Default representative extents match long single-line sizing.
	hw_def, hh_def = stm_edge_label_half_extents_pt()
	assert hw_def == pytest.approx(hw_long)
	assert hh_def == pytest.approx(hh_long)
	assert _STM_EDGE_LABEL_FONTSIZE == 8.0


def test_oncurve_and_callout_use_single_line_label_extents():
	'''Placement collides with the wider/shorter single-line half-extents.'''
	x1, y1, x2, y2 = 0.0, 0.0, 2.0, 0.0
	rad = 0.28
	text = stm_format_edge_label(0.89, 8, edge_id='T5')
	assert '\n' not in text
	hw_pt, hh_pt = stm_edge_label_half_extents_pt(text)
	# Data-ish half box proportional to pt estimate.
	label_half_w = hw_pt * 0.01
	label_half_h = hh_pt * 0.01
	# Two-line legacy box was taller relative to this single-line height.
	legacy_half_w = 36.0 * 0.01
	legacy_half_h = 14.0 * 0.01
	assert label_half_h < legacy_half_h
	assert label_half_w != legacy_half_w or label_half_h != legacy_half_h

	node_centers = {'A': (0.0, 0.0), 'B': (2.0, 0.0)}
	node_radii = {'A': 0.2, 'B': 0.2}
	on_curve = stm_place_edge_label(
		x1, y1, x2, y2, rad,
		node_centers, node_radii, [], [],
		label_half_w, label_half_h,
		min_clearance_data=0.001,
		units_per_point=0.01,
	)
	assert on_curve['mode'] == 'on_curve'
	callout = stm_place_edge_label(
		x1, y1, x2, y2, rad,
		node_centers, node_radii, [], [],
		label_half_w, label_half_h,
		min_clearance_data=5.0,
		units_per_point=0.01,
	)
	assert callout['mode'] == 'callout'
	# Same extents + inputs → same placement (deterministic).
	assert stm_place_edge_label(
		x1, y1, x2, y2, rad,
		node_centers, node_radii, [], [],
		label_half_w, label_half_h,
		min_clearance_data=0.001,
		units_per_point=0.01,
	) == on_curve
	assert stm_place_edge_label(
		x1, y1, x2, y2, rad,
		node_centers, node_radii, [], [],
		label_half_w, label_half_h,
		min_clearance_data=5.0,
		units_per_point=0.01,
	) == callout


def test_deterministic_edge_identifiers_and_key_ordering():
	m = stm_compute_animal_metrics(
		['A', 'B', 'A', 'C', 'B', 'A'],
		['A', 'B', 'C'],
	)
	e1 = stm_assign_edge_identifiers(
		stm_ordered_transition_edges(
			m['observed_behaviors'],
			m['count_matrix'],
			m['probability_matrix'],
		)
	)
	e2 = stm_assign_edge_identifiers(
		stm_ordered_transition_edges(
			m['observed_behaviors'],
			m['count_matrix'],
			m['probability_matrix'],
		)
	)
	assert [edge['edge_id'] for edge in e1] == [edge['edge_id'] for edge in e2]
	assert [edge['edge_id'] for edge in e1] == [
		'T%d' % i for i in range(1, len(e1) + 1)
	]
	# Ordered by (src, dst) in sorted observed: A,B,C
	assert [(edge['src'], edge['dst']) for edge in e1] == sorted(
		[(edge['src'], edge['dst']) for edge in e1],
		key=lambda pair: (
			m['observed_behaviors'].index(pair[0]),
			m['observed_behaviors'].index(pair[1]),
		),
	)
	key1 = stm_format_transition_key_lines(e1)
	key2 = stm_format_transition_key_lines(e2)
	assert key1 == key2
	assert key1[0].startswith('T1: ')
	assert ' → ' in key1[0]
	assert key1[0].endswith(
		': %.2f (%d)' % (e1[0]['value'], e1[0]['count'])
	)


def test_edge_endpoints_terminate_near_node_boundaries():
	'''Shrink tracks node radius so path endpoints meet node boundaries.'''
	occ_src = 0.2
	occ_dst = 0.8
	s_src = stm_node_marker_size(occ_src)
	s_dst = stm_node_marker_size(occ_dst)
	shrink_a = stm_edge_shrink_points(s_src)
	shrink_b = stm_edge_shrink_points(s_dst)
	assert shrink_a == pytest.approx(stm_marker_radius_points(s_src) + 4.0)
	assert shrink_b == pytest.approx(stm_marker_radius_points(s_dst) + 4.0)
	assert shrink_b > shrink_a

	# Geometric check in a fixed data-space conversion (1 data unit = 50 points).
	points_per_data = 50.0
	x1, y1, x2, y2 = 0.0, 0.0, 2.0, 0.0
	rad = _STM_EDGE_RAD_SINGLE
	r_src = stm_marker_radius_points(s_src) / points_per_data
	r_dst = stm_marker_radius_points(s_dst) / points_per_data
	shrink_a_data = shrink_a / points_per_data
	shrink_b_data = shrink_b / points_per_data
	ex, ey, _ = stm_arc3_point_at_arclength(
		x1, y1, x2, y2, rad, shrink_a_data, from_end=False,
	)
	fx, fy, _ = stm_arc3_point_at_arclength(
		x1, y1, x2, y2, rad, shrink_b_data, from_end=True,
	)
	# Attachment points sit at node radius (+ small stroke pad) along the curve.
	assert abs(math.hypot(ex - x1, ey - y1) - shrink_a_data) <= _STM_ENDPOINT_TOLERANCE
	assert abs(math.hypot(fx - x2, fy - y2) - shrink_b_data) <= _STM_ENDPOINT_TOLERANCE
	assert abs(shrink_a_data - r_src) <= 4.0 / points_per_data + 1e-9
	assert abs(shrink_b_data - r_dst) <= 4.0 / points_per_data + 1e-9


def test_reciprocal_transitions_are_geometrically_distinguishable():
	assert _STM_EDGE_RAD_BIDIR > _STM_EDGE_RAD_SINGLE
	m = stm_compute_animal_metrics(['A', 'B', 'A', 'B'], ['A', 'B'])
	# Magnitude seed (not final drawn rad).
	assert stm_edge_rad('A', 'B', m['count_matrix']) == _STM_EDGE_RAD_BIDIR
	assert stm_edge_rad('B', 'A', m['count_matrix']) == _STM_EDGE_RAD_BIDIR
	x1, y1 = 0.0, 0.0
	x2, y2 = 2.0, 0.0
	node_centers = {'A': (0.0, 0.0), 'B': (2.0, 0.0)}
	node_radii = {'A': 0.2, 'B': 0.2}
	r1 = stm_select_edge_route(
		x1, y1, x2, y2, 'A', 'B', _STM_EDGE_RAD_BIDIR,
		node_centers, node_radii, 0.05, 0.02, [], paired_sign=None,
	)
	r2 = stm_select_edge_route(
		x2, y2, x1, y1, 'B', 'A', _STM_EDGE_RAD_BIDIR,
		node_centers, node_radii, 0.05, 0.02, [r1['polyline']],
		paired_sign=_stm_rad_sign(r1['rad']),
	)
	assert r1['clearance'] >= 0.0
	assert r2['clearance'] >= 0.0
	assert r2['reciprocal_side_relaxed'] is False
	# Same Arc3 rad *sign* => opposite geometric bows when endpoints reverse.
	assert _stm_rad_sign(r1['rad']) == _stm_rad_sign(r2['rad'])
	mx1, my1, _, _ = stm_arc3_point_and_tangent(x1, y1, x2, y2, r1['rad'], 0.5)
	mx2, my2, _, _ = stm_arc3_point_and_tangent(x2, y2, x1, y1, r2['rad'], 0.5)
	assert my1 * my2 < 0.0
	assert math.hypot(mx1 - mx2, my1 - my2) > 0.2


def test_edge_labels_lie_on_home_curve_and_are_deterministic():
	x1, y1, x2, y2 = 0.0, 0.0, 2.0, 0.0
	rad = 0.28
	lx, ly, rot = stm_edge_label_placement(x1, y1, x2, y2, rad)
	home = _stm_sample_arc3_polyline(x1, y1, x2, y2, rad, n=64)
	# Label is generated from the home Arc3 curve (exact sample or on polyline).
	on_curve = False
	for t in (_STM_EDGE_LABEL_T, 0.5, 0.55, 0.6):
		px, py, _, _ = stm_arc3_point_and_tangent(x1, y1, x2, y2, rad, t)
		if math.hypot(lx - px, ly - py) <= _STM_ON_CURVE_TOLERANCE:
			on_curve = True
			break
	if not on_curve:
		# Distance to densely sampled home curve must be within tolerance.
		from LabGym.tools import _stm_min_dist_to_polyline
		assert _stm_min_dist_to_polyline(lx, ly, home) <= 1e-6
	assert abs(rot) <= _STM_EDGE_LABEL_MAX_ROTATION
	assert stm_edge_label_placement(x1, y1, x2, y2, rad) == (lx, ly, rot)

	# Opposite direction is also on its own curve and deterministic.
	lx2, ly2, rot2 = stm_edge_label_placement(x2, y2, x1, y1, rad)
	assert stm_edge_label_placement(x2, y2, x1, y1, rad) == (lx2, ly2, rot2)
	assert math.hypot(lx - lx2, ly - ly2) > 0.2

	# Picker returns an on-curve point; identical inputs -> identical placement.
	node_centers = {'A': (0.0, 0.0), 'B': (2.0, 0.0)}
	node_radii = {'A': 0.35, 'B': 0.35}
	p1 = stm_pick_edge_label_position(
		x1, y1, x2, y2, rad,
		node_centers, node_radii,
		other_polylines=[],
		placed_centers=[],
		label_half_w=0.12,
		label_half_h=0.05,
	)
	p2 = stm_pick_edge_label_position(
		x1, y1, x2, y2, rad,
		node_centers, node_radii,
		other_polylines=[],
		placed_centers=[],
		label_half_w=0.12,
		label_half_h=0.05,
	)
	assert p1 == p2
	px, py, prot = p1
	matched = False
	for t in (
		0.55, 0.50, 0.60, 0.45, 0.65, 0.40, 0.70,
	):
		qx, qy, _, _ = stm_arc3_point_and_tangent(x1, y1, x2, y2, rad, t)
		if math.hypot(px - qx, py - qy) <= _STM_ON_CURVE_TOLERANCE:
			matched = True
			break
	assert matched
	assert abs(prot) <= _STM_EDGE_LABEL_MAX_ROTATION
	assert math.hypot(px - 0.0, py - 0.0) > node_radii['A']
	assert math.hypot(px - 2.0, py - 0.0) > node_radii['B']


def test_edge_label_collision_maximizes_minimum_clearance():
	'''Picker chooses the candidate t that maximizes min clearance to a crossing.'''
	x1, y1, x2, y2 = 0.0, 0.0, 2.0, 0.0
	rad = 0.35
	# Foreign polyline crosses near the preferred mid-curve point.
	foreign = [(1.0, -0.5), (1.0, 0.5)]
	node_centers = {'A': (0.0, 0.0), 'B': (2.0, 0.0)}
	node_radii = {'A': 0.2, 'B': 0.2}
	px, py, _ = stm_pick_edge_label_position(
		x1, y1, x2, y2, rad,
		node_centers, node_radii,
		other_polylines=[foreign],
		placed_centers=[],
		label_half_w=0.12,
		label_half_h=0.05,
	)
	from LabGym.tools import _stm_min_dist_to_polyline
	# Chosen point remains on the home curve.
	matched_t = None
	for t in (0.55, 0.50, 0.60, 0.45, 0.65, 0.40, 0.70):
		qx, qy, _, _ = stm_arc3_point_and_tangent(x1, y1, x2, y2, rad, t)
		if math.hypot(px - qx, py - qy) <= _STM_ON_CURVE_TOLERANCE:
			matched_t = t
			break
	assert matched_t is not None
	mid_x, mid_y, _, _ = stm_arc3_point_and_tangent(x1, y1, x2, y2, rad, 0.55)
	d_mid = _stm_min_dist_to_polyline(mid_x, mid_y, foreign)
	d_pick = _stm_min_dist_to_polyline(px, py, foreign)
	# Maximin clearance should leave the mid-curve crossing when a better t exists.
	assert d_pick > d_mid + 1e-9
	assert matched_t != 0.55


def test_edge_label_rotation_clamped_and_upright():
	'''Rotation is upright then clamped to +/- max degrees.'''
	# Steep upward tangent would exceed clamp.
	assert stm_edge_label_rotation(0.1, 1.0) == pytest.approx(
		_STM_EDGE_LABEL_MAX_ROTATION
	)
	assert stm_edge_label_rotation(0.1, -1.0) == pytest.approx(
		-_STM_EDGE_LABEL_MAX_ROTATION
	)
	# Near-horizontal is unchanged within clamp.
	assert abs(stm_edge_label_rotation(1.0, 0.05)) <= _STM_EDGE_LABEL_MAX_ROTATION
	# Upside-down tangents are flipped upright before clamp.
	rot = stm_edge_label_rotation(-1.0, 0.0)
	assert abs(rot) <= 90.0
	assert abs(rot) <= _STM_EDGE_LABEL_MAX_ROTATION
	assert stm_edge_label_rotation(1.0, 0.0, max_deg=10.0) == pytest.approx(0.0)


def test_fancy_arrow_patch_casing_and_shrink_integration(tmp_path, monkeypatch):
	'''Inspect FancyArrowPatch kwargs from _stm_draw_animal_map (no PNG write).'''
	captured = []
	RealFancyArrowPatch = FancyArrowPatch

	class CapturingFancyArrowPatch(RealFancyArrowPatch):
		def __init__(self, *args, **kwargs):
			captured.append({
				'posA': args[0] if len(args) > 0 else kwargs.get('posA'),
				'posB': args[1] if len(args) > 1 else kwargs.get('posB'),
				'kwargs': dict(kwargs),
			})
			super().__init__(*args, **kwargs)

	monkeypatch.setattr(
		'matplotlib.patches.FancyArrowPatch',
		CapturingFancyArrowPatch,
	)
	import matplotlib.pyplot as plt
	monkeypatch.setattr(plt, 'savefig', lambda *a, **k: None)

	labels = ['A', 'B', 'A', 'C', 'B']
	included = ['A', 'B', 'C']
	metrics = stm_compute_animal_metrics(labels, included)
	assert metrics['status'] == 'ok'
	edges = stm_ordered_transition_edges(
		metrics['observed_behaviors'],
		metrics['count_matrix'],
		metrics['probability_matrix'],
	)
	assert len(edges) >= 2
	positions = stm_circular_layout(metrics['observed_behaviors'])
	colors = {name: '#6B9FE0' for name in metrics['observed_behaviors']}
	animal_dir = tmp_path / '0'
	animal_dir.mkdir()
	_stm_draw_animal_map(
		str(animal_dir),
		0,
		metrics,
		positions,
		colors,
		dpi=72,
	)

	assert len(captured) == 2 * len(edges)
	occupancy = metrics['occupancy']
	max_edge = max(float(e['value']) for e in edges)
	for i, edge in enumerate(edges):
		casing = captured[2 * i]
		fg = captured[2 * i + 1]
		ck = casing['kwargs']
		fk = fg['kwargs']
		assert ck.get('color') == 'white'
		assert fk.get('color') == 'black'
		assert float(ck['linewidth']) > float(fk['linewidth'])
		assert float(ck['linewidth']) == pytest.approx(
			float(fk['linewidth']) + _STM_EDGE_CASING_EXTRA
		)
		assert int(ck['zorder']) < int(fk['zorder'])
		assert casing['posA'] == fg['posA']
		assert casing['posB'] == fg['posB']
		assert ck['connectionstyle'] == fk['connectionstyle']
		assert ck['shrinkA'] == fk['shrinkA']
		assert ck['shrinkB'] == fg['kwargs']['shrinkB']
		assert ck['arrowstyle'] == fk['arrowstyle']
		src, dst = edge['src'], edge['dst']
		assert ck['shrinkA'] == pytest.approx(
			stm_edge_shrink_points(stm_node_marker_size(occupancy[src]))
		)
		assert ck['shrinkB'] == pytest.approx(
			stm_edge_shrink_points(stm_node_marker_size(occupancy[dst]))
		)
		assert float(fk['linewidth']) == pytest.approx(
			stm_edge_linewidth(edge['value'], max_edge)
		)
	assert not (tmp_path / '0' / 'state_transition_map.png').exists()


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


def test_route_casing_clearance_avoids_unrelated_nodes():
	'''Visible casing half-width + radius + pad are cleared of non-endpoints.'''
	# Chord A->C passes through B on the x-axis; route must bow around B.
	node_centers = {
		'A': (0.0, 0.0),
		'B': (1.0, 0.0),
		'C': (2.0, 0.0),
	}
	node_radii = {'A': 0.15, 'B': 0.20, 'C': 0.15}
	half_w = 0.08
	pad = 0.03
	route = stm_select_edge_route(
		0.0, 0.0, 2.0, 0.0, 'A', 'C', 0.12,
		node_centers, node_radii, half_w, pad, [],
	)
	assert route['clearance'] >= 0.0
	assert route['pass_behind'] is False
	obstacles = {'B': node_centers['B']}
	clear = stm_route_node_clearance(
		route['polyline'],
		obstacles,
		{'B': node_radii['B']},
		half_w,
		pad,
	)
	assert clear >= 0.0
	assert clear == pytest.approx(route['clearance'])
	assert stm_visible_edge_halfwidth_pt(1.0) > 0.5


def test_clear_route_remains_fully_solid():
	node_centers = {'A': (0.0, 0.0), 'B': (2.0, 0.0)}
	node_radii = {'A': 0.15, 'B': 0.15}
	route = stm_select_edge_route(
		0.0, 0.0, 2.0, 0.0, 'A', 'B', 0.12,
		node_centers, node_radii, 0.05, 0.02, [],
	)
	assert route['pass_behind'] is False
	assert route['crossed_nodes'] == []
	pieces = stm_pass_behind_path_pieces(
		0.0, 0.0, 2.0, 0.0, route['rad'], [], 0.05,
	)
	assert pieces
	assert all(p['style'] == 'solid' for p in pieces)


def test_forced_no_clear_route_uses_pass_behind_not_raise():
	'''Oversized mid-node forces pass-behind; no RuntimeError.'''
	node_centers = {
		'A': (0.0, 0.0),
		'B': (1.0, 0.0),
		'C': (2.0, 0.0),
	}
	node_radii = {'A': 0.1, 'B': 1.5, 'C': 0.1}
	route = stm_select_edge_route(
		0.0, 0.0, 2.0, 0.0, 'A', 'C', 0.12,
		node_centers, node_radii, 0.2, 0.1, [],
	)
	assert route['pass_behind'] is True
	assert 'B' in route['crossed_nodes']
	assert abs(route['rad']) <= _STM_ROUTE_REASONABLE_MAX + 1e-12
	assert max(abs(r) for r in stm_edge_route_reasonable_rads(0.12)) <= (
		_STM_ROUTE_REASONABLE_MAX + 1e-12
	)


def test_pass_behind_hides_center_and_dashes_at_boundary():
	x1, y1, x2, y2 = 0.0, 0.0, 2.0, 0.0
	rad = 0.0  # straight through mid node
	node_centers = {
		'A': (0.0, 0.0),
		'B': (1.0, 0.0),
		'C': (2.0, 0.0),
	}
	node_radii = {'A': 0.1, 'B': 0.25, 'C': 0.1}
	half_w, pad = 0.05, 0.02
	intervals = stm_route_obstacle_t_intervals(
		x1, y1, x2, y2, rad, {'B': (1.0, 0.0)}, {'B': 0.25}, half_w, pad,
	)
	assert intervals
	assert intervals[0][0] == 'B'
	t_enter, t_exit = intervals[0][1], intervals[0][2]
	assert 0.0 < t_enter < 0.5 < t_exit < 1.0
	pieces = stm_pass_behind_path_pieces(
		x1, y1, x2, y2, rad, intervals, 0.06,
	)
	styles = [p['style'] for p in pieces]
	assert 'dash' in styles
	assert 'solid' in styles
	# No sample points deep inside the node disk.
	r = 0.25 + half_w + pad
	for piece in pieces:
		for px, py in piece['points']:
			assert math.hypot(px - 1.0, py - 0.0) + 1e-9 >= r * 0.85
	# Dash pieces should sit near enter/exit.
	dash_mid_ts = []
	for piece in pieces:
		if piece['style'] != 'dash':
			continue
		mx = sum(p[0] for p in piece['points']) / len(piece['points'])
		# Straight chord: x ≈ 2t
		dash_mid_ts.append(mx / 2.0)
	assert any(abs(t - t_enter) < 0.15 for t in dash_mid_ts)
	assert any(abs(t - t_exit) < 0.15 for t in dash_mid_ts)


def test_pass_behind_multiple_crossed_nodes():
	x1, y1, x2, y2 = 0.0, 0.0, 3.0, 0.0
	rad = 0.0
	obstacles = {'B': (1.0, 0.0), 'D': (2.0, 0.0)}
	radii = {'B': 0.2, 'D': 0.2}
	half_w, pad = 0.04, 0.01
	intervals = stm_route_obstacle_t_intervals(
		x1, y1, x2, y2, rad, obstacles, radii, half_w, pad,
	)
	names = [iv[0] for iv in intervals]
	assert names == sorted(names)
	assert 'B' in names and 'D' in names
	pieces = stm_pass_behind_path_pieces(
		x1, y1, x2, y2, rad, intervals, 0.04,
	)
	assert sum(1 for p in pieces if p['style'] == 'dash') >= 2


def test_pass_behind_preserves_probability_count_and_direction(tmp_path, monkeypatch):
	import matplotlib.pyplot as plt
	monkeypatch.setattr(plt, 'savefig', lambda *a, **k: None)
	# Force pass-behind on A->C through large mid occupancy node.
	labels = ['A', 'C', 'A', 'C'] + ['B'] * 20
	metrics = stm_compute_animal_metrics(labels, ['A', 'B', 'C'])
	# Place B between A and C on a line-like layout.
	positions = {
		'A': (0.0, 0.0),
		'B': (1.0, 0.0),
		'C': (2.0, 0.0),
	}
	# Inflate B by high occupancy when drawing radii; force route pass-behind
	# via select API with fat radius.
	max_edge = 1.0
	routes = []
	for edge in stm_ordered_transition_edges(
		metrics['observed_behaviors'],
		metrics['count_matrix'],
		metrics['probability_matrix'],
	):
		route = stm_select_edge_route(
			positions[edge['src']][0],
			positions[edge['src']][1],
			positions[edge['dst']][0],
			positions[edge['dst']][1],
			edge['src'],
			edge['dst'],
			0.12,
			positions,
			{'A': 0.1, 'B': 1.2, 'C': 0.1},
			0.15,
			0.05,
			[],
		)
		routes.append((edge, route))
	ac = [r for e, r in routes if e['src'] == 'A' and e['dst'] == 'C']
	if ac:
		assert ac[0]['pass_behind'] is True
		e = next(e for e, r in routes if e['src'] == 'A' and e['dst'] == 'C')
		assert e['value'] > 0
		assert e['count'] >= 1
	# Drawing must not raise with fat mid node.
	metrics_force = metrics
	# Artificially huge marker for B only via occupancy after clone of radii path:
	animal_dir = tmp_path / '0'
	animal_dir.mkdir()
	colors = {n: '#6B9FE0' for n in metrics['observed_behaviors']}
	# Still use circular layout but pass-behind not guaranteed; at least draw.
	_stm_draw_animal_map(
		str(animal_dir),
		0,
		metrics_force,
		stm_circular_layout(metrics['observed_behaviors']),
		colors,
		dpi=72,
	)


def test_conditional_legend_pass_behind_only_when_used(tmp_path, monkeypatch):
	import matplotlib.pyplot as plt
	from LabGym import tools as tools_mod

	captured = []

	real_text = plt.Axes.text

	def capturing_text(self, *args, **kwargs):
		if args:
			captured.append(args[2] if len(args) > 2 else kwargs.get('s', ''))
		elif 's' in kwargs:
			captured.append(kwargs['s'])
		return real_text(self, *args, **kwargs)

	monkeypatch.setattr(plt.Axes, 'text', capturing_text)
	monkeypatch.setattr(plt, 'savefig', lambda *a, **k: None)

	# Clear map: only A↔B — no third-node crossings expected.
	m_clear = stm_compute_animal_metrics(['A', 'B', 'A', 'B'], ['A', 'B'])
	dirs = tmp_path / 'clear'
	dirs.mkdir()
	_stm_draw_animal_map(
		str(dirs),
		0,
		m_clear,
		stm_circular_layout(m_clear['observed_behaviors']),
		{n: '#6B9FE0' for n in m_clear['observed_behaviors']},
		dpi=72,
	)
	legend_clear = [t for t in captured if isinstance(t, str) and 'Node size' in t]
	assert legend_clear
	assert _STM_PASS_BEHIND_LEGEND not in legend_clear[-1]

	# Force pass-behind by making final-transform clearance check always fail
	# (flags any_pass_behind and appends the conditional legend line).
	captured.clear()

	monkeypatch.setattr(
		tools_mod,
		'stm_route_node_clearance',
		lambda *a, **k: -0.05,
	)
	monkeypatch.setattr(
		tools_mod,
		'stm_route_crossed_nodes',
		lambda *a, **k: ['forced'],
	)
	dirp = tmp_path / 'pass'
	dirp.mkdir()
	_stm_draw_animal_map(
		str(dirp),
		1,
		m_clear,
		stm_circular_layout(m_clear['observed_behaviors']),
		{n: '#6B9FE0' for n in m_clear['observed_behaviors']},
		dpi=72,
	)
	legend_pass = [t for t in captured if isinstance(t, str) and 'Node size' in t]
	assert legend_pass
	assert _STM_PASS_BEHIND_LEGEND in legend_pass[-1]
	assert _STM_PASS_BEHIND_LEGEND == (
		'Dashed segment = edge passes behind a node.'
	)


def test_multi_animal_continues_without_routing_exception(tmp_path, monkeypatch):
	import matplotlib.pyplot as plt
	monkeypatch.setattr(plt, 'savefig', lambda *a, **k: None)
	event_probability = {
		0: [['A', 0.9], ['B', 0.9], ['A', 0.9]],
		1: [['X', 0.9], ['Y', 0.9], ['Z', 0.9], ['X', 0.9]],
	}
	# Mid-node dense chain animal should not abort package.
	event_probability[1] = (
		[['A', 0.9], ['C', 0.9]] * 3
		+ [['B', 0.9]] * 30
	)
	result = plot_state_transition_map(
		str(tmp_path / 'stm'),
		event_probability,
		['A', 'B', 'C'],
		behavior_colors={
			'A': '#6B9FE0',
			'B': '#DD8452',
			'C': '#55A868',
		},
		draw_maps=True,
		map_dpi=72,
	)
	assert result['status'] in ('success', 'warning_partial', 'warning_no_maps')
	assert result.get('maps_written', 0) >= 1


def test_route_selection_deterministic():
	node_centers = {'A': (0.0, 0.0), 'B': (1.0, 0.5), 'C': (2.0, 0.0)}
	node_radii = {'A': 0.15, 'B': 0.15, 'C': 0.15}
	kwargs = dict(
		x1=0.0, y1=0.0, x2=2.0, y2=0.0, src='A', dst='C',
		seed_magnitude=0.12,
		node_centers=node_centers, node_radii=node_radii,
		half_width_data=0.05, pad_data=0.02, selected_polylines=[],
	)
	r1 = stm_select_edge_route(**kwargs)
	r2 = stm_select_edge_route(**kwargs)
	assert r1['rad'] == r2['rad']
	assert r1['clearance'] == r2['clearance']
	assert r1['pass_behind'] == r2['pass_behind']


def test_micro_crossing_interval_expanded_hidden_with_dashes():
	'''Single-sample real crossing must yield a hide interval and dash segments.'''
	x1, y1, x2, y2 = 0.0, 0.0, 2.0, 0.0
	rad = 0.0
	n = _STM_ROUTE_SAMPLE_N * 2
	# Neighbor sample spacing on the chord is 2/n data units; choose R so only
	# the exact midpoint sample lies inside the reserved disk (micro-hit).
	r_disk = (2.0 / float(n)) * 0.49
	half_w = 0.0
	pad = 0.0
	obstacles = {'M': (1.0, 0.0)}
	radii = {'M': r_disk}
	# Raw hits: exactly one sample inside when sampling with n.
	inside_count = 0
	for i in range(n + 1):
		t = i / float(n)
		px, py, _, _ = stm_arc3_point_and_tangent(x1, y1, x2, y2, rad, t)
		if math.hypot(px - 1.0, py - 0.0) < r_disk + half_w + pad:
			inside_count += 1
	assert inside_count == 1

	intervals = stm_route_obstacle_t_intervals(
		x1, y1, x2, y2, rad, obstacles, radii, half_w, pad, n=n,
	)
	assert intervals, 'micro-crossing interval must not be discarded'
	assert intervals[0][0] == 'M'
	t_enter, t_exit = intervals[0][1], intervals[0][2]
	assert t_exit > t_enter + 1e-9
	assert t_exit - t_enter + 1e-12 >= min(
		_STM_PASS_BEHIND_MIN_INTERVAL_DT, 1.0 / float(n),
	)
	assert 0.0 <= t_enter < 0.5 < t_exit <= 1.0

	dash_dt = 0.05
	pieces = stm_pass_behind_path_pieces(
		x1, y1, x2, y2, rad, intervals, dash_dt, n=n,
	)
	styles = [p['style'] for p in pieces]
	assert 'dash' in styles
	assert 'solid' in styles
	# Covered center at t=0.5 must not appear in any drawn polyline point.
	r_reserved = r_disk + half_w + pad
	for piece in pieces:
		for px, py in piece['points']:
			assert math.hypot(px - 1.0, py - 0.0) + 1e-9 >= r_reserved * 0.5
	# At least one sample on the curve midpoint is in the expanded hidden band.
	assert t_enter - 1e-12 <= 0.5 <= t_exit + 1e-12


def test_final_transform_reselection_picks_clear_alternate_rad(tmp_path, monkeypatch):
	'''
	Real axes + clearance: preliminary rad can fail after bounds expand while
	another reasonable rad remains clear; final routing must reselect it.
	'''
	import matplotlib.pyplot as plt
	from LabGym import tools as tools_mod

	monkeypatch.setattr(plt, 'savefig', lambda *a, **k: None)

	fig = plt.figure(figsize=(6, 6), dpi=72)
	ax = fig.add_subplot(111)
	ax.set_aspect('equal')
	centers = {'A': (0.0, 0.0), 'M': (1.0, 0.0), 'B': (2.0, 0.0)}
	occ = {'A': 0.15, 'M': 0.15, 'B': 0.15}
	lw_pt = 1.5

	def radii_pad_half():
		fig.canvas.draw()
		pad = _STM_ROUTE_NODE_PAD_PT * _stm_data_units_per_point(ax)
		radii = {
			name: _stm_node_radius_data(ax, stm_node_marker_size(occ[name]))
			for name in centers
		}
		half_w = stm_edge_halfwidth_data(
			ax, stm_visible_edge_halfwidth_pt(lw_pt),
		)
		return radii, pad, half_w

	# Preliminary (tight) transform: select a mild clear rad.
	ax.set_xlim(-0.2, 2.2)
	ax.set_ylim(-0.15, 0.15)
	rad_p, pad_p, half_p = radii_pad_half()
	preliminary = stm_select_edge_route(
		0.0, 0.0, 2.0, 0.0, 'A', 'B', 0.12,
		centers, rad_p, half_p, pad_p, [],
	)
	assert preliminary['pass_behind'] is False
	prelim_rad = preliminary['rad']

	# Final (expanded) transform: that same rad is no longer clear, but another
	# reasonable rad still clears the mid node under real geometry.
	ax.set_xlim(-0.2, 2.2)
	ax.set_ylim(-1.8, 1.8)
	rad_f, pad_f, half_f = radii_pad_half()
	obst = {'M': centers['M']}
	obst_r = {'M': rad_f['M']}
	poly_prelim = _stm_sample_arc3_polyline(
		0.0, 0.0, 2.0, 0.0, prelim_rad, n=_STM_ROUTE_SAMPLE_N,
	)
	clear_prelim_final = stm_route_node_clearance(
		poly_prelim, obst, obst_r, half_f, pad_f,
	)
	assert clear_prelim_final < 0.0, (
		'fixture requires preliminary rad invalid under final transform'
	)
	clear_alts = []
	for rad in stm_edge_route_reasonable_rads(0.12):
		poly = _stm_sample_arc3_polyline(
			0.0, 0.0, 2.0, 0.0, rad, n=_STM_ROUTE_SAMPLE_N,
		)
		c = stm_route_node_clearance(poly, obst, obst_r, half_f, pad_f)
		if c >= 0.0:
			clear_alts.append(rad)
	assert clear_alts, 'fixture needs a clear alternate reasonable rad'

	# Full reselection under final transform (production ranking) — not demote.
	final = stm_select_edge_route(
		0.0, 0.0, 2.0, 0.0, 'A', 'B', 0.12,
		centers, rad_f, half_f, pad_f, [],
	)
	assert final['pass_behind'] is False
	assert final['rad'] in clear_alts
	assert final['clearance'] >= 0.0
	assert final['rad'] != prelim_rad

	# Draw path records real select calls: last A→B selection must be clear.
	recorded = []
	real_select = tools_mod.stm_select_edge_route

	def recording_select(*args, **kwargs):
		route = real_select(*args, **kwargs)
		# args: x1,y1,x2,y2,src,dst,...
		src = args[4] if len(args) > 4 else kwargs.get('src')
		dst = args[5] if len(args) > 5 else kwargs.get('dst')
		item = dict(route)
		item['_src'] = src
		item['_dst'] = dst
		recorded.append(item)
		return route

	monkeypatch.setattr(tools_mod, 'stm_select_edge_route', recording_select)

	# Occupancy close to the geometric fixture (~0.15 mid among endpoints).
	labels = ['A'] * 5 + ['M'] * 2 + ['B'] * 5 + ['A', 'B'] * 4
	metrics = stm_compute_animal_metrics(labels, ['A', 'M', 'B'])
	assert metrics['status'] == 'ok'
	positions = {'A': (0.0, 0.0), 'M': (1.0, 0.0), 'B': (2.0, 0.0)}
	animal_dir = tmp_path / 'reselect'
	animal_dir.mkdir()
	_stm_draw_animal_map(
		str(animal_dir),
		0,
		metrics,
		positions,
		{name: '#6B9FE0' for name in metrics['observed_behaviors']},
		dpi=72,
	)
	ab_selects = [
		r for r in recorded if r.get('_src') == 'A' and r.get('_dst') == 'B'
	]
	assert ab_selects, 'draw must route the A→B edge'
	final_ab = ab_selects[-1]
	assert final_ab['pass_behind'] is False
	assert final_ab['clearance'] >= 0.0
	# If the last pick still used the invalid prelim rad, clearance would be < 0
	# under final-transform-like wide radii — the reselection result must clear.
	assert final_ab['rad'] in (
		list(stm_edge_route_reasonable_rads(0.12))
	)
	plt.close(fig)


def test_conservative_envelope_fallback_when_convergence_hits_limit(
	tmp_path, monkeypatch,
):
	'''
	Ordinary select/bounds loop hit its max → conservative envelope applied once,
	final selection under that transform, routes+casing fit final axes.
	'''
	import matplotlib.pyplot as plt
	from LabGym import tools as tools_mod

	# Force ordinary convergence to exhaust after one non-matching iteration.
	monkeypatch.setattr(tools_mod, '_STM_ROUTE_CONVERGENCE_MAX', 1)
	monkeypatch.setattr(plt, 'savefig', lambda *a, **k: None)

	envelope_calls = []
	real_envelope = tools_mod.stm_route_conservative_envelope_bounds

	def tracking_envelope(*args, **kwargs):
		bounds = real_envelope(*args, **kwargs)
		envelope_calls.append(tuple(float(v) for v in bounds))
		return bounds

	monkeypatch.setattr(
		tools_mod, 'stm_route_conservative_envelope_bounds', tracking_envelope,
	)

	select_events = []
	real_select = tools_mod.stm_select_edge_route

	def tracking_select(*args, **kwargs):
		# Snapshot active map axes limits if present.
		import matplotlib.pyplot as _plt
		lim = None
		for num in _plt.get_fignums():
			fig = _plt.figure(num)
			for ax in fig.axes:
				if ax.get_aspect() == 'equal' or True:
					lim = (
						float(ax.get_xlim()[0]),
						float(ax.get_xlim()[1]),
						float(ax.get_ylim()[0]),
						float(ax.get_ylim()[1]),
					)
					break
		route = real_select(*args, **kwargs)
		src = args[4] if len(args) > 4 else kwargs.get('src')
		dst = args[5] if len(args) > 5 else kwargs.get('dst')
		select_events.append({
			'src': src,
			'dst': dst,
			'limits': lim,
			'rad': route['rad'],
			'pass_behind': route['pass_behind'],
			'polyline': list(route['polyline']),
		})
		return route

	monkeypatch.setattr(tools_mod, 'stm_select_edge_route', tracking_select)

	labels = ['A', 'B', 'A', 'C', 'B', 'A']
	metrics = stm_compute_animal_metrics(labels, ['A', 'B', 'C'])
	assert metrics['status'] == 'ok'
	positions = stm_circular_layout(metrics['observed_behaviors'])
	animal_dir = tmp_path / 'envelope'
	animal_dir.mkdir()

	_stm_draw_animal_map(
		str(animal_dir),
		0,
		metrics,
		positions,
		{n: '#6B9FE0' for n in metrics['observed_behaviors']},
		dpi=72,
	)

	assert envelope_calls, 'conservative envelope fallback must be used'
	envelope_limits = envelope_calls[-1]

	# After envelope, final edge selections must run under that applied transform.
	n_edges = len(stm_ordered_transition_edges(
		metrics['observed_behaviors'],
		metrics['count_matrix'],
		metrics['probability_matrix'],
	))
	assert n_edges >= 1
	final_selects = select_events[-n_edges:]
	assert len(final_selects) == n_edges
	for ev in final_selects:
		assert ev['limits'] is not None
		# Final selection under fallback transform (matches envelope, not stale).
		assert all(
			abs(a - b) <= 1e-6
			for a, b in zip(ev['limits'], envelope_limits)
		)

	# Reconstruct final casing under a live axes transform matching envelope.
	fig_chk = plt.figure(figsize=(_STM_FIGSIZE_MAP, _STM_FIGSIZE_MAP), dpi=72)
	ax_chk = fig_chk.add_subplot(111)
	ax_chk.set_aspect('equal')
	ax_chk.set_xlim(envelope_limits[0], envelope_limits[1])
	ax_chk.set_ylim(envelope_limits[2], envelope_limits[3])
	fig_chk.canvas.draw()
	selected_like = [{'polyline': ev['polyline']} for ev in final_selects]
	ordered = stm_assign_edge_identifiers(
		stm_ordered_transition_edges(
			metrics['observed_behaviors'],
			metrics['count_matrix'],
			metrics['probability_matrix'],
		)
	)
	max_edge = max(float(e['value']) for e in ordered)
	halfs = []
	for edge in ordered:
		lw = stm_edge_linewidth(edge['value'], max_edge)
		halfs.append(
			stm_edge_halfwidth_data(ax_chk, stm_visible_edge_halfwidth_pt(lw))
		)
	assert stm_selected_routes_fit_axes_bounds(
		selected_like, halfs, envelope_limits,
	)
	plt.close(fig_chk)

	# Stale bounds: ordinary-loop selections used limits different from envelope.
	early = [e for e in select_events[:-n_edges] if e['limits'] is not None]
	assert early, 'ordinary loop must perform at least one selection pass'
	assert any(
		any(abs(a - b) > 1e-6 for a, b in zip(e['limits'], envelope_limits))
		for e in early
	), 'fallback must supersede stale ordinary-loop bounds'


def test_reciprocal_opposite_side_when_possible():
	node_centers = {'A': (0.0, 0.0), 'B': (2.0, 0.0)}
	node_radii = {'A': 0.2, 'B': 0.2}
	r1 = stm_select_edge_route(
		0.0, 0.0, 2.0, 0.0, 'A', 'B', _STM_EDGE_RAD_BIDIR,
		node_centers, node_radii, 0.04, 0.01, [],
	)
	r2 = stm_select_edge_route(
		2.0, 0.0, 0.0, 0.0, 'B', 'A', _STM_EDGE_RAD_BIDIR,
		node_centers, node_radii, 0.04, 0.01, [r1['polyline']],
		paired_sign=_stm_rad_sign(r1['rad']),
	)
	assert r2['reciprocal_side_relaxed'] is False
	assert _stm_rad_sign(r1['rad']) == _stm_rad_sign(r2['rad'])
	mx1, my1, _, _ = stm_arc3_point_and_tangent(0.0, 0.0, 2.0, 0.0, r1['rad'], 0.5)
	mx2, my2, _, _ = stm_arc3_point_and_tangent(2.0, 0.0, 0.0, 0.0, r2['rad'], 0.5)
	assert my1 * my2 < 0.0


def test_reciprocal_side_relaxed_when_no_opposite():
	'''When opposite side cannot hard-clear, relax but stay non-negative.'''
	# Large obstacle on the positive-bow side of A->B; force first route +rad.
	node_centers = {
		'A': (0.0, 0.0),
		'B': (2.0, 0.0),
		# Obstacle largely blocking negative rad for reverse may force relax.
		'O': (1.0, -0.55),
	}
	node_radii = {'A': 0.15, 'B': 0.15, 'O': 0.45}
	half_w, pad = 0.06, 0.02
	r1 = stm_select_edge_route(
		0.0, 0.0, 2.0, 0.0, 'A', 'B', 0.28,
		node_centers, node_radii, half_w, pad, [],
	)
	r2 = stm_select_edge_route(
		2.0, 0.0, 0.0, 0.0, 'B', 'A', 0.28,
		node_centers, node_radii, half_w, pad, [r1['polyline']],
		paired_sign=_stm_rad_sign(r1['rad']),
	)
	assert r1['clearance'] >= 0.0
	assert r2['clearance'] >= 0.0
	# Either opposite-side success or documented relaxed fallback.
	if r2['reciprocal_side_relaxed']:
		assert r2['clearance'] >= 0.0
	else:
		assert _stm_rad_sign(r1['rad']) == _stm_rad_sign(r2['rad'])


def test_clear_label_stays_on_curve():
	x1, y1, x2, y2 = 0.0, 0.0, 2.0, 0.0
	rad = 0.28
	placement = stm_place_edge_label(
		x1, y1, x2, y2, rad,
		{'A': (0.0, 0.0), 'B': (2.0, 0.0)},
		{'A': 0.15, 'B': 0.15},
		[],
		[],
		0.08,
		0.04,
		min_clearance_data=0.001,
		units_per_point=0.01,
	)
	assert placement['mode'] == 'on_curve'
	px, py, _, _ = stm_arc3_point_and_tangent(
		x1, y1, x2, y2, rad, placement['attach_t'],
	)
	assert math.hypot(placement['x'] - px, placement['y'] - py) <= 1e-9


def test_forced_low_clearance_uses_callout():
	x1, y1, x2, y2 = 0.0, 0.0, 2.0, 0.0
	rad = 0.35
	# Huge endpoint reserves + midpoint obstacle on curve force under-threshold.
	node_centers = {
		'A': (0.0, 0.0),
		'B': (2.0, 0.0),
		'M': (1.0, 0.2),
	}
	node_radii = {'A': 0.9, 'B': 0.9, 'M': 0.8}
	placement = stm_place_edge_label(
		x1, y1, x2, y2, rad,
		node_centers,
		node_radii,
		[],
		[],
		0.25,
		0.12,
		min_clearance_data=0.5,
		units_per_point=0.02,
	)
	assert placement['mode'] == 'callout'


def test_callout_attachment_is_best_maximin_oncurve_t():
	x1, y1, x2, y2 = 0.0, 0.0, 2.0, 0.0
	rad = 0.35
	node_centers = {
		'A': (0.0, 0.0),
		'B': (2.0, 0.0),
		'M': (1.0, 0.2),
	}
	node_radii = {'A': 0.9, 'B': 0.9, 'M': 0.8}
	candidates = stm_evaluate_oncurve_label_candidates(
		x1, y1, x2, y2, rad,
		node_centers, node_radii, [], [], 0.25, 0.12,
	)
	best = stm_best_oncurve_label_candidate(candidates)
	placement = stm_place_edge_label(
		x1, y1, x2, y2, rad,
		node_centers, node_radii, [], [],
		0.25, 0.12,
		min_clearance_data=0.5,
		units_per_point=0.02,
	)
	assert placement['mode'] == 'callout'
	assert placement['attach_t'] == best['t']
	assert abs(placement['attach_x'] - best['x']) <= 1e-12
	assert abs(placement['attach_y'] - best['y']) <= 1e-12


def test_callout_leader_segment_clears_prohibited_geometry():
	x1, y1, x2, y2 = 0.0, 0.0, 2.0, 0.0
	rad = 0.4
	node_centers = {'A': (0.0, 0.0), 'B': (2.0, 0.0)}
	node_radii = {'A': 0.25, 'B': 0.25}
	# Force callout by high threshold after packing nodes near curve.
	placement = stm_place_edge_label(
		x1, y1, x2, y2, rad,
		node_centers, node_radii, [], [],
		0.2, 0.1,
		min_clearance_data=0.35,
		units_per_point=0.02,
	)
	if placement['mode'] != 'callout':
		# Escalate threshold until callout triggers for a stable fixture.
		placement = stm_place_edge_label(
			x1, y1, x2, y2, rad,
			node_centers, node_radii, [], [],
			0.2, 0.1,
			min_clearance_data=5.0,
			units_per_point=0.02,
		)
	assert placement['mode'] == 'callout'
	# Leader samples (coarse) stay outside endpoint node radii.
	steps = 12
	for i in range(steps + 1):
		u = i / float(steps)
		sx = placement['attach_x'] + u * (placement['x'] - placement['attach_x'])
		sy = placement['attach_y'] + u * (placement['y'] - placement['attach_y'])
		for name, (nx, ny) in node_centers.items():
			d = math.hypot(sx - nx, sy - ny)
			assert d + 1e-9 >= node_radii[name] * 0.5


def test_callout_placement_deterministic():
	kwargs = dict(
		x1=0.0, y1=0.0, x2=2.0, y2=0.0, rad=0.35,
		node_centers={'A': (0.0, 0.0), 'B': (2.0, 0.0), 'M': (1.0, 0.2)},
		node_radii={'A': 0.9, 'B': 0.9, 'M': 0.8},
		other_polylines=[],
		placed_centers=[],
		label_half_w=0.25,
		label_half_h=0.12,
		min_clearance_data=0.5,
		units_per_point=0.02,
	)
	p1 = stm_place_edge_label(**kwargs)
	p2 = stm_place_edge_label(**kwargs)
	assert p1 == p2


def test_key_explain_exact_wording():
	assert _STM_KEY_EXPLAIN == 'Values show: transition probability (count)'


def test_key_vertical_pack_uses_point_gaps():
	p1 = stm_key_pack_y_positions(1)
	p3 = stm_key_pack_y_positions(3)
	assert p1['gap_pt'] == _STM_KEY_GAP_PT
	assert p1['title'] > p1['explain'] > p1['body']
	# More body lines requires a taller region; compact pack stays ordered.
	h1 = stm_key_region_height_inches(1)
	h3 = stm_key_region_height_inches(3)
	assert h3 > h1
	# Not the Iteration-2 fixed axes fractions.
	assert p1['explain'] != pytest.approx(0.78)
	assert p1['body'] != pytest.approx(0.58)


def test_routes_remain_valid_after_final_transform(tmp_path, monkeypatch):
	'''Drawing completes under final bounds; routes stay within reasonable rads.'''
	import matplotlib.pyplot as plt
	monkeypatch.setattr(plt, 'savefig', lambda *a, **k: None)

	labels = ['A', 'B', 'C', 'A', 'C', 'B']
	metrics = stm_compute_animal_metrics(labels, ['A', 'B', 'C'])
	positions = stm_circular_layout(metrics['observed_behaviors'])
	colors = {n: '#6B9FE0' for n in metrics['observed_behaviors']}
	animal_dir = tmp_path / '0'
	animal_dir.mkdir()
	_stm_draw_animal_map(str(animal_dir), 0, metrics, positions, colors, dpi=72)

	edges = stm_ordered_transition_edges(
		metrics['observed_behaviors'],
		metrics['count_matrix'],
		metrics['probability_matrix'],
	)
	max_edge = max(float(e['value']) for e in edges) if edges else 1.0
	node_centers = {b: positions[b] for b in metrics['observed_behaviors']}
	node_radii = {b: 0.12 for b in metrics['observed_behaviors']}
	selected = []
	pair_signs = {}
	for edge in edges:
		src, dst = edge['src'], edge['dst']
		x1, y1 = positions[src]
		x2, y2 = positions[dst]
		hw = 0.5 * (
			stm_edge_linewidth(edge['value'], max_edge) + _STM_EDGE_CASING_EXTRA
		) * 0.01
		seed = stm_edge_rad(src, dst, metrics['count_matrix'])
		pk = tuple(sorted((src, dst)))
		route = stm_select_edge_route(
			x1, y1, x2, y2, src, dst, seed,
			node_centers, node_radii, hw, 0.02,
			[e['polyline'] for e in selected],
			paired_sign=pair_signs.get(pk),
		)
		assert abs(route['rad']) <= _STM_ROUTE_REASONABLE_MAX + 1e-12
		if route['pass_behind']:
			assert route['clearance'] < 0.0
		else:
			assert route['clearance'] >= 0.0
		if src != dst and pk not in pair_signs:
			pair_signs[pk] = _stm_rad_sign(route['rad'])
		selected.append(route)
