"""
Monkeypatch wx.App, and provide wx utility functions and wx.Dialog subclasses.

Import this package before the first import of wx, to patch wx.App to be
a strict-singleton before an unpatched instance of wx.App can possibly
be created.

Example -- Display a modal dialog.  In this example, mywx is a
subpackage of mypkg (not in a dir in sys.path).
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
*   Why patch wx.App?
	Because it's easy to misuse, producing delayed consequences that may
	be difficult to diagnose.

	Scraped on 2025-12-10 from wxPython 4.2.3 documentation
	https://docs.wxpython.org/wx.App.html
		The wx.App class represents the application and is used to:
		*   bootstrap the wxPython system and initialize the underlying
			gui toolkit
		*   set and get application-wide properties
		*   implement the native windowing system main message or event
			loop, and to dispatch events to window instances
		*   etc.

		Every wx application must have a single wx.App instance, and all
		creation of UI objects should be delayed until after the wx.App
		object has been created in order to ensure that the gui platform
		and wxWidgets have been fully initialized.

		Normally you would derive from this class and implement an
		OnInit method that creates a frame and then calls
		self.SetTopWindow(frame), however wx.App is also usable on its
		own without derivation.

	Scraped on 2025-12-10 from wxPython discussion
	https://discuss.wxpython.org/t/two-wx-app-instances-one-appx-mainloop-runs-both-app-instances/24934
		wx.App is supposed to be used as a singleton.  It doesn't own
		the frames that are created in its OnInit, but instead assumes
		that it is supposed to manage and deliver events to all the
		windows that exist in the application.

*   Why patch wx.App to be a "strict singleton" (that raises an
	exception on a second instantiation attempt) instead of a singleton
	that returns the existing instance?
	Because the intention is to prevent the misuse of wx (according to
	the lib documentation), not to accommodate the misuse of wx.

*   During development of a feature, more wx-related functions and
	classes are being parked in mywx.custom out of convenience, but
	there may be a better way to reorganize them after the feature code
	is stable.
"""

# Standard library imports.
import logging

# Log the load of this module (by the module loader, on first import).
# Intentionally positioning these statements before other imports, against the
# guidance of PEP 8, to log the load before other imports log messages.
logger = logging.getLogger(__name__)
logger.debug('%s', f'loading {__name__}')

# Related third party imports.
# None

# Local application/library specific imports.
# On load of this package, import/load .patch, which monkeypatches wx.App.
from . import patch

# Expose custom functions and classes as attributes of this package.
from .custom import (
	bring_wxapp_to_foreground,
	OK_Dialog,
	OK_Cancel_Dialog,
	)
