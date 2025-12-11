"""Monkeypatch wx.App to be a strict-singleton.

Import this module before the first import of wx, to patch wx.App to be
a strict-singleton before an unpatched instance of wx.App can possibly
be created.
"""

# Allow use of newer syntax Python 3.10 type hints in Python 3.9.
from __future__ import annotations

# Standard library imports.
import logging
import sys
import textwrap

# Log the load of this module (by the module loader, on first import).
# Intentionally positioning these statements before other imports, against the
# guidance of PEP 8, to log the load before other imports log messages.
logger = logging.getLogger(__name__)
logger.debug('%s', f'loading {__name__}')

# Related third party imports.
# Verify the assumption that wx is not yet loaded, so there's been no
# opportunity to create an unpatched instance of wx.App, then import wx.
try:
	assert 'wx' not in sys.modules
	import wx
	patched = False
except AssertionError as e:
	# Rule out a false alarm by inspecting wx and finding its already patched.
	import wx
	if hasattr(wx, 'mywx_AppCount'):
		logger.warning('%s', textwrap.fill(textwrap.dedent(f"""\
			Weird, wx.App is already patched.  To the developer: Maybe
			this module ({__name__}) was loaded earlier under a
			different package name?  Consistency in the imports is
			recommended.  ({e!r})
			"""), width=400))
		patched = True
	else:
		raise

# Local application/library specific imports.
# None


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
			super().__init__(*args, **kwargs)
			self._initialized = True
			wx.mywx_AppCount += 1


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
		wx.mywx_AppCount += 1
		return cls._instance


if not patched:
	# monkeypatch wx.App
	wx.mywx_AppCount = 0
	wx.App = StrictSingleton
