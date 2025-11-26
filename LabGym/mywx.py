"""Provide some wx utility functions and some wx.Dialog subclasses.

Originally, this module simply provided App, a function to guard from
multiple instantiations of wx.App.
During development of userdata_survey, more wx-related functions and
classes are being parked in this module, but there may be a better way
to reorganize them after userdata_survey is stable.

Public Functions
	App -- Return the wx.App object.
	bring_wxapp_to_foreground -- Bring the wx app to the foreground.

Public Classes
	OK_Dialog -- A wx.Dialog with left-aligned msg, and centered OK button.
	OK_Cancel_Dialog -- A wx.Dialog with left-aligned msg, and centered
		OK and Cancel buttons.

Usage for mywx.App
	import mywx
	app = mywx.App()
or
	import mywx
	mywx.App()
instead of
	import wx
	app = wx.App()
for added protection against creating two wx.App objects at once.

This implementation uses the common approach of using a module-level
variable to store the value after its initial creation.
This pattern is often referred to as memoization or lazy initialization.

A side benefit of this implementation is that a reference to object
is preserved (as module variable _cached_app), so it doesn't get garbage
collected when used like
	import mywx
	mywx.App()

Note that mywx.App could be implemented as a subclass of wx.App instead
of a function.  It would use a custom __new__ method to guard against
creating multiple instances, and a custom __init__ method to guard
against re-initializing the singleton object.
If a custom OnInit method was desired, the scales would be tipped in
favor of the subclass implementation over the function implementation.

"wx.App is supposed to be used as a singleton.  It doesn't own the
frames that are created in its OnInit, but instead assumes that it is
supposed to manage and deliver events to all the windows that exist in
the application."

"the OnInit is called during the construction of the App (after the
toolkit has been initialized) not during the MainLoop call."
"""

# Allow use of newer syntax Python 3.10 type hints in Python 3.9.
from __future__ import annotations

# Standard library imports.
import logging
import sys

# Related third party imports.
if sys.platform == 'darwin':  # macOS
	# AppKit is from package pyobjc-framework-Cocoa, "Wrappers for the
	# Cocoa frameworks on macOS".
	from AppKit import NSApp, NSApplication
import wx  # wxPython, Cross platform GUI toolkit for Python, "Phoenix" version

# Local application/library specific imports.
# (none)


logger = logging.getLogger(__name__)

_cached_app = None


def App():
	"""Return the wx.App object."""

	global _cached_app

	if _cached_app is not None:
		return _cached_app

	# Milestone -- This must be the first time running this function.
	# Construct the app obj, cache it, and return it.

	_cached_app = app
	return app


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

	I wasn't able to resolve this on macOS using the wx.Dialog object's
	Raise, SetFocus, and Restore methods.
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
	def add_buttons(self, panel, button_sizer):
		# Create/Add/Bind for the OK button
		super().add_buttons(panel, button_sizer)

		# Create/Add/Bind for the Cancel button
		cancel_button = wx.Button(panel, wx.ID_CANCEL)
		button_sizer.AddButton(cancel_button)
		self.Bind(wx.EVT_BUTTON, self.on_cancel, id=wx.ID_CANCEL)

	def on_cancel(self, event):
		self.EndModal(wx.ID_CANCEL)
