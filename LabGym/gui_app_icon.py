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
This module provides cross-platform icon handling for the LabGym GUI using one
simplified LabGym artwork set (ICO on Windows, PNG elsewhere, ICNS on macOS Dock).
'''
# Standard library imports.
import logging
import sys
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
		NSImage = None

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_icon_paths():
	"""Get all icon paths once and cache them."""
	base_path = files("LabGym") / "assets/icons"
	return {
		'ico': base_path / "labgym.ico",
		'icns': base_path / "labgym.icns",
		'png': base_path / "labgym.png",
	}


def get_frame_icon_path():
	"""Return the platform-appropriate path for wx frame icons.

	Windows uses the multi-resolution labgym.ico. macOS and other platforms
	use the matching labgym.png.
	"""
	icon_paths = _get_icon_paths()

	if sys.platform.startswith("win"):
		if icon_paths['ico'].is_file():
			return str(icon_paths['ico'])
		if icon_paths['png'].is_file():
			return str(icon_paths['png'])
		return ""

	# macOS and non-Windows fallback
	if icon_paths['png'].is_file():
		return str(icon_paths['png'])
	return ""


def set_frame_icon(frame):
	"""Set the frame icon from the unified simplified artwork."""
	try:
		icon_path = get_frame_icon_path()
		if not icon_path or not Path(icon_path).is_file():
			logger.warning('Frame icon asset not found')
			return

		icon = wx.Icon(icon_path, wx.BITMAP_TYPE_ANY)
		if icon.IsOk():
			frame.SetIcon(icon)
		else:
			logger.warning('Failed to load frame icon from %s', icon_path)
	except Exception:
		logger.exception('Error setting frame icon')


def set_windows_app_user_model_id():
	"""Establish Windows process/taskbar identity via AppUserModelID.

	Call this early (before the first visible window) when practical.
	This does not embed an executable icon; it only sets runtime process
	identity used by the shell for taskbar grouping.
	"""
	if not sys.platform.startswith("win"):
		return
	try:
		app_id = "umyelab.LabGym"
		ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
	except Exception:
		logger.exception('Failed to set Windows AppUserModelID')


# Backward-compatible name used by older call sites.
set_windows_taskbar_icon = set_windows_app_user_model_id


def set_macos_dock_icon():
	"""Set the Dock icon on macOS for unbundled runs (optional PyObjC)."""
	if sys.platform != "darwin" or not NSApplication:
		return
	try:
		icon_paths = _get_icon_paths()
		if icon_paths['icns'].is_file():
			icon_path = str(icon_paths['icns'])
		elif icon_paths['png'].is_file():
			icon_path = str(icon_paths['png'])
		else:
			logger.warning('macOS Dock icon asset not found')
			return

		img = NSImage.alloc().initWithContentsOfFile_(icon_path)
		if img:
			NSApplication.sharedApplication().setApplicationIconImage_(img)
		else:
			logger.warning('Failed to load macOS Dock icon from %s', icon_path)
	except Exception:
		logger.exception('Error setting macOS Dock icon')


def setup_application_icons():
	"""Set up process/Dock icons for the current platform.

	Safe to call more than once. Prefer an early call before the first
	visible window so Windows AppUserModelID is established first.
	"""
	set_windows_app_user_model_id()
	set_macos_dock_icon()
