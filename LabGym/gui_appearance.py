'''
Copyright (C)
This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with this program. If not, see https://tldrlegal.com/license/gnu-general-public-license-v3-(gpl-3)#fulltext.

For license issues, please contact:

Dr. Bing Ye
Life Sciences Institute
University of Michigan
210 Washtenaw Avenue, Room 5403
Ann Arbor, MI 48109-2216
USA

Email: bingye@umich.edu
'''


'''Native appearance helpers for LabGym.

Reports whether the OS / wxPython effective appearance is dark so callers can
pick appearance-dependent values (e.g. colours). Does not implement a custom
theme, Light/Dark/System override, preference persistence, or widget recoloring.
'''

import wx


def _colour_luminance(colour) -> float:
	"""Return approximate relative luminance of a wx colour (0–255 scale)."""
	try:
		r, g, b = colour.Red(), colour.Green(), colour.Blue()
	except Exception:
		try:
			r, g, b = colour.Get()[:3]
		except Exception:
			return 128.0
	# ITU-R BT.601 luma coefficients, full 8-bit channel range.
	return 0.299 * r + 0.587 * g + 0.114 * b


def _is_dark_from_system_colours() -> bool:
	"""Infer dark appearance by comparing system window background vs text."""
	bg = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)
	fg = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT)
	return _colour_luminance(bg) < _colour_luminance(fg)


def is_dark_appearance() -> bool:
	"""Return True when the effective native wx appearance is dark.

	Detection order:
	1. ``wx.SystemSettings.GetAppearance().IsDark()`` when available.
	2. ``GetAppearance().IsUsingDarkBackground()`` when ``IsDark`` is missing
	   or raises (older / partial APIs).
	3. System window vs window-text luminance when the appearance API is
	   unavailable or fails.
	4. Light (``False``) as a final safe default.
	"""
	get_appearance = getattr(wx.SystemSettings, 'GetAppearance', None)
	if callable(get_appearance):
		try:
			appearance = get_appearance()
		except Exception:
			appearance = None

		if appearance is not None:
			is_dark = getattr(appearance, 'IsDark', None)
			if callable(is_dark):
				try:
					return bool(is_dark())
				except Exception:
					pass

			# Fallback / older builds: IsUsingDarkBackground without IsDark.
			is_using_dark_bg = getattr(appearance, 'IsUsingDarkBackground', None)
			if callable(is_using_dark_bg):
				try:
					return bool(is_using_dark_bg())
				except Exception:
					pass

	try:
		return bool(_is_dark_from_system_colours())
	except Exception:
		return False


def select_for_appearance(light_value, dark_value):
	"""Return ``dark_value`` under dark native appearance, else ``light_value``.

	Values may be ``wx.Colour`` instances or any other small appearance-dependent
	objects; this helper does not inspect or convert them.
	"""
	if is_dark_appearance():
		return dark_value
	return light_value
