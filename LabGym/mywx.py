"""
Monkeypatch wx.App, and provide wx utility functions and wx.Dialog subclasses.

Originally, this module simply provided App, a function to guard from
multiple instantiations of wx.App.
But I'm not seeing a good way to ensure that wx.App isn't used directly
in some future development work, defeating the protection.
So now ...

Load this module to monkeypatch wx.App to prevent multiple instances.

The loading of this module
	(a) loads wx for the first time, and
	(b) monkeypatches wx.App to prevent multiple instances.

Usage
	import mywx  # on load, monkeypatch wx.App to be a singleton

During development of a LabGym feature, more wx-related functions and
classes are being parked in this module out of convenience, but there
may be a better way to reorganize them after the feature code is stable.

Public Functions
	bring_wxapp_to_foreground -- Bring the wx app to the foreground.

Public Classes
	OK_Dialog -- A wx.Dialog with left-aligned msg, and centered OK button.
	OK_Cancel_Dialog -- A wx.Dialog with left-aligned msg, and centered
		OK and Cancel buttons.

Why patch wx.App?  Because
	"wx.App is supposed to be used as a singleton.  It doesn't own the
	frames that are created in its OnInit, but instead assumes that it
	is supposed to manage and deliver events to all the windows that
	exist in the application."

"the OnInit is called during the construction of the App (after the
toolkit has been initialized) not during the MainLoop call."
"""

# Allow use of newer syntax Python 3.10 type hints in Python 3.9.
from __future__ import annotations

# Standard library imports.
import logging
import sys

# Log the load of this module (by the module loader, on first import).
# Intentionally positioning these statements before other imports, against the
# guidance of PEP-8, to log the load before other imports log messages.
logger =  logging.getLogger(__name__)
logger.debug('loading %s', __file__)

# Related third party imports.
if sys.platform == 'darwin':  # macOS
	# AppKit is from package pyobjc-framework-Cocoa, "Wrappers for the
	# Cocoa frameworks on macOS".
	from AppKit import NSApp, NSApplication
# Verify the assumption that wx is not yet loaded.
assert sys.modules.get('wx') is None
import wx  # wxPython, Cross platform GUI toolkit for Python, "Phoenix" version

# Local application/library specific imports.
# (none)


class Patch_A(wx.App):
	_instance = None  # Class variable to hold the single instance

	def __new__(cls, *args, **kwargs):
		logger.debug('patched __new__ -- entered')
		if cls._instance is None:
			logger.debug('patched __new__ -- instantiating')
			cls._instance = super().__new__(cls)
		logger.debug(f'patched __new__ -- returning {cls._instance}')
		return cls._instance

	def __init__(self, *args, **kwargs):
		logger.debug('patched __init__ -- entered')
		if not hasattr(self, '_initialized'):
			logger.debug('patched __init__ -- initializing')
			super().__init__(self, *args, **kwargs)
			self._initialized = True


class Patch_B(wx.App):
	_instance = None  # Class variable to hold the single instance

	def __new__(cls, *args, **kwargs):
		logger.debug('patched __new__ -- entered')
		if cls._instance is None:
			logger.debug('patched __new__ -- instantiating')
			cls._instance = super().__new__(cls)
		else:
			raise AssertionError('wx.App() is called once at most.')
		logger.debug(f'patched __new__ -- returning {cls._instance}')
		return cls._instance


# monkeypatch wx.App
wx.App = Patch_B


# def App():
#     """Return the wx.App object.
#
#     To ensure that only one wx.App object is instantiated, developers
#     may use this function instead of calling wx.App().
#
#     *   If wx.App was called before the first call to this function,
#         then raise an exception.
#     *   If wx.App is called after the first call to this function,
#         then raise an exception.
#     """
#
#     return wx.App()

#     global _cached_app
#
#     if _cached_app is not None:
#         return _cached_app
#
#     # Milestone -- This must be the first time running this function.
#
#     # If wx.GetApp() shows that wx.App was called before the first call
#     # to this function, then raise an exception.  But wx.GetApp is an
#     # imperfect indicator... if wx is already fouled, then wx.GetApp()
#     # may return None.
#     if wx.GetApp():
#         raise AssertionError('wx.App() is called once at most.')
#
#     # wx.GetApp() returned None, so either
#     # (a) this will be the # first call to wx.App(), or,
#     # (b) wx is already fouled and this call to # wx.App() will crash like
#     #         objc[88558]: Invalid or prematurely-freed autorelease pool 0x7f8bb28113e0.
#
#     # Construct the app obj, cache it
#     logger.debug('wx.App() -- Calling')
#     app = wx.App()
#     logger.debug('%s: %r', 'app', app)
#
#     _cached_app = app
#
#     # If wx.App is called after the first call to this function,
#     # then raise an exception.
#     # Implement this future behavior by monkeypatching/sabotaging
#     # the __new__ method.
#
#     # wx.App.__new__ = lambda *args, **kwargs: (
#     #     raise AssertionError('wx.App() is called once at most.'))
#
#     def _raise(e):
#         raise e
#     wx.App.__new__ = lambda *args, **kwargs: _raise(
#         AssertionError('wx.App() is called once at most.'))
#
#     return app


def bring_wxapp_to_foreground() -> None:
	"""Bring the wx app to the foreground.

	We want the wx app displayed to the user, not initially obscured by
	windows from other apps.

	On macOS 12.7, with LabGym started from terminal, I'm seeing:
	*   the registration dialog is displayed, but doesn't have focus
		and is under the windows of the active app (terminology?),
		potentially hidden completely.
	*   a bouncing python rocketship icon in the tray.  The bouncing
		stops when you mouseover the icon.  Also some other actions
		can stop the bouncing or just pause the bouncing... weird.

	I wasn't able to resolve this undesirable behavior on macOS using
	the wx.Dialog object's Raise, SetFocus, and Restore methods.
	Instead, this approach worked for me...
		"Calling NSApp().activateIgnoringOtherApps_(True) via AppKit:
		This macOS workaround uses the AppKit module to explicitly
		activate the application, ignoring other running applications.
		This is typically done after your wxPython application has
		started and its main window is shown."
	"""

	if sys.platform == 'darwin':  # macOS
		NSApplication.sharedApplication()
		NSApp().activateIgnoringOtherApps_(True)


class OK_Dialog(wx.Dialog):
	"""An OK dialog object, with the message text left-aligned.

	Why use a custom class instead of using wx.MessageDialog?
	Because left-alignment of the message is preferred, and a
	wx.MessageDialog cannot be customized to control the alignment of
	its message text or buttons.

	(class purpose and functionality, and optionally its attributes and methods)
	"""

	def __init__(self, parent, title='', msg=''):
		super().__init__(parent, title=title)

		panel = wx.Panel(self)
		main_sizer = wx.BoxSizer(wx.VERTICAL)

		# Add the msg
		main_sizer.Add(wx.StaticText(panel, label=msg),
			0,  # proportion (int).  0 means the item won't expand
				# beyond its minimal size.

			# border on all sides, and align left
			wx.ALL | wx.LEFT,

			10,  # width (in pixels) of the borders specified
			)

		# Create sizers for layout.
		button_sizer = wx.StdDialogButtonSizer()

		# Create buttons, Add buttons to sizers, and Bind event handlers
		self.add_buttons(panel, button_sizer)

		# Realize the sizer to apply platform-specific layout
		button_sizer.Realize()

		# Add the button sizer to the main sizer
		main_sizer.Add(button_sizer, 0, wx.ALL | wx.EXPAND, 10)

		panel.SetSizer(main_sizer)
		main_sizer.Fit(self)
		# self.SetSizerAndFit(main_sizer)  # is this equivalent??

	def add_buttons(self, panel, button_sizer):
		"""Create and add buttons to sizers, and bind event handlers.

		Create standard buttons with their respective IDs.
		Add buttons to the StdDialogButtonSizer.
		Bind event handlers for the buttons.
		"""
		# Create/Add/Bind for the OK button
		ok_button = wx.Button(panel, wx.ID_OK)
		button_sizer.AddButton(ok_button)
		self.Bind(wx.EVT_BUTTON, self.on_ok, id=wx.ID_OK)

	def on_ok(self, event):
		self.EndModal(wx.ID_OK)


class OK_Cancel_Dialog(OK_Dialog):
	"""An OK/Cancel dialog object, with the message text left-aligned."""

	def add_buttons(self, panel, button_sizer):
		# Create/Add/Bind for the OK button
		super().add_buttons(panel, button_sizer)

		# Create/Add/Bind for the Cancel button
		cancel_button = wx.Button(panel, wx.ID_CANCEL)
		button_sizer.AddButton(cancel_button)
		self.Bind(wx.EVT_BUTTON, self.on_cancel, id=wx.ID_CANCEL)

	def on_cancel(self, event):
		self.EndModal(wx.ID_CANCEL)
