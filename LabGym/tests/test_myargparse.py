import logging
import sys

import pytest

from LabGym import myargparse


# basicConfig here isn't effective, maybe pytest has already configured logging?
#   logging.basicConfig(level=logging.DEBUG)
# so instead, use the root logger's setLevel method
logging.getLogger().setLevel(logging.DEBUG)


class ValuesSubclass(myargparse.Values):
    def __eq__(self, other):
        logging.debug('entered custom __eq__ method')
        return self.__dict__ == other.__dict__


# 1. ['cmd']
def test_parse_args_1(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['cmd'])
    logging.debug('monkeypatched sys.argv')
    vals = myargparse.parse_args()

    reference_obj = ValuesSubclass()
    reference_obj.cmd = 'cmd'

    # logging.debug('%s: %r', 'vals', vals)
    # logging.debug('%s: %r', 'reference_obj', reference_obj)

    # interesting, surprising to me!  Both assertions work, that is,
    # both use the custom __eq__ method from the derivative class obj.
    # assert reference_obj == vals
    assert vals == reference_obj


# 2.  ['cmd', '--verbose', '--logginglevel', 'INFO']
#     Args are parsed left-to-right, so logginglevelname gets INFO.
def test_parse_args_2(monkeypatch):
    monkeypatch.setattr(sys, 'argv',
        ['cmd', '--verbose', '--logginglevel', 'INFO']
        )
    logging.debug('monkeypatched sys.argv')
    vals = myargparse.parse_args()

    reference_obj = ValuesSubclass()
    reference_obj.cmd = 'cmd'
    reference_obj.logginglevelname = 'INFO'

    assert vals == reference_obj


# 3.  ['cmd', '--logginglevel', 'INFO', '--verbose']
#     Args are parsed left-to-right, so logginglevelname gets DEBUG.
def test_parse_args_3(monkeypatch):
    monkeypatch.setattr(sys, 'argv',
        ['cmd', '--logginglevel', 'INFO', '--verbose']
        )
    logging.debug('monkeypatched sys.argv')
    vals = myargparse.parse_args()

    reference_obj = ValuesSubclass()
    reference_obj.cmd = 'cmd'
    reference_obj.logginglevelname = 'DEBUG'

    assert vals == reference_obj


# 4. ['cmd', '--verbose', '--', '--logginglevel', 'INFO']
#    two positional args instead of none 
#
#    The '--' arg terminates option processing, so the two following
#    args are considered positional args.
#    But nargs == 0 fails, so prints error msg to stderr, and exits 1.
def test_parse_args_4(monkeypatch):
    monkeypatch.setattr(sys, 'argv',
        ['cmd', '--verbose', '--', '--logginglevel', 'INFO']
        )
    logging.debug('monkeypatched sys.argv')

    with pytest.raises(SystemExit,
        match='cmd: bad usage -- takes 0 args after options, but 2 were found.'
            '\nUsage: ') as exc_info:
        # match='.* takes 0 positional arguments but 2 were found'):
        vals = myargparse.parse_args()

    # logging.debug('%s: %r', 'dir(exc_info)', dir(exc_info))
    # logging.debug('%s: %r', 'exc_info.value', exc_info.value)
    # logging.debug('%s: %r', 'exc_info', exc_info)


# 5. ['cmd', '--moo']
#    bad option
def test_parse_args_5(monkeypatch):
    monkeypatch.setattr(sys, 'argv',
        ['cmd', '--moo']
        )
    logging.debug('monkeypatched sys.argv')

    with pytest.raises(SystemExit,
        match='cmd: bad usage -- unrecognized option --moo'
            '\nUsage: ') as exc_info:
        vals = myargparse.parse_args()
