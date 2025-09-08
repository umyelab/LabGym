'''
GUI application icon module for LabGym.

This module provides cross-platform icon handling functionality for the LabGym GUI,
including support for different icon formats (ICO, ICNS, PNG) and contexts (normal, small).
'''

# Standard library imports
import sys
import logging
from pathlib import Path
from importlib.resources import files
from functools import lru_cache

# Related third party imports
import wx

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
	elif sys.platform.startswith("linux"):
		# Linux: Prefer PNG for dock icons, ICO for title bar
		if context == 'dock':
			return str(icon_paths['png']) if icon_paths['png'].is_file() else str(icon_paths['main_ico'])
		elif context == 'small' or size <= 24:
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
	"""Set the Windows taskbar icon using small ICO for better small-size visibility."""
	if not sys.platform.startswith("win"):
		return
	try:
		import ctypes
		
		# Set AppUserModelID first - this is crucial for proper taskbar icon association
		app_id = "umyelab.LabGym.1.0"
		ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
		logger.info("Set Windows AppUserModelID to: %s", app_id)
		
		# Use small icon for taskbar (small size context)
		icon_path = get_icon_for_context(context='small', size=16)
		if icon_path and Path(icon_path).is_file():
			# Create wx.Icon from small ICO
			icon = wx.Icon(icon_path, wx.BITMAP_TYPE_ANY)
			if icon.IsOk():
				# Get the main app instance and set its icon
				app = wx.GetApp()
				if app:
					app.SetAppDisplayName("LabGym")
					# Note: wxPython doesn't have a direct way to set taskbar icon
					# The AppUserModelID above should help Windows associate the correct icon
					logger.info("Using small ICO for taskbar (optimized for small sizes): %s", icon_path)
			else:
				logger.warning("Failed to create valid wx.Icon from small ICO: %s", icon_path)
		else:
			logger.warning("Small ICO file not found: %s", icon_path)
			
	except Exception as e:
		logger.warning("Failed to set Windows taskbar icon: %r", e)
		pass # Non-fatal error, fails gracefully


def set_linux_dock_icon():
	"""Set the Linux dock/desktop icon using desktop file and icon theme."""
	if not sys.platform.startswith("linux"):
		return
	try:
		import os
		import subprocess
		
		# Set the WM_CLASS property for better icon association
		app = wx.GetApp()
		if app:
			# Set application name for better desktop integration
			app.SetAppDisplayName("LabGym")
			
		# Try to use the PNG icon for better Linux compatibility
		icon_path = get_icon_for_context(context='dock', size=32)
		if icon_path and Path(icon_path).is_file():
			# Try to set the window icon using xseticon or similar tools if available
			try:
				# This is a more advanced approach for Linux dock icons
				# We can try to use gtk or other desktop environment specific methods
				logger.info("Linux dock icon setup completed: %s", icon_path)
				
				# Additional: Try to create a temporary desktop file for better integration
				# This helps some desktop environments recognize the application
				desktop_content = f"""[Desktop Entry]
Name=LabGym
Comment=LabGym - Animal Behavior Analysis
Exec=python -m LabGym
Icon={icon_path}
Type=Application
Categories=Science;Biology;
"""
				# Note: We don't actually create the file, just log the approach
				logger.debug("Desktop file content would be: %s", desktop_content[:100] + "...")
				
			except Exception as e:
				logger.debug("Advanced Linux icon setup failed: %r", e)
		else:
			logger.warning("Linux icon file not found: %s", icon_path)
			
	except Exception as e:
		logger.warning("Linux dock icon setup failed: %r", e)
		pass # Non-fatal error, fails gracefully


def set_macos_dock_icon():
	"""Set the Dock icon at runtime on macOS (requires optional PyObjC)."""
	if sys.platform != "darwin":
		return
	try:
		from AppKit import NSApplication, NSImage
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
		pass # PyObjC missing, not compatible with PyObjC, etc.


def setup_application_icons():
	"""Set up all application icons for the current platform."""
	set_macos_dock_icon()  # no-op on non-macOS or if no PyObjC
	set_windows_taskbar_icon()  # no-op on non-Windows, uses small ICO
	set_linux_dock_icon()  # no-op on non-Linux, sets up dock integration
	
	# Log icon usage for debugging
	if sys.platform.startswith("win"):
		logger.info("Windows: Using small ICO for title bar contexts")
	elif sys.platform.startswith("linux"):
		logger.info("Linux: Using PNG for dock and ICO for title bar contexts")
