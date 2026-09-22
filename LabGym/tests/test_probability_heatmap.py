"""Probability heat-map missing-value masking (non-detector and detector)."""

import math
import os

import matplotlib
matplotlib.use('Agg')

from matplotlib.axes import Axes
from matplotlib.colors import LogNorm, to_rgba
import matplotlib.pyplot as plt
import numpy as np
import pytest

from LabGym.analyzebehavior import (
	PROBABILITY_HEATMAP_FLOOR,
	PROBABILITY_HEATMAP_MISSING_COLOR,
	PROBABILITY_HEATMAP_MISSING_LEGEND,
	AnalyzeAnimal,
	prepare_probability_heatmap_array,
	probability_heatmap_colormap,
)
from LabGym.analyzebehavior_dt import AnalyzeAnimalDetector


def _capture_imshow(monkeypatch):
	captured = {}
	real_imshow = Axes.imshow

	def wrapper(self, X, *args, **kwargs):
		captured['X'] = X
		captured['kwargs'] = kwargs
		captured['self'] = self
		return real_imshow(self, X, *args, **kwargs)

	monkeypatch.setattr(Axes, 'imshow', wrapper)
	return captured


def _non_detector_analyzer(tmp_path, walk_probs, sit_probs, times=None):
	times = list(range(len(walk_probs))) if times is None else times
	animal = AnalyzeAnimal()
	animal.results_path = str(tmp_path)
	animal.all_time = times
	animal.event_probability = {0: None}
	animal.all_behavior_parameters = {
		'walk': {'probability': {0: walk_probs}},
		'sit': {'probability': {0: sit_probs}},
	}
	return animal


def _detector_analyzer(tmp_path, walk_probs, sit_probs, times=None):
	times = list(range(len(walk_probs))) if times is None else times
	animal = AnalyzeAnimalDetector()
	animal.results_path = str(tmp_path)
	animal.all_time = times
	animal.event_probability = {'mouse': {0: None}}
	animal.all_behavior_parameters = {
		'mouse': {
			'walk': {'probability': {0: walk_probs}},
			'sit': {'probability': {0: sit_probs}},
		}
	}
	return animal


def test_nan_and_nonfinite_are_masked_not_floored():
	raw = np.array([[np.nan, np.inf, -np.inf, 0.2]], dtype=np.float64)
	prepared = prepare_probability_heatmap_array(raw)
	assert np.ma.is_masked(prepared)
	assert prepared.mask[0, 0]
	assert prepared.mask[0, 1]
	assert prepared.mask[0, 2]
	assert not prepared.mask[0, 3]
	assert prepared[0, 3] == pytest.approx(0.2)
	np.testing.assert_array_equal(raw, [[np.nan, np.inf, -np.inf, 0.2]])


def test_finite_floor_value_is_not_missing():
	raw = np.array([[PROBABILITY_HEATMAP_FLOOR, 0.0, 1.5]], dtype=np.float64)
	prepared = prepare_probability_heatmap_array(raw)
	assert not np.any(prepared.mask)
	assert prepared[0, 0] == pytest.approx(PROBABILITY_HEATMAP_FLOOR)
	assert prepared[0, 1] == pytest.approx(PROBABILITY_HEATMAP_FLOOR)
	assert prepared[0, 2] == pytest.approx(1.0)


def test_finite_values_keep_lognorm_mapping():
	raw = np.array([[0.001, 0.01, 0.1, 1.0]], dtype=np.float64)
	prepared = prepare_probability_heatmap_array(raw)
	norm = LogNorm(vmin=1e-3, vmax=1)
	mapped = [float(norm(v)) for v in prepared.compressed()]
	assert mapped[0] == pytest.approx(0.0)
	assert mapped[-1] == pytest.approx(1.0)
	assert mapped == sorted(mapped)
	assert math.isclose(mapped[1], norm(0.01))
	assert math.isclose(mapped[2], norm(0.1))


def test_colormap_bad_is_gray_and_does_not_mutate_global():
	inferno = plt.get_cmap('inferno')
	before = inferno.get_bad().copy()
	cmap = probability_heatmap_colormap()
	after = inferno.get_bad()
	np.testing.assert_array_equal(before, after)
	expected_bad = np.array(to_rgba(PROBABILITY_HEATMAP_MISSING_COLOR))
	np.testing.assert_allclose(cmap.get_bad(), expected_bad)
	assert PROBABILITY_HEATMAP_MISSING_COLOR == 'gray'


def _assert_plotted_missing_and_floor(captured):
	plotted = captured['X']
	assert np.ma.is_masked(plotted)
	# After transpose: behaviors x frames. walk is row 0.
	assert plotted.mask[0, 1]
	assert not plotted.mask[0, 0]
	assert plotted[0, 0] == pytest.approx(PROBABILITY_HEATMAP_FLOOR)
	assert not plotted.mask[1, 0]
	assert plotted[1, 0] == pytest.approx(0.2)
	norm = captured['kwargs']['norm']
	assert isinstance(norm, LogNorm)
	assert float(norm.vmin) == pytest.approx(1e-3)
	assert float(norm.vmax) == pytest.approx(1.0)
	cmap = captured['kwargs']['cmap']
	expected_bad = np.array(to_rgba(PROBABILITY_HEATMAP_MISSING_COLOR))
	np.testing.assert_allclose(cmap.get_bad(), expected_bad)
	legend_labels = [t.get_text() for t in captured['self'].get_legend().get_texts()]
	assert PROBABILITY_HEATMAP_MISSING_LEGEND in legend_labels


def test_non_detector_heatmap_masks_nan_and_keeps_floor(tmp_path, monkeypatch):
	captured = _capture_imshow(monkeypatch)
	animal = _non_detector_analyzer(
		tmp_path,
		walk_probs=[0.001, np.nan, 0.4],
		sit_probs=[0.2, 0.8, 1.0],
		times=[0.0, 0.1, 0.2],
	)
	animal.export_probability_matrices(make_heatmap=True)
	_assert_plotted_missing_and_floor(captured)


def test_detector_heatmap_follows_same_missing_rule(tmp_path, monkeypatch):
	captured = _capture_imshow(monkeypatch)
	animal = _detector_analyzer(
		tmp_path,
		walk_probs=[0.001, np.nan, 0.4],
		sit_probs=[0.2, 0.8, 1.0],
		times=[0.0, 0.1, 0.2],
	)
	animal.export_probability_matrices_dt(make_heatmap=True)
	_assert_plotted_missing_and_floor(captured)


def test_saved_numeric_matrices_unchanged_by_plotting(tmp_path):
	walk = [0.001, np.nan, 0.4]
	sit = [0.2, np.inf, 1.0]
	expected = np.array([walk, sit], dtype=np.float32).T

	true_dir = tmp_path / 'heat'
	false_dir = tmp_path / 'noheat'
	true_dir.mkdir()
	false_dir.mkdir()

	a_true = _non_detector_analyzer(true_dir, walk, sit, times=[0.0, 0.1, 0.2])
	a_false = _non_detector_analyzer(false_dir, walk, sit, times=[0.0, 0.1, 0.2])
	a_true.export_probability_matrices(make_heatmap=True)
	a_false.export_probability_matrices(make_heatmap=False)

	loaded_true = np.load(os.path.join(str(true_dir), 'probability_matrix_ID0.npy'))
	loaded_false = np.load(os.path.join(str(false_dir), 'probability_matrix_ID0.npy'))
	np.testing.assert_array_equal(loaded_true, expected)
	np.testing.assert_array_equal(loaded_false, expected)
	csv_true = np.genfromtxt(
		os.path.join(str(true_dir), 'probability_matrix_ID0.csv'),
		delimiter=',',
		names=True,
		)
	assert np.isnan(csv_true['walk'][1])

	d_true = _detector_analyzer(true_dir / 'dt', walk, sit, times=[0.0, 0.1, 0.2])
	(true_dir / 'dt').mkdir()
	d_true.export_probability_matrices_dt(make_heatmap=True)
	loaded_dt = np.load(os.path.join(str(true_dir / 'dt'), 'mouse_probability_matrix_ID0.npy'))
	np.testing.assert_array_equal(loaded_dt, expected)


def test_stride_downsampling_unchanged(tmp_path, monkeypatch):
	captured = _capture_imshow(monkeypatch)
	n = 10
	walk = [0.2] * n
	sit = [0.3] * n
	times = [i * 0.1 for i in range(n)]
	max_frames = 4
	expected_stride = int(np.ceil(n / max_frames))
	assert expected_stride == 3
	expected_frames = len(np.arange(n)[::expected_stride])

	animal = _non_detector_analyzer(tmp_path / 'nd', walk, sit, times=times)
	(tmp_path / 'nd').mkdir()
	animal.export_probability_matrices(make_heatmap=True, max_frames_for_heatmap=max_frames)
	assert captured['X'].shape[1] == expected_frames
	loaded = np.load(os.path.join(str(tmp_path / 'nd'), 'probability_matrix_ID0.npy'))
	assert loaded.shape == (n, 2)

	dt = _detector_analyzer(tmp_path / 'dt', walk, sit, times=times)
	(tmp_path / 'dt').mkdir()
	dt.export_probability_matrices_dt(make_heatmap=True, max_frames_for_heatmap=max_frames)
	assert captured['X'].shape[1] == expected_frames
	loaded_dt = np.load(os.path.join(str(tmp_path / 'dt'), 'mouse_probability_matrix_ID0.npy'))
	assert loaded_dt.shape == (n, 2)
