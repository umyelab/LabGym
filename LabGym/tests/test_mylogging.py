import logging
import sys

import pytest

from LabGym import mylogging
from LabGym.myargparse import Values


# basicConfig here isn't effective, maybe pytest has already configured logging?
#   logging.basicConfig(level=logging.DEBUG)
# so instead, use the root logger's setLevel method
logging.getLogger().setLevel(logging.DEBUG)


class ValuesSubclass(Values):
    def __init__(self, datadict={}):
        super().__init__()
        self.__dict__.update(datadict) 
    def __eq__(self, other):
        logging.debug('entered custom __eq__ method')
        return self.__dict__ == other.__dict__


# success cases
# mylogging.config() with opts dict like {'loggingconfigfile': ...}

# 1. bad logginglevelname produces a pair of warning messages.
def test_config_1(monkeypatch):
    # Arrange
    valobj = ValuesSubclass({'logginglevelname': 'ALFA'})
    # print(f'DEBUG: valobj.__dict__, {valobj.__dict__!r}')
    monkeypatch.setattr(
        'LabGym.mylogging.myargparse.parse_args', 
        lambda: valobj)

    # Act
    logrecords = []
    mylogging.config(logrecords)
    mylogging.handle(logrecords)

    # Assert
    # WARNING	mylogging	module 'logging' has no attribute 'ALFA'
    # WARNING	mylogging	Trouble overriding root logger level.


# 2. bad configfile name produces a pair of warning messages.
def test_config_2(monkeypatch):
    # Arrange
    valobj = ValuesSubclass({'loggingconfig': '/bravo/charlie.yaml'})
    # print(f'DEBUG: valobj.__dict__, {valobj.__dict__!r}')
    monkeypatch.setattr(
        'LabGym.mylogging.myargparse.parse_args', 
        lambda: valobj)

    # Act
    logrecords = []
    mylogging.config(logrecords)
    mylogging.handle(logrecords)

    # Assert
    # WARNING	mylogging	[Errno 2] No such file or directory: '/bravo/charlie.yaml'
    # WARNING	mylogging	Trouble configuring logging...  Calling logging.basicConfig(level=logging.DEBUG)


# 3. bad configfile content produces a pair of warning messages.
# def test_config_3(mocker):
#     pass
