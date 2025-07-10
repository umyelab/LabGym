"""
Load each of the package's top-level py-files.

...namely, LabGym/*.py.
These tests will expose basic syntax errors that prevent import.

Some tests are specific to a set of py-files, possibly because they 
require setup.

The final test, test_remainder(), imports each of the remaining top-
level py-files.
The strength of this catch-all final test is that if a new top-level 
py-file is introduced, full coverage is preserved and this test-file
may still be suitable.
"""

import glob
import importlib
import logging
import os
import pprint
import sys
import textwrap


submodules = []


def test_import_LabGym_package():
    """Load LabGym.__init__.py and get a list of submodules."""
    import LabGym

    # Confirm the assumption that under pytest, cwd is LabGym package's 
    # parent dir (the repo dir).
    assert os.getcwd() == os.path.dirname(os.path.dirname(LabGym.__file__))

    # Prepare a list of all submodule py-files in LabGym dir, but not subdirs.
    pyfiles = glob.glob(os.path.join(os.path.dirname(LabGym.__file__), '*.py'))
    pyfiles.sort()  # result from glob.glob() isn't sorted
    submodules.extend([os.path.basename(f).rstrip('.py') for f in pyfiles])
    logging.debug('%s:\n%s', 'Milepost 0, submodules', 
        textwrap.indent(pprint.pformat(submodules), '  '))

    # Remove __init__.py.  There's no need to challenge it, as it was
    # already loaded by the "import LabGym" statement at the beginning 
    # of this in this test.
    submodules.remove('__init__')


def test_imports_with_sysargv_initialized(monkeypatch):
    # Arrange sys.argv.  Otherwise sys.argv contains pytest args, and
    # myargparse raises an exception.
    monkeypatch.setattr(sys, 'argv', ['dummy'])

    # Act
    logging.info('import LabGym.__main__')
    import LabGym.__main__
    submodules.remove('__main__')

    logging.info('import LabGym.myargparse')
    import LabGym.myargparse
    submodules.remove('myargparse')


def test_remainder():
    logging.debug('%s:\n%s', 'Milepost 1, submodules', 
        textwrap.indent(pprint.pformat(submodules), '  '))

    while len(submodules) > 0:
        submodule = submodules[0]
        logging.info(f"importlib.import_module('LabGym.{submodule}')")
        importlib.import_module(f'LabGym.{submodule}')
        submodules.pop(0)

    logging.debug('%s:\n%s', 'Milepost 2, submodules', 
        textwrap.indent(pprint.pformat(submodules), '  '))
