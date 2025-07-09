import pprint
import sys
import textwrap


def test_import_LabGym_package():
    '''
    Ensures that the interpreter reads every file in LabGym,
    which will catch basic syntax errors and compatibility errors between
    Python 3.9 and 3.10.
    '''

    import LabGym
    print(f'sys.modules: {pprint.pformat(sys.modules)}')


def test_import_LabGym_submodules_alfa(monkeypatch):
    # Arrange sys.argv.  Otherwise it contains pytest args, and
    # myargparse raises an exception.
    monkeypatch.setattr(sys, 'argv', ['dummy'])
    import LabGym.__main__


def test_import_LabGym_submodules_bravo():
    # import LabGym.__main__
    import LabGym.analyzebehavior
    import LabGym.analyzebehavior_dt
    print(f'sys.modules: {pprint.pformat(sys.modules)}')


def test_import_LabGym_submodules_charlie():
    import LabGym.categorizer
    import LabGym.detector
    import LabGym.gui_analyzer
    print(f'sys.modules: {pprint.pformat(sys.modules)}')


def test_import_LabGym_submodules_delta():
    import LabGym.gui_categorizer
    import LabGym.gui_detector
    import LabGym.gui_main
    print(f'sys.modules: {pprint.pformat(sys.modules)}')


def test_import_LabGym_submodules_echo():
    import LabGym.gui_preprocessor
    import LabGym.minedata
    import LabGym.myargparse
    print(f'sys.modules: {pprint.pformat(sys.modules)}')


def test_import_LabGym_submodules_foxtrot():
    import LabGym.mylogging
    import LabGym.tools
    print(f'sys.modules: {pprint.pformat(sys.modules)}')
