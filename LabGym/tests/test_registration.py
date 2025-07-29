import logging
import os
from pathlib import Path
import re
import sys
import time

import pytest  # pytest: simple powerful testing with Python
import wx  # wxPython, Cross platform GUI toolkit for Python, "Phoenix" version

from LabGym import registration


testdir = Path(__file__[:-3])  # dir containing support files for unit tests
assert testdir.is_dir()


# @pytest.fixture(scope="module")  # invoke once in the test module
@pytest.fixture()
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


def test_dummy():
    # Arrange
    # Act
    pass
    # Assert not necessary.  This unit test passes unless exception was raised.


def test_mydialog_skip(wx_app):
    frame = wx.Frame(None)  # parent for the dialog
    dialog = registration.RegFormDialog(frame)

    # def click_register():
    def click_skip():
        click_event = wx.CommandEvent(wx.EVT_BUTTON.typeId, wx.ID_CANCEL)
        dialog.ProcessEvent(click_event)

    # CallAfter is a function used to schedule a callable to be executed
    # on the main GUI thread after the current event hander and any
    # pending event handlers have completed.
    # wx.CallAfter(click_skip)
    wx.CallLater(1000, click_skip)

    # The ShowModal() method is used to display a dialog box in a 
    # "modal" fashion.  When a modal dialog is shown, it blocks user 
    # interaction with other windows in the application until the modal
    # dialog is dismissed (closed by the user).
    result = dialog.ShowModal()

    # Assert
    assert result == wx.ID_CANCEL

    # Teardown
    dialog.Destroy()  # request the dialog to self-destruct


def test_mydialog_register(wx_app):
    frame = wx.Frame(None)  # parent for the dialog
    dialog = registration.RegFormDialog(frame)

    def click_register():
        click_event = wx.CommandEvent(wx.EVT_BUTTON.typeId, wx.ID_OK)
        dialog.ProcessEvent(click_event)

    def click_skip():
        click_event = wx.CommandEvent(wx.EVT_BUTTON.typeId, wx.ID_CANCEL)
        dialog.ProcessEvent(click_event)

    def enter_name():
        dialog.input_name.SetValue('Mark Wilson')
    def enter_affiliation():
        dialog.input_affiliation.SetValue('Cupertino')
    def enter_email():
        dialog.input_email.SetValue('Mark.Wilson@gmail.com')

    # CallAfter is a function used to schedule a callable to be executed
    # on the main GUI thread after the current event hander and any
    # pending event handlers have completed.
    # Use CallAfter to interact with the dialog *after* it's been shown.
    # This allows the dialog to become active before test code attempts
    # to interact with it.
    # wx.CallAfter(click_register)
    wx.CallLater(1000, enter_name)  # delay in ms
    wx.CallLater(2000, enter_affiliation)  # delay in ms
    wx.CallLater(3000, enter_email)  # delay in ms
    wx.CallLater(5000, click_register)  # delay in ms

    # The ShowModal() method is used to display a dialog box in a 
    # "modal" fashion.  When a modal dialog is shown, it blocks user 
    # interaction with other windows in the application until the modal
    # dialog is dismissed (closed by the user).
    result = dialog.ShowModal()

    # Assert
    assert result == wx.ID_OK

    # Teardown
    dialog.Destroy()  # request the dialog to self-destruct


def test__get_reginfo_from_form(monkeypatch, wx_app, tmp_path):

    # frame = wx.Frame(None)  # parent for the dialog
    # dialog = registration.RegFormDialog(frame)

    def click_register(dialog_obj):
        click_event = wx.CommandEvent(wx.EVT_BUTTON.typeId, wx.ID_OK)
        dialog_obj.ProcessEvent(click_event)

    def click_skip(dialog_obj):
        click_event = wx.CommandEvent(wx.EVT_BUTTON.typeId, wx.ID_CANCEL)
        dialog_obj.ProcessEvent(click_event)

    def enter_name(dialog_obj):
        dialog_obj.input_name.SetValue('Paul Baker')
    def enter_affiliation(dialog_obj):
        dialog_obj.input_affiliation.SetValue('Cupertino')
    def enter_email(dialog_obj):
        dialog_obj.input_email.SetValue('Paul.Baker@gmail.com')

    # CallAfter is a function used to schedule a callable to be executed
    # on the main GUI thread after the current event hander and any
    # pending event handlers have completed.
    # Use CallAfter to interact with the dialog *after* it's been shown.
    # This allows the dialog to become active before test code attempts
    # to interact with it.
    # wx.CallAfter(click_register)

    # wx.CallLater(1000, enter_name, h)  # delay in ms
    # wx.CallLater(2000, enter_affiliation, h)  # delay in ms
    # wx.CallLater(3000, enter_email, h)  # delay in ms
    # wx.CallLater(5000, click_register, h)  # delay in ms

    monkeypatch.setattr(registration.wx, 'App', lambda: None)
    h = registration.RegFormDialog(None)
    monkeypatch.setattr(registration, 'RegFormDialog', lambda arg1: h)

    wx.CallLater(1000, enter_name, h)  # delay in ms
    wx.CallLater(2000, enter_affiliation, h)  # delay in ms
    wx.CallLater(3000, enter_email, h)  # delay in ms
    wx.CallLater(5000, click_register, h)  # delay in ms
    
    # this works, but why not run registration itself?
    # reginfo = registration._get_reginfo_from_form()
    _config = {
        'configdir': tmp_path,
        }
    monkeypatch.setattr(registration.config, 'get_config', lambda: _config)
    logging.debug('%s: %r', '_config', _config)

    registration.register(logging.getLogger())

    # The ShowModal() method is used to display a dialog box in a 
    # "modal" fashion.  When a modal dialog is shown, it blocks user 
    # interaction with other windows in the application until the modal
    # dialog is dismissed (closed by the user).
    # result = dialog.ShowModal()

    # Assert
    # assert result == wx.ID_OK

    # Teardown
    # dialog.Destroy()  # request the dialog to self-destruct


def test_get_reginfo_from_file(monkeypatch):
    # Arrange
    _config = {
        'configdir': testdir,
        }
    monkeypatch.setattr(registration.config, 'get_config', lambda: _config)
    logging.debug('%s: %r', '_config', _config)

    # Act
    result = registration.get_reginfo_from_file()
    # Assert
    assert result.get('schema') == 'reginfo 2025-07-10'


def test_is_registered(monkeypatch, tmp_path):
    # Arrange
    _config = {
        'configdir': tmp_path,
        }
    monkeypatch.setattr(registration.config, 'get_config', lambda: _config)
    logging.debug('%s: %r', '_config', _config)

    # Act
    result = registration.is_registered()
    # Assert
    assert result == False


# basicConfig here isn't effective, maybe pytest has already configured logging?
#   logging.basicConfig(level=logging.DEBUG)
# so instead, use the root logger's setLevel method
logging.getLogger().setLevel(logging.DEBUG)

# the output from this debug statement is not accessible?
# instead, perform inside a test function.
#   logging.debug('%s: %r', 'dir(LabGym)', dir(LabGym))
#
# def test_inspect():
#     logging.debug('%s: %r', 'dir(LabGym)', dir(LabGym))
#     logging.debug('%s: %r', "os.getenv('PYTHONPATH')", os.getenv('PYTHONPATH'))


def x_test_probes(monkeypatch):
    # Arrange
    _config = {
        'anonymous': True, 
        'enable': {'registration': False, 'central_logger': False},
        }
    monkeypatch.setattr(probes.config, 'get_config', lambda: _config)
    logging.debug('%s: %r', '_config', _config)
    monkeypatch.setattr(probes.central_logging.config, 'get_config', lambda: _config)

    # Act
    probes.probes()

    # Assert
    # the probes were run and didn't raise an exception.
