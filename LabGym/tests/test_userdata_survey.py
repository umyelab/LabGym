import logging
import os
from pathlib import Path
import re
import sys
import textwrap
import time

import pytest  # pytest: simple powerful testing with Python

from LabGym import mywx  # on load, monkeypatch wx.App to be a singleton
import wx  # wxPython, Cross platform GUI toolkit for Python, "Phoenix" version

from LabGym import userdata_survey
from .exitstatus import exitstatus


# testdir = Path(__file__[:-3])  # dir containing support files for unit tests
# assert testdir.is_dir()

@pytest.fixture(scope="module")  # invoke once in the test module
def wx_app():
	# setup logic
	app = wx.App()

	yield app

	# teardown logic
	# Ensure a graceful shutdown of a wxPython application by deferring
	# the exit of the main event loop until the current event handling
	# is complete.
	wx.CallAfter(app.ExitMainLoop)
	app.MainLoop()  # Ensure app processes pending events before exit.

	del app
	wx.App._instance = None


delay = 2000  # msec


class AutoclickOK(mywx.OK_Dialog):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		# set a delayed click...
		wx.CallLater(delay, self.click_ok)
	def click_ok(self):
		click_event = wx.CommandEvent(wx.EVT_BUTTON.typeId, wx.ID_OK)
		self.ProcessEvent(click_event)

def test_dummy():
	# Arrange
	# Act
	pass
	# Assert (optional).  This unit test passes unless exception was raised.


def test_is_path_under():

	# path1 and path2 are equivalent
	assert userdata_survey.is_path_under('/a/b', '/a/b') == False
	assert userdata_survey.is_path_under('/a/b', '/a/b/..') == False

	# path2 is under path1
	assert userdata_survey.is_path_under('/a/b', '/a/b/c') == True
	assert userdata_survey.is_path_under('/a/b', '/a/b/c/d') == True
	assert userdata_survey.is_path_under('/a/b', '/a/c/../b/d') == True

	# path2 is not under path1
	assert userdata_survey.is_path_under('/a/b/c', '/a/b') == False
	assert userdata_survey.is_path_under('/a/b', '/a/c') == False
	assert userdata_survey.is_path_under('/a/b', '/a/b/../c') == False


def test_is_path_equivalent():
	# path1 and path2 are equivalent
	assert userdata_survey.is_path_equivalent('/a/b', '/a/b') == True

	# path1 and path2 are not equivalent
	assert userdata_survey.is_path_equivalent('/a/b', '/a/c') == False


def test_resolve():
	result = userdata_survey.resolve('.')
	assert Path(result).is_absolute()


# def dict2str(arg: dict, hanging_indent: str=' '*16) -> str:
def test_dict2str():
	myarg = {}
	assert userdata_survey.dict2str(myarg) == ''

	# In Python, all standard dictionaries (dict) are ordered by
	# insertion order starting from Python 3.7.

	myarg = {'a': 'A', 'c': 'C', 'b': 'B'}
	hanging_indent = ' ' * 16
	expected = textwrap.dedent(f"""\
		a: A
		{hanging_indent}c: C
		{hanging_indent}b: B
		""").strip()
	result = userdata_survey.dict2str(myarg)
	assert result == expected

	myarg = {'a': 'A', 'c': 'C', 'b': 'B'}
	hanging_indent = ' ' * 2
	expected = textwrap.dedent(f"""\
		a: A
		{hanging_indent}c: C
		{hanging_indent}b: B
		""").strip()
	result = userdata_survey.dict2str(myarg, hanging_indent=hanging_indent)
	assert result == expected


# def get_list_of_subdirs(parent_dir: str|Path) -> List[str]:
def test_get_list_of_subdirs(tmp_path):
	(Path(tmp_path) / 'alfa').mkdir()
	(Path(tmp_path) / 'bravo').mkdir()
	(Path(tmp_path) / 'charlie').mkdir()
	(Path(tmp_path) / '__pycache__').mkdir()
	(Path(tmp_path) / '__init__.py').touch()

	expected = ['alfa', 'bravo', 'charlie']
	result = userdata_survey.get_list_of_subdirs(tmp_path)
	assert result == expected


# def assert_userdata_dirs_are_separate(
def test_assert_userdata_dirs_are_separate(
		monkeypatch, tmp_path, wx_app, caplog):
	"""Violate the assertion by passing in equivalent path1 & path2."""

	# Arrange
	# Use a custom self- OK-ing subclass of the dialog object.
	monkeypatch.setattr(userdata_survey.mywx, 'OK_Dialog', AutoclickOK)

	# Act
	with pytest.raises(SystemExit,
			match="Bad configuration"
			) as e:
		userdata_survey.assert_userdata_dirs_are_separate(tmp_path, tmp_path)

	# Assert
	assert exitstatus(e.value) == 1

	expected_msg = textwrap.dedent("""
		LabGym Configuration Error
		The userdata folders must be separate.
		""").strip()
	assert expected_msg in caplog.text


# def survey(
def test_survey_case1(monkeypatch, tmp_path, wx_app, caplog):
	"""violate check 1, and get SystemExit."""
	# Arrange
	# Use a custom self- OK-ing subclass of the dialog object.
	monkeypatch.setattr(userdata_survey.mywx, 'OK_Dialog', AutoclickOK)
	monkeypatch.setattr(userdata_survey.config, 'get_config',
		lambda: {'enable': {'assess_userdata_folders': True}})

	# prepare args
	labgym = os.path.join(tmp_path, 'LabGym')
	detectors = os.path.join(tmp_path, 'detectors')
	models = os.path.join(tmp_path, 'detectors', 'models')

	# Act
	with pytest.raises(SystemExit,
			match="Bad configuration"
			) as e:
		userdata_survey.survey(labgym, detectors, models)

	# Assert
	assert exitstatus(e.value) == 1

	expected_msg = textwrap.dedent("""
		LabGym Configuration Error
		The userdata folders must be separate.
		""").strip()
	assert expected_msg in caplog.text


def test_survey_case2(monkeypatch, tmp_path, wx_app, caplog):
	"""violate check 2, and get Warning."""
	# Arrange
	# Use a custom self- OK-ing subclass of the dialog object.
	monkeypatch.setattr(userdata_survey.mywx, 'OK_Dialog', AutoclickOK)
	monkeypatch.setattr(userdata_survey.config, 'get_config',
		lambda: {'enable': {'assess_userdata_folders': True}})

	# prepare args
	labgym = os.path.join(tmp_path, 'LabGym')
	detectors = os.path.join(tmp_path, 'detectors')
	models = os.path.join(tmp_path, 'models')

	# Act
	userdata_survey.survey(labgym, detectors, models)

	# Assert
	expected_msg = \
		"External Userdata folders specified by config don't exist."
	assert expected_msg in caplog.text


def test_survey_case3(monkeypatch, tmp_path, wx_app, caplog):
	"""violate check 3, and get Warning."""
	# Arrange
	# Use a custom self- OK-ing subclass of the dialog object.
	monkeypatch.setattr(userdata_survey.mywx, 'OK_Dialog', AutoclickOK)
	monkeypatch.setattr(userdata_survey.config, 'get_config',
		lambda: {'enable': {'assess_userdata_folders': True}})

	# prepare args
	labgym = os.path.join(tmp_path, 'LabGym')
	detectors = os.path.join(tmp_path, 'LabGym', 'detectors')
	models = os.path.join(tmp_path, 'LabGym', 'models')

	# Act
	userdata_survey.survey(labgym, detectors, models)

	# Assert
	expected_msg = "Found internal Userdata folders specified by config."
	assert expected_msg in caplog.text


def test_survey_case4(monkeypatch, tmp_path, wx_app, caplog):
	"""violate check 4, and get Warning."""
	# Arrange
	# Use a custom self- OK-ing subclass of the dialog object.
	monkeypatch.setattr(userdata_survey.mywx, 'OK_Dialog', AutoclickOK)
	monkeypatch.setattr(userdata_survey.config, 'get_config',
		lambda: {'enable': {'assess_userdata_folders': True}})

	# prepare args
	labgym = os.path.join(tmp_path, 'LabGym')
	detectors = os.path.join(tmp_path, 'detectors')
	models = os.path.join(tmp_path, 'models')
	# create the external userdata dirs
	os.mkdir(detectors)
	os.mkdir(models)

	# create four orphan userdata dirs
	orphans = [
		os.path.join(labgym, 'detectors', 'detector1'),
		os.path.join(labgym, 'detectors', 'detector2'),
		os.path.join(labgym, 'detectors', '__pycache__'),

		os.path.join(labgym, 'models', 'model1'),
		os.path.join(labgym, 'models', 'model2'),
		os.path.join(labgym, 'models', '__pycache__'),
		]
	for orphan in orphans:
		os.makedirs(orphan)

	# also create some files which are not reported by this check...
	(Path(labgym)/'detectors'/'__init__.py').touch()
	(Path(labgym)/'models'/'__init__.py').touch()

	# Act
	userdata_survey.survey(labgym, detectors, models)

	# Assert
	print(caplog.text)
	expected_msg = 'Found Userdata orphaned in old Userdata folders.'
	assert expected_msg in caplog.text
