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
		import tempfile
		from pathlib import Path
		import shutil
		
		# Set the WM_CLASS property for better icon association
		app = wx.GetApp()
		if app:
			# Set application name for better desktop integration
			app.SetAppDisplayName("LabGym")
			
		# Try to use the PNG icon for better Linux compatibility
		icon_path = get_icon_for_context(context='dock', size=32)
		if icon_path and Path(icon_path).is_file():
			try:
				# Also copy the icon to the user's icon theme directory for robustness
				icon_theme_dir = Path.home() / ".local" / "share" / "icons" / "hicolor" / "48x48" / "apps"
				icon_theme_dir.mkdir(parents=True, exist_ok=True)

				icon_dest = icon_theme_dir / "labgym.png"
				if Path(icon_path).exists():
					shutil.copy2(icon_path, icon_dest)
					logger.info("Copied icon to theme directory: %s", icon_dest)
				else:
					# Fallback if icon source is missing for some reason
					icon_dest = "application-x-executable"
				# Create a temporary desktop file for better dock integration
				# This helps desktop environments like GNOME/Unity recognize the application
				desktop_content = f"""[Desktop Entry]
Name=LabGym
Comment=LabGym - Animal Behavior Analysis
Exec=python3 -m LabGym
Icon={icon_dest}
Type=Application
Categories=Science;Biology;
StartupWMClass=LabGym
"""
				
				# Create temporary desktop file
				with tempfile.NamedTemporaryFile(mode='w', suffix='.desktop', delete=False) as f:
					f.write(desktop_content)
					temp_desktop = f.name
				
				# Make it executable
				os.chmod(temp_desktop, 0o755)
				
				# Try to install it to user applications directory
				user_apps_dir = Path.home() / ".local" / "share" / "applications"
				user_apps_dir.mkdir(parents=True, exist_ok=True)
				
				desktop_dest = user_apps_dir / "labgym.desktop"
				if desktop_dest.exists():
					desktop_dest.unlink()  # Remove existing file
				
				# Copy the desktop file
				shutil.copy2(temp_desktop, desktop_dest)
				
				# Clean up temp file
				os.unlink(temp_desktop)
				
				# Update desktop database and force icon cache refresh
				try:
					import subprocess
					logger.debug("Attempting to update desktop database...")
					result = subprocess.run(['update-desktop-database', str(user_apps_dir)],
								  capture_output=True, timeout=5, check=False)
					if result.returncode != 0:
						logger.warning("update-desktop-database failed: %s", result.stderr.decode('utf-8', 'ignore'))
					else:
						logger.debug("update-desktop-database succeeded.")

					# Force icon cache refresh for GTK
					# The icon directory is ~/.local/share/icons
					gtk_icon_cache_dir = Path.home() / ".local" / "share" / "icons"
					logger.debug("Attempting to update GTK icon cache for %s", gtk_icon_cache_dir)
					result = subprocess.run(['gtk-update-icon-cache', '-f', '-t', str(gtk_icon_cache_dir)],
								  capture_output=True, timeout=5, check=False)
					if result.returncode != 0:
						logger.warning("gtk-update-icon-cache failed: %s", result.stderr.decode('utf-8', 'ignore'))
					else:
						logger.debug("gtk-update-icon-cache succeeded.")

				except (subprocess.TimeoutExpired, FileNotFoundError) as e:
					logger.warning("Failed to run desktop update commands: %s", e)
				
				# Also try to set the icon directly on the window
				try:
					# Get the main frame and set its class name for better matching
					app = wx.GetApp()
					if app and app.GetTopWindow():
						frame = app.GetTopWindow()
						# Set window class name to match desktop file
						frame.SetName("LabGym")
						# Force a window refresh
						frame.Refresh()
				except Exception:
					pass
				
				logger.info("Linux dock icon setup completed with desktop file: %s", desktop_dest)
				
			except Exception as e:
				logger.debug("Desktop file creation failed: %r", e)
				logger.info("Linux dock icon setup completed (basic): %s", icon_path)
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
