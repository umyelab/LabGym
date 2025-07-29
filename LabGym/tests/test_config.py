import logging
from pathlib import Path
import sys

import pytest  # pytest: simple powerful testing with Python

from LabGym import config
from .exitstatus import exitstatus


testdir = Path(__file__[:-3])  # dir containing support files for unit tests
assert testdir.is_dir()


# basicConfig here isn't effective, maybe pytest has already configured logging?
# instead, use the root logger's setLevel method
logging.getLogger().setLevel(logging.DEBUG)


# success cases
def test_success_parse_args_empty(monkeypatch):
    # Arrange
    monkeypatch.setattr(config, '_cached_config', None)
    result = {}
    monkeypatch.setattr(config.myargparse, 'parse_args', lambda: result)
    # logging.debug('%s: %r', 'result', result)

    # Act
    _config = config.get_config()

    # Assert


def test_success_parse_args_has_enable(monkeypatch):
    # Arrange
    monkeypatch.setattr(config, '_cached_config', None)
    result = {'enable': {'alfa': True, 'bravo': False}}
    monkeypatch.setattr(config.myargparse, 'parse_args', lambda: result)
    # logging.debug('%s: %r', 'result', result)

    # Act
    _config = config.get_config()

    # Assert


# A missing explicitly specified configfile is fatal.
def test_missing_configfile(monkeypatch):
    # Arrange
    monkeypatch.setattr(config, '_cached_config', None)
    result = {'configfile': Path('/charlie/delta.yaml')}
    monkeypatch.setattr(config.myargparse, 'parse_args', lambda: result)
    # logging.debug('%s: %r', 'result', result)

    # Act
    with pytest.raises(SystemExit,
            match='Trouble reading user-specified configfile'
            ) as e:
        _config = config.get_config()

    # SystemExit: Trouble reading user-specified configfile (/charlie/delta.yaml)

    # Assert
    assert exitstatus(e.value) == 1


# An existing but defective configfile is fatal.
def test_bad_configfile(monkeypatch):
    # Arrange
    monkeypatch.setattr(config, '_cached_config', None)
    result = {'configfile': testdir.parent.joinpath('bad.yaml')}
    monkeypatch.setattr(config.myargparse, 'parse_args', lambda: result)
    # logging.debug('%s: %r', 'result', result)

    # Act
    with pytest.raises(SystemExit,
            match='Trouble reading user-specified configfile '
            ) as e:
        _config = config.get_config()

    # Assert
    # SystemExit: Trouble reading user-specified configfile (/charlie/delta.yaml)
    assert exitstatus(e.value) == 1
