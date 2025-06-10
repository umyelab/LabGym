import logging
import re
import sys

import pytest

from LabGym import myargparse
import LabGym  # get __version__ from __init__.py
from exitstatus import exitstatus


# basicConfig here isn't effective, because pytest has already configured logging?
#   logging.basicConfig(level=logging.DEBUG)
# instead, use the root logger's setLevel method
logging.getLogger().setLevel(logging.DEBUG)


class ValuesSubclass(myargparse.Values):
    def __eq__(self, other):
        logging.debug('entered custom __eq__ method')
        return self.__dict__ == other.__dict__


# 1.  ['cmd']
def test_parse_args_1(monkeypatch):
    # Arrange
    monkeypatch.setattr(sys, 'argv', ['cmd'])
    logging.debug('monkeypatched sys.argv')

    # Act
    vals = myargparse.parse_args()

    # Assert
    reference_obj = ValuesSubclass()
    reference_obj.cmd = 'cmd'

    # interesting, surprising to me!  Both assertions work, that is,
    # both use the custom __eq__ method from the derivative class obj.
    assert vals == reference_obj
    assert reference_obj == vals


# 2.  ['cmd', '--verbose', '--logginglevel', 'INFO']
#     Args are parsed left-to-right, so logginglevelname gets INFO.
def test_parse_args_2(monkeypatch):
    # Arrange
    monkeypatch.setattr(sys, 'argv',
        ['cmd', '--verbose', '--logginglevel', 'INFO']
        )
    logging.debug('monkeypatched sys.argv')

    # Act
    vals = myargparse.parse_args()

    # Assert
    reference_obj = ValuesSubclass()
    reference_obj.cmd = 'cmd'
    reference_obj.logginglevelname = 'INFO'

    assert vals == reference_obj


# 3.  ['cmd', '--logginglevel', 'INFO', '--verbose']
#     Args are parsed left-to-right, so logginglevelname gets DEBUG.
def test_parse_args_3(monkeypatch):
    # Arrange
    monkeypatch.setattr(sys, 'argv',
        ['cmd', '--logginglevel', 'INFO', '--verbose']
        )
    logging.debug('monkeypatched sys.argv')

    # Act
    vals = myargparse.parse_args()

    # Assert
    reference_obj = ValuesSubclass()
    reference_obj.cmd = 'cmd'
    reference_obj.logginglevelname = 'DEBUG'

    assert vals == reference_obj


# 4.  ['cmd', '--verbose', '--', '--logginglevel', 'INFO']
#     two positional args instead of none
#
#     The '--' arg terminates option processing, so the two following
#     args are considered positional args.
#     But nargs == 0 fails, so prints error msg to stderr, and exits 1.
def test_parse_args_4(monkeypatch):
    # Arrange
    monkeypatch.setattr(sys, 'argv',
        ['cmd', '--verbose', '--', '--logginglevel', 'INFO']
        )
    logging.debug('monkeypatched sys.argv')

    # Act, and assert raises(SystemExit)
    with pytest.raises(SystemExit,
            match='cmd: bad usage -- takes 0 args after options, but 2 were found.'
            '\nUsage: ') as e:
        vals = myargparse.parse_args()

    # Assert
    assert exitstatus(e.value) == 1


# 5.  ['cmd', '--moo']
#     bad option
def test_parse_args_bad_option(monkeypatch):
    # Arrange
    monkeypatch.setattr(sys, 'argv',
        ['cmd', '--moo']
        )
    logging.debug('monkeypatched sys.argv')

    # Act, and assert raises(SystemExit)
    with pytest.raises(SystemExit,
        match="cmd: bad usage -- unrecognized option '--moo'"
            '\nUsage: ') as e:
        vals = myargparse.parse_args()

    # Assert
    assert exitstatus(e.value) == 1


# 6.  --help produces helpmsg on stdout, and sys.exit(0)
def test_parse_args_help(monkeypatch, capsys):
    # Arrange
    monkeypatch.setattr(sys, 'argv',
        ['cmd', '--logginglevel', 'alfa', '-v', '--help', 'bravo', 'charlie']
        )
    logging.debug('monkeypatched sys.argv')

    # Act, and assert raises(SystemExit)
    with pytest.raises(SystemExit) as e:
        vals = myargparse.parse_args()

    # Assert
    assert re.match('Usage: ', capsys.readouterr().out)
    assert exitstatus(e.value) == 0


# 7.  --version produces version on stdout, and sys.exit(0)
def test_parse_args_version(monkeypatch, capsys):
    # Arrange
    monkeypatch.setattr(sys, 'argv',
        ['cmd', '--version']
        )
    logging.debug('monkeypatched sys.argv')

    # Act, and assert raises(SystemExit)
    with pytest.raises(SystemExit) as e:
        vals = myargparse.parse_args()

    # Assert
    assert (capsys.readouterr().out
         == f'LabGym.__version__: {LabGym.__version__}\n')
    assert exitstatus(e.value) == 0
