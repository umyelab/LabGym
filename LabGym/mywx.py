"""Provide function to guard from multiple instantiations of wx.App

Use
	import mywx
	app = mywx.App()
or
	import mywx
	mywx.App()
instead of
	import wx
	app = wx.App()
to avoid creating two wx.App objects at once.

This implementation uses the common approach of using a module-level
variable to store the value after its initial creation.
This pattern is often referred to as memoization or lazy initialization.

A side benefit of this implementation is that a reference to object
is preserved (as module variable _cached_app), so it doesn't get garbage
collected when used like
	import mywx
	mywx.App()

"wx.App is supposed to be used as a singleton.  It doesn't own the
frames that are created in its OnInit, but instead assumes that it is
supposed to manage and deliver events to all the windows that exist in
the application."

"the OnInit is called during the construction of the App (after the
toolkit has been initialized) not during the MainLoop call."
"""

import logging

import wx


logger = logging.getLogger(__name__)


_cached_app = None


def App():
	"""Return the wx.App object."""

	global _cached_app

	if _cached_app is not None:
		return _cached_app

	# Milestone -- This must be the first time running this function.
	# Construct the app obj, cache it, and return it.

	app = wx.App()
	logger.debug('%s: %r', 'app', app)

	_cached_app = app
	return app
