"""AF regression: Workflow Map client-size transform (no live GUI windows)."""

from LabGym.gui_utils import compute_workflow_map_transform


def test_map_transform_uses_client_size():
	cw, ch, scale, ox, oy = compute_workflow_map_transform(1100, 560)
	assert cw == 1100 and ch == 560
	assert abs(scale - min(1100 / 2200, 560 / 660)) < 1e-9
	assert abs(ox - (1100 - 2200 * scale) / 2) < 1e-9
	assert abs(oy - (560 - 660 * scale) / 2) < 1e-9


def test_map_transform_tiny_client_falls_back():
	cw, ch, scale, ox, oy = compute_workflow_map_transform(0, 0)
	assert cw == 1100 and ch == 560
	assert scale > 0
