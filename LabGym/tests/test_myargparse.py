import logging
import re
import sys

import pytest

from LabGym import myargparse
from LabGym import __version__ as version
from .exitstatus import exitstatus


# basicConfig here isn't effective, because pytest has already configured logging?
#   logging.basicConfig(level=logging.DEBUG)
# instead, use the root logger's setLevel method
logging.getLogger().setLevel(logging.DEBUG)


# No args.
def test_parse_args_no_args(monkeypatch):
    # Arrange
    monkeypatch.setattr(sys, 'argv', ['cmd'])

    # Act
    result = myargparse.parse_args()

    # Assert
    assert result == {}


# Args are parsed left-to-right, so logging_levelname gets INFO.
def test_parse_args_verbose_then_info(monkeypatch):
    # Arrange
    monkeypatch.setattr(sys, 'argv',
        ['cmd', '--verbose', '--logging_level', 'INFO'])

    # Act
    result = myargparse.parse_args()

    # Assert
    assert result == {'logging_level': 'INFO'}


# Args are parsed left-to-right, so logging_level gets DEBUG.
def test_parse_args_info_then_verbose(monkeypatch):
    # Arrange
    monkeypatch.setattr(sys, 'argv',
        ['cmd', '--logging_level', 'INFO', '--verbose'])

    # Act
    result = myargparse.parse_args()

    # Assert
    assert result == {'logging_level': 'DEBUG'}


# bad option
def test_parse_args_bad_option(monkeypatch):
    # Arrange
    monkeypatch.setattr(sys, 'argv',
        ['cmd', '--moo'])

    # Act, and assert raises(SystemExit)
    with pytest.raises(SystemExit,
        match="cmd: bad usage -- unrecognized option '--moo'"
            '\nUsage: ') as e:
        result = myargparse.parse_args()
 
    # Assert
    assert exitstatus(e.value) == 1


#  --help produces helpmsg on stdout, and sys.exit(0)
def test_parse_args_help(monkeypatch, capsys):
    # Arrange
    monkeypatch.setattr(sys, 'argv',
        ['cmd', '--logging_level', 'ALFA', '-v', '--help', 'bravo'])
 
    # Act, and assert raises(SystemExit)
    with pytest.raises(SystemExit) as e:
        result = myargparse.parse_args()

    # Assert
    assert re.match('Usage: ', capsys.readouterr().out)
    assert exitstatus(e.value) == 0


# --version produces version on stdout, and sys.exit(0)
def test_parse_args_version(monkeypatch, capsys):
    # Arrange
    monkeypatch.setattr(sys, 'argv',
        ['cmd', '--version'])
 
    # Act, and assert raises(SystemExit)
    with pytest.raises(SystemExit) as e:
        result = myargparse.parse_args()

    # Assert
    assert capsys.readouterr().out == f'version: {version}\n'
    assert exitstatus(e.value) == 0
 
 
def test_anonymous(monkeypatch):
    # Arrange
    monkeypatch.setattr(sys, 'argv', 
        ['dummy', '--anonymous'])

    # Act
    result = myargparse.parse_args()

    # Assert
    assert result == {'anonymous': True}
 

def test_enable_(monkeypatch):
    # Arrange
    monkeypatch.setattr(sys, 'argv',
        ['dummy', '--enable', 'F1', '--enable', 'F2', '--disable', 'F1'])

    # Act
    result = myargparse.parse_args()

    # Assert
    assert result == {'enable': {'F1': False, 'F2': True}}
