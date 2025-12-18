import importlib
import logging
import os
import re
import sys
import time

from packaging import version

# Deliberately importing __main__ inside test functions instead of here.
# Why?  Because (1) must patch mylogging.configure before importing
# __main__, (2) want to time the import and report that duration from a
# test function (duration is significant, ~30 sec?).
# from LabGym import __main__

# But, it's possible that detectron2 has been loaded already, without cv2!
# which produces errors...
#     FAILED ... - ModuleNotFoundError: import of cv2 halted; None in sys.modules
# in which case, import cv2.
# if 'cv2' in sys.modules and sys.modules['cv2'] is None:
#     del sys.modules['cv2']
#     import cv2
#     # if detectron2 isn't loaded yet, don't foul up cv2 on load.
#     os.environ['DETECTRON2_DISABLE_CV2'] = '0'  # use '0' for False here.

import pytest


logger = logging.getLogger(__name__)


def test_main(monkeypatch):
	# Arrange
	# patch configure, in mylogging, *before* importing __main__
	from LabGym import mylogging
	monkeypatch.setattr(mylogging, 'configure', lambda *args: None)

	from LabGym import __main__
	monkeypatch.setattr(__main__.probes, 'probes', lambda: None)
	monkeypatch.setattr(__main__.gui_main, 'main_window', lambda: None)

	monkeypatch.setattr(__main__.wx, 'GetApp', lambda: None)
	monkeypatch.setattr(__main__.wx, 'App', lambda: None)

	monkeypatch.setattr(__main__.config, 'get_config', lambda: {'selftest': False})

	# Act
	__main__.main()

	# Assert... not needed.
	# This unit test passes if __main__.main doesn't raise an exception.


def test_main_current_labgym(monkeypatch):
	# Arrange
	# patch configure, in mylogging, *before* importing __main__
	from LabGym import mylogging
	monkeypatch.setattr(mylogging, 'configure', lambda *args: None)

	from LabGym import __main__
	return_values = [
		version.Version('2.8.16'),  # version of LabGym here
		version.Version('2.8.16'),  # version of LabGym at pypi.org
		]
	monkeypatch.setattr(__main__.version, 'parse', lambda self: return_values.pop(0))

	monkeypatch.setattr(__main__.probes, 'probes', lambda: None)
	monkeypatch.setattr(__main__.gui_main, 'main_window', lambda: None)

	monkeypatch.setattr(__main__.wx, 'GetApp', lambda: None)
	monkeypatch.setattr(__main__.wx, 'App', lambda: None)

	monkeypatch.setattr(__main__.config, 'get_config', lambda: {'selftest': False})

	# Act
	__main__.main()

	# Assert... not needed.
	# This unit test passes if __main__.main doesn't raise an exception.


def test_main_stale_labgym(monkeypatch):
	# Arrange
	# patch configure, in mylogging, *before* importing __main__
	from LabGym import mylogging
	monkeypatch.setattr(mylogging, 'configure', lambda *args: None)

	from LabGym import __main__
	return_values = [
		version.Version('2.8.16'),  # version of LabGym here
		version.Version('2.9.0'),  # version of LabGym at pypi.org
		]
	monkeypatch.setattr(__main__.version, 'parse', lambda self: return_values.pop(0))

	monkeypatch.setattr(__main__.probes, 'probes', lambda: None)
	monkeypatch.setattr(__main__.gui_main, 'main_window', lambda: None)

	monkeypatch.setattr(__main__.wx, 'GetApp', lambda: None)
	monkeypatch.setattr(__main__.wx, 'App', lambda: None)

	monkeypatch.setattr(__main__.config, 'get_config', lambda: {'selftest': False})

	# Act
	__main__.main()

	# Assert... not needed.
	# This unit test passes if __main__.main doesn't raise an exception.


# from .exitstatus import exitstatus
#
# # Specify sys.argv before importing __main__.  Why?  Because the
# # loading of my __main__ is sensitive to the contents of sys.argv, which
# # is initialized the pytest command and args.
# sys.argv = ['cmd', '--verbose']
# T0 = time.time()
# import LabGym.__main__  # Time consuming... (typical 24 sec, 25 sec, 34 sec)
# sys.loadtime = time.time() - T0
#
# def test_inspect():
#     logging.debug(f'sys.argv: {sys.argv!r}')
#     logging.debug(f'load time for import __main__: {sys.loadtime:.0f} seconds')
#     logging.debug(f'LabGym.__main__.logrecords: {LabGym.__main__.logrecords!r}')
#
#     for rec in LabGym.__main__.logrecords:
#         # logging.debug(f'dir(rec): {dir(rec)}')
#         assert rec.msg == '%s'
#         assert len(rec.args) == 1
#         print(f'{rec.levelname} {rec.args[0]}')
#
#
# def test_main(monkeypatch):
#     monkeypatch.setattr('LabGym.__main__.gui_main.main_window', lambda: None)
#     LabGym.__main__.main()
#
#
# def x_test_moduleload(monkeypatch):
#     """This doesn't seem to reload everything, since loadtime is typical 0.000222 sec."""
#
#     logging.debug(f'sys.argv: {sys.argv!r}')
#     T0 = time.time()
#     try:
#         logging.debug('reloading LabGym.__main__')
#         importlib.reload(LabGym.__main__)
#     except NameError as e:
#         logging.debug('importing LabGym.__main__')
#         import LabGym.__main__
#     loadtime = time.time() - T0
#
#     logging.debug(f'LabGym.__main__.logrecords: {LabGym.__main__.logrecords!r}')
#     # logging.debug(f'load time for import __main__: {loadtime:.0f} seconds')
#     logging.debug(f'load time for import __main__: {loadtime:f} seconds')
