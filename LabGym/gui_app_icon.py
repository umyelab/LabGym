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

'''GUI application icon module for LabGym.
This module provides cross-platform icon handling functionality for the LabGym
GUI, including support for different icon formats (ICO, ICNS, PNG) and
contexts (normal, small).
'''
# Standard library imports.
import sys
import logging
from pathlib import Path
from importlib.resources import files
from functools import lru_cache
if sys.platform.startswith("win"):
	import ctypes

# Related third party imports.
import wx
if sys.platform == "darwin":
	try:
		from AppKit import NSApplication, NSImage
	except ImportError:
		NSApplication = None


logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_icon_paths():
	"""Get all icon paths once and cache them."""
	base_path = files("LabGym") / "assets/icons"
	return {
		'small_ico': base_path / "labgym_small.ico",
		'main_ico': base_path / "labgym.ico", 
		'icns': base_path / "labgym.icns",
		'png': base_path / "labgym.png"
	}


def get_icon_for_context(context='normal', size=16):
	"""Get appropriate icon path for given context and size."""
	icon_paths = _get_icon_paths()
	
	if sys.platform.startswith("win"):
		# Windows: Use ICO files for better compatibility
		if context == 'small' or size <= 24:
			return str(icon_paths['small_ico']) if icon_paths['small_ico'].is_file() else str(icon_paths['png'])
		else:
			return str(icon_paths['main_ico']) if icon_paths['main_ico'].is_file() else str(icon_paths['png'])
	
	# macOS or fallback
	return str(icon_paths['png']) if icon_paths['png'].is_file() else ""


def set_frame_icon(frame, context='normal', size=16):
	"""Set frame icon with proper error handling."""
	try:
		icon_path = get_icon_for_context(context, size)
		if not icon_path or not Path(icon_path).is_file():
			logger.warning("Icon file not found: %s", icon_path)
			return
			
		icon = wx.Icon(icon_path, wx.BITMAP_TYPE_ANY)
		if icon.IsOk():
			frame.SetIcon(icon)
			logger.info("Set frame icon: %s", icon_path)
		else:
			logger.warning("Failed to create valid wx.Icon from %s", icon_path)
	except Exception as e:
		logger.warning("Failed to set frame icon: %r", e)


def set_windows_taskbar_icon():
	"""Set the Windows taskbar icon.
	Set the Windows taskbar icon using small ICO for better small-size
	visibility.
	"""
	if not sys.platform.startswith("win"):
		return
	try:
		# Set AppUserModelID first - this is crucial for proper taskbar icon association
		app_id = "umyelab.LabGym.1.0"
		ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
		logger.info("Set Windows AppUserModelID to: %s", app_id)
	except Exception as e:
		logger.warning("Failed to set Windows taskbar icon: %r", e)


def set_macos_dock_icon():
	"""Set the Dock icon on macOS.
	Set the Dock icon at runtime on macOS (requires optional PyObjC).
	"""
	if sys.platform != "darwin" or not NSApplication:
		return
	try:
		baseIconDir = files("LabGym")
		icns = baseIconDir / "assets/icons/labgym.icns"
		png = baseIconDir / "assets/icons/labgym.png"

		icon_path = str(icns if icns.is_file() else png)
		img = NSImage.alloc().initWithContentsOfFile_(icon_path)
		if img:
			NSApplication.sharedApplication().setApplicationIconImage_(img)
			logger.info("Set macOS dock icon: %s", icon_path)
		else:
			logger.warning("NSImage failed to load dock icon from %s", icon_path)
	except Exception as e:
		logger.warning("Dock icon set failed: %r", e)


def setup_application_icons():
	"""Set up all application icons for the current platform."""
	set_macos_dock_icon()  # no-op on non-macOS or if no PyObjC
	set_windows_taskbar_icon()  # no-op on non-Windows, uses small ICO
	
	# Log icon usage for debugging
	if sys.platform.startswith("win"):
		logger.info("Windows: Using small ICO for title bar contexts")
