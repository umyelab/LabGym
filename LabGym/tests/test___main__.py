import importlib
import logging
import os
import re
import sys
import time

# basicConfig here isn't effective, maybe pytest has already configured logging?
#   logging.basicConfig(level=logging.DEBUG)
# so instead, use the root logger's setLevel method
logging.getLogger().setLevel(logging.DEBUG)

from packaging import version
import pytest

# is the . really necessary after fixing the pth?
from .exitstatus import exitstatus

# Specify sys.argv before importing __main__.  Why?  Because the 
# loading of my __main__ is sensitive to the contents of sys.argv, which
# is initialized the pytest command and args.
sys.argv = ['cmd', '--verbose']
T0 = time.time()
import LabGym.__main__  # Time consuming... (typical 24 sec, 25 sec, 34 sec)
sys.loadtime = time.time() - T0

def test_inspect():
    logging.debug(f'sys.argv: {sys.argv!r}')
    logging.debug(f'load time for import __main__: {sys.loadtime:.0f} seconds')
    logging.debug(f'LabGym.__main__.logrecords: {LabGym.__main__.logrecords!r}')
    
    for rec in LabGym.__main__.logrecords:
        # logging.debug(f'dir(rec): {dir(rec)}')
        assert rec.msg == '%s'
        assert len(rec.args) == 1
        print(f'{rec.levelname} {rec.args[0]}') 
    

def test_handshake():
    LabGym.__main__.handshake.handshake()

def test_main(monkeypatch):
    monkeypatch.setattr('LabGym.__main__.gui_main.main_window', lambda: None)
    LabGym.__main__.main()


def x_test_moduleload(monkeypatch):
    """This doesn't seem to reload everything, since loadtime is typical 0.000222 sec."""

    logging.debug(f'sys.argv: {sys.argv!r}')
    T0 = time.time()
    try:
        logging.debug('reloading LabGym.__main__')
        importlib.reload(LabGym.__main__)
    except NameError as e:
        logging.debug('importing LabGym.__main__')
        import LabGym.__main__
    loadtime = time.time() - T0

    logging.debug(f'LabGym.__main__.logrecords: {LabGym.__main__.logrecords!r}')
    # logging.debug(f'load time for import __main__: {loadtime:.0f} seconds')
    logging.debug(f'load time for import __main__: {loadtime:f} seconds')
