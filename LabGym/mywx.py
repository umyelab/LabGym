"""
Monkeypatch wx.App, and provide wx utility functions and wx.Dialog subclasses.

Import this module before the first import of wx, to prevent multiple
instances of wx.App.

Public Functions
	bring_wxapp_to_foreground -- Bring the wx app to the foreground.

Public Classes
	OK_Dialog -- A wx.Dialog with left-aligned msg, and centered OK button.
	OK_Cancel_Dialog -- A wx.Dialog with left-aligned msg, and centered
		OK and Cancel buttons.

Example -- Import mywx before the first import of wx.
	If mywx is in a dir in sys.path, that is, mywx is not in a package,
		import mywx  # on load, monkeypatch wx.App to be a strict-singleton

	If mywx is inside a package "mypkg", then
		from mypkg import mywx  # on load, monkeypatch wx.App to be a strict-singleton

Example -- Display a modal dialog.  mywx is inside a package "mypkg"
	from mypkg import mywx  # on load, monkeypatch wx.App to be a strict-singleton
	import wx  # wxPython, Cross platform GUI toolkit for Python, "Phoenix" version

	# Dialog obj requires that the wx.App obj exists already.
	if not wx.GetApp():
		wx.App()
		mywx.bring_wxapp_to_foreground()

	# Show modal dialog.
	title = 'My Title'
	msg = 'My message'
	with mywx.OK_Dialog(None, title=title, msg=msg) as dlg:
		result = dlg.ShowModal()  # will return wx.ID_OK upon OK or dismiss

Notes
*   Why patch wx.App?  Because
	"wx.App is supposed to be used as a singleton.  It doesn't own the
	frames that are created in its OnInit, but instead assumes that it
	is supposed to manage and deliver events to all the windows that
	exist in the application."

*   "the OnInit is called during the construction of the App (after the
	toolkit has been initialized) not during the MainLoop call."

*   Why patch wx.App to be a "strict singleton" (that raises an
	exception on a second instantiation attempt) instead of a singleton
	that returns the existing instance?
	Because the intention is to prevent the misuse of wx (according to
	the third-party lib documentation), not to accommodate the misuse of
	wx.

*   Why use a new wx module attribute to indicate that App is patched,
	wouldn't this be sufficient to avoid an unpatched wx.App?
		import sys
		assert 'wx' not in sys.modules
		import wx
		(patch wx)
	No.  While that would work if this module were loaded/executed only
	once, it would raise a false alarm if loaded/executed a second time.

*   During development of a LabGym feature, more wx-related functions
	and classes are being parked in this module out of convenience, but
	there may be a better way to reorganize them after the feature code
	is stable.

History
	Originally, this module simply provided App, a function to guard
	from multiple instantiations of wx.App.
	But a weakness of that implementation is that it didn't prevent some
	future work calling wx.App() directly, instead of mywx.App().
	So it remained easy to inadventently bypass the intended protection.


------------------------------------------------------------------------
The loading of this module
	(a) loads wx for the first time, and
	(b) monkeypatches wx.App to be a "strict singleton", to prevent
		multiple instantiations.
or, if wx is already loaded, asserts that wx.App is already patched.

*   If wx has already been loaded, the import of this module will raise
	an exception.

*   Ensure that either (a) wx has not been loaded yet, and therefore no
	unpatched wx.App objects have been instantiated, or (b) this module
	is being loaded/executed again (!) but
------------------------------------------------------------------------
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
logger.debug('%s', f'loading {__name__} from {__file__}')

# Related third party imports.
if sys.platform == 'darwin':  # macOS
	# AppKit is from package pyobjc-framework-Cocoa, "Wrappers for the
	# Cocoa frameworks on macOS".
	from AppKit import NSApp, NSApplication

# Verify the assumption that wx is not yet loaded.
# If wx is already loaded, but wx.App is not patched, then raise  exception.
if 'wx' in sys.modules:
	import wx
	assert hasattr(wx, 'App_is_patched')
	patched = True
else:
	patched = False

import wx  # wxPython, Cross platform GUI toolkit for Python, "Phoenix" version

# Local application/library specific imports.
# (none)


class Singleton(wx.App):
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


class StrictSingleton(wx.App):
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


if not patched:
	# monkeypatch wx.App
	wx.App = StrictSingleton
	wx.App_is_patched = True


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
