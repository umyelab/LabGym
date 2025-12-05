import logging
import os
from pathlib import Path
import re
import sys
import time

import pytest  # pytest: simple powerful testing with Python

from LabGym import mywx  # on load, monkeypatch wx.App to be a singleton
import wx  # wxPython, Cross platform GUI toolkit for Python, "Phoenix" version

from LabGym import userdata_survey


# testdir = Path(__file__[:-3])  # dir containing support files for unit tests
# assert testdir.is_dir()


# @pytest.fixture(scope="module")  # invoke once in the test module
# def wx_app():
#     # setup logic
#     app = wx.App()
#
#     yield app
#
#     # teardown logic
#     # Ensure a graceful shutdown of a wxPython application by deferring
#     # the exit of the main event loop until the current event handling
#     # is complete.
#     wx.CallAfter(app.ExitMainLoop)
#     app.MainLoop()  # Ensure app processes pending events before exit.
#
#     del app
#     wx.App._instance = None


def test_dummy():
	# Arrange
	# Act
	pass
	# Assert not necessary.  This unit test passes unless exception was raised.


def test_is_path_under():
	assert userdata_survey.is_path_under('/a/b', '/a/b/c') == True
	assert userdata_survey.is_path_under('/a/b', '/a/b/c/d') == True
	assert userdata_survey.is_path_under('/a/b', '/a/c/../b/d') == True

	assert userdata_survey.is_path_under('/a/b', '/a/b') == False

	assert userdata_survey.is_path_under('/a/b/c', '/a/b') == False
	assert userdata_survey.is_path_under('/a/b', '/a/c') == False
	assert userdata_survey.is_path_under('/a/b', '/a/b/../c') == False


def test_is_path_equivalent():
	assert userdata_survey.is_path_equivalent('/a/b', '/a/b') == True

	assert userdata_survey.is_path_equivalent('/a/b', '/a/c') == False
