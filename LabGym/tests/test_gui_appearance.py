"""Unit tests for LabGym.gui_appearance (no GUI window required)."""

from types import SimpleNamespace
from unittest.mock import MagicMock

from LabGym import mywx  # patch wx.App before any import of wx
import wx

from LabGym import gui_appearance


class _FakeColour:
	"""Minimal stand-in for wx.Colour with Red/Green/Blue accessors."""

	def __init__(self, r, g, b):
		self._r, self._g, self._b = r, g, b

	def Red(self):
		return self._r

	def Green(self):
		return self._g

	def Blue(self):
		return self._b


def test_is_dark_appearance_true_when_IsDark(monkeypatch):
	appearance = MagicMock()
	appearance.IsDark.return_value = True
	monkeypatch.setattr(wx.SystemSettings, 'GetAppearance', lambda: appearance)

	assert gui_appearance.is_dark_appearance() is True
	appearance.IsDark.assert_called_once()
	appearance.IsUsingDarkBackground.assert_not_called()


def test_is_dark_appearance_false_when_IsDark(monkeypatch):
	appearance = MagicMock()
	appearance.IsDark.return_value = False
	monkeypatch.setattr(wx.SystemSettings, 'GetAppearance', lambda: appearance)

	assert gui_appearance.is_dark_appearance() is False
	appearance.IsDark.assert_called_once()


def test_is_dark_appearance_falls_back_to_IsUsingDarkBackground(monkeypatch):
	"""Prefer IsDark; when absent, use IsUsingDarkBackground."""
	appearance = SimpleNamespace()
	# No IsDark attribute.
	appearance.IsUsingDarkBackground = MagicMock(return_value=True)
	monkeypatch.setattr(wx.SystemSettings, 'GetAppearance', lambda: appearance)

	assert gui_appearance.is_dark_appearance() is True
	appearance.IsUsingDarkBackground.assert_called_once()


def test_is_dark_appearance_falls_back_to_luminance_when_no_appearance_api(
		monkeypatch):
	"""Without GetAppearance, compare system window colours."""
	if hasattr(wx.SystemSettings, 'GetAppearance'):
		monkeypatch.delattr(wx.SystemSettings, 'GetAppearance')

	def fake_get_colour(index):
		if index == wx.SYS_COLOUR_WINDOW:
			return _FakeColour(30, 30, 30)  # dark bg
		if index == wx.SYS_COLOUR_WINDOWTEXT:
			return _FakeColour(220, 220, 220)  # light text
		return _FakeColour(128, 128, 128)

	monkeypatch.setattr(wx.SystemSettings, 'GetColour', fake_get_colour)

	assert gui_appearance.is_dark_appearance() is True


def test_is_dark_appearance_luminance_light(monkeypatch):
	if hasattr(wx.SystemSettings, 'GetAppearance'):
		monkeypatch.delattr(wx.SystemSettings, 'GetAppearance')

	def fake_get_colour(index):
		if index == wx.SYS_COLOUR_WINDOW:
			return _FakeColour(255, 255, 255)
		if index == wx.SYS_COLOUR_WINDOWTEXT:
			return _FakeColour(0, 0, 0)
		return _FakeColour(128, 128, 128)

	monkeypatch.setattr(wx.SystemSettings, 'GetColour', fake_get_colour)

	assert gui_appearance.is_dark_appearance() is False


def test_is_dark_appearance_IsDark_exception_then_IsUsingDarkBackground(
		monkeypatch):
	appearance = MagicMock()
	appearance.IsDark.side_effect = RuntimeError('unavailable')
	appearance.IsUsingDarkBackground.return_value = False
	monkeypatch.setattr(wx.SystemSettings, 'GetAppearance', lambda: appearance)

	assert gui_appearance.is_dark_appearance() is False
	appearance.IsUsingDarkBackground.assert_called_once()


def test_select_for_appearance_dark(monkeypatch):
	monkeypatch.setattr(gui_appearance, 'is_dark_appearance', lambda: True)
	assert gui_appearance.select_for_appearance('light', 'dark') == 'dark'


def test_select_for_appearance_light(monkeypatch):
	monkeypatch.setattr(gui_appearance, 'is_dark_appearance', lambda: False)
	assert gui_appearance.select_for_appearance('light', 'dark') == 'light'


def test_select_for_appearance_with_colours(monkeypatch):
	light = _FakeColour(255, 255, 255)
	dark = _FakeColour(20, 20, 20)
	monkeypatch.setattr(gui_appearance, 'is_dark_appearance', lambda: True)
	assert gui_appearance.select_for_appearance(light, dark) is dark

	monkeypatch.setattr(gui_appearance, 'is_dark_appearance', lambda: False)
	assert gui_appearance.select_for_appearance(light, dark) is light
