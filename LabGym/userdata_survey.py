"""
Provide functions for surveying the locations of user data.

Public functions:
    survey
    assert_userdata_dirs_are_separate
    offer_to_mkdir_userdata_dirs
    advise_on_internal_userdata_dirs

    is_path_under(path1: str|Path, path2: str|Path) -> bool
    is_path_equivalent(path1: str|Path, path2: str|Path) -> bool
    resolve(path1: str|Path) -> str
    dict2str(arg: dict, hanging_indent: str=' '*16) -> str
(consider making some public functions private?)

Public classes: None

The survey function has an early-exit capability, for demonstration
purposes.  If LabGym is started with --enable userdata_survey_exit,
then survey will call sys.exit('Intentionally exiting early').

Design with paths as strings, or, paths as pathlib.Path objects?
Since the paths are configured as strings, assume the calls from outside
this module pass strings, and inside this module, developer is free to
use pathlib where convenient.
In other words, for public functions, support string path args, and
optionally, extend to support Path object args.
"""

# Allow use of newer syntax Python 3.10 type hints in Python 3.9.
from __future__ import annotations

# Standard library imports.
import logging
import os
from pathlib import Path
import sys
import textwrap

# Related third party imports.
import wx  # wxPython, Cross platform GUI toolkit for Python, "Phoenix" version

# Local application/library specific imports.
from LabGym import config, mywx


logger = logging.getLogger(__name__)


def is_path_under(path1: str|Path, path2: str|Path) -> bool:
    """Return True if path2 is under path1."""
    p1 = Path(path1).resolve()
    p2 = Path(path2).resolve()
    return p1 in p2.parents


def is_path_equivalent(path1: str|Path, path2: str|Path) -> bool:
    """Return True if path1 & path2 are equivalent."""

    # if they both exist, are they the same?
    if Path(path1).exists() and Path(path2).exists():
        return Path(path1).samefile(Path(path2))

    # if neither exists, are the strings of the resolved paths the same?
    if not Path(path1).exists() and not Path(path2).exists():
        return resolve(path1) == resolve(path2)

    # At this point, one exists and the other doesn't, therefore False
    return False


def resolve(path1: str|Path) -> str:
    """Return a string representation of the resolved string or Path obj."""
    return str(Path(path1).resolve())


def dict2str(arg: dict, hanging_indent: str=' '*16) -> str:
    """Return a string representation of the dict, with a hanging indent.

    Return '' if the dict is empty.

    Why the hanging indent?  So that it can be tuned to avoid fouling
    the left-alignment when used inside a multiline string that will be
    dedented.
    """

    result = ('\n' + hanging_indent).join(
        [f'{key}: {value}' for key, value in arg.items()]
        )

    return result


def assert_userdata_dirs_are_separate(
        detectors_dir: str, models_dir: str) -> None:
    """Verify the separation of configuration's userdata dirs.

    If not separate, then display an error message, then sys.exit().

    Enforce an expectation that the detectors_dir and models_dir are
    separate, and do not have a "direct, lineal relationshop", where one
    is under the other.
    """

    if (is_path_equivalent(detectors_dir, models_dir)
            or is_path_under(detectors_dir, models_dir)
            or is_path_under(models_dir, detectors_dir)):

        # fatal configuration error
        title = 'LabGym Configuration Error'
        msg = textwrap.dedent(f"""\
            LabGym Configuration Error
                detectors: {detectors_dir!r} ({resolve(detectors_dir)!r})
                models: {models_dir!r} ({resolve(models_dir)!r})

            The userdata dirs must be separate.
            """)

        logger.error('%s', msg)

        # Show the error msg with an OK_Dialog.
        with mywx.OK_Dialog(None, title=title, msg=msg) as dlg:
            mywx.bring_wxapp_to_foreground()

            result = dlg.ShowModal()  # will return wx.ID_OK upon OK or dismiss
            logger.debug('%s: %r', 'result', result)

            sys.exit('Bad configuration')


def offer_to_mkdir_userdata_dirs(
        labgym_dir: str, detectors_dir: str, models_dir: str) -> None:
    """Offer to attempt to mkdir userdata dirs if they are external.

    If there are any userdata dirs that
        (a) are defined in the LabGym configuration to be external to
            the LabGym sw directory,
        (b) don't already exist.
    then offer to attempt to mkdir them.

    Note that the attempts to mkdir can fail and raise an exception for
    several reasons, including insufficient permissions, or parent dir
    of the target dir doesn't exist.
    """

    mkdir_targets = {}

    if (not is_path_under(labgym_dir, detectors_dir)
            and not os.path.isdir(detectors_dir)):
        mkdir_targets.update({'detectors': detectors_dir})
    if (not is_path_under(labgym_dir, models_dir)
            and not os.path.isdir(models_dir)):
        mkdir_targets.update({'models': models_dir})

    if mkdir_targets:
        title = 'LabGym Configuration: make directories?'
        msg = textwrap.dedent(f"""\
            These directories are specified by your LabGym
            configuration, but they don't exist yet.
                {dict2str(mkdir_targets)}

            Try to create them?
            """)
        logger.debug('%s:\n%s', 'msg', msg)

        with mywx.OK_Cancel_Dialog(None, title=title, msg=msg) as dlg:
            mywx.bring_wxapp_to_foreground()

            result = dlg.ShowModal()  # will return wx.ID_OK upon OK or dismiss
            logger.debug('%s: %r', 'result', result)

            if result == wx.ID_OK:
                 for value in mkdir_targets.values():
                      # Deliberately using os.mkdir instead of os.makedirs.
                      # to avoid unintentionally creating a mistake with
                      # multiple levels...
                      os.mkdir(value)


def advise_on_internal_userdata_dirs(
        labgym_dir: str, detectors_dir: str, models_dir: str) -> None:
    """
    """
    if not (is_path_under(labgym_dir, detectors_dir) or
            is_path_under(labgym_dir, models_dir)):
        # No advice is warranted.
        return

    # One or both userdata dirs is under labgym_dir.
    # Prepare the message.

    title = 'LabGym Configuration: internal userdata dirs'

    msg = textwrap.dedent("""\
        Your LabGym configuration (or the configuration 
        defaults) presently define userdata dirs as 
        located within the LabGym tree.
        This arrangement is now deprecated.

        Please follow these instructions to resolve,
        then restart LabGym.
        """)
        #-----------------------------------------------

    # if detectors_dir is internal, and no data is stored, then advise
    # (a) configure new external detectors dir, (b) make the dir.
    # elif detectors_dir is internal, and data is stored, then advise
    # (a) configure new external detectors dir, (b) make the dir, 
    # (d) back up data, (e) move data.

    # msg += textwrap.dedent("""\
    #     
    #     """)
    #     #-----------------------------------------------
       
    logger.debug('%s:\n%s', 'msg', msg)

    with mywx.OK_Dialog(None, title=title, msg=msg) as dlg:
        mywx.bring_wxapp_to_foreground()

        result = dlg.ShowModal()  # will return wx.ID_OK upon OK or dismiss
        logger.debug('%s: %r', 'result', result)


def survey(
    labgym_dir: str,
    detectors_dir: str,
    models_dir: str,
    ) -> None:
    """Display guidance if userdata dirs are within the LabGym tree.

    1.  Verify the separation of configuration's userdata dirs.
        If bad (not separate),
        then display an error message, then sys.exit().

    2.  Check for user data dirs that are external, but don't exist.
        If any, offer to attempt mkdir.

    3.  Check for userdata dirs still located within the LabGym tree.
        If any, advise user to change config, make dirs, backup data,
        move data.  Press OK to quit LabGym.  Press Cancel to
        carry on with deprecated configuration.
    """

    # Get all of the values needed from config.get_config().
    enable_userdata_survey_exit: bool = config.get_config(
        )['enable'].get('userdata_survey_exit', False)

    logger.debug('%s: %r', 'labgym_dir', labgym_dir)
    logger.debug('%s: %r', 'detectors_dir', detectors_dir)
    logger.debug('%s: %r', 'models_dir', models_dir)

    # 1.  Verify the separation of configuration's userdata dirs.
    #     If bad (not separate),
    #     then display an error message, then sys.exit().
    assert_userdata_dirs_are_separate(detectors_dir, models_dir)

    # At this point, the configured detectors_dir models_dir are not in
    # fundamental conflict, at least.

    # 2.  Check for user data dirs that are external, but don't exist.
    #     If any, offer to attempt mkdir.
    offer_to_mkdir_userdata_dirs(labgym_dir, detectors_dir, models_dir)

    # 3.  Check for userdata dirs still located within the LabGym tree.
    #     If any, advise user to change config, make dirs, backup data,
    #     move data.  Press OK to quit LabGym.  Press Cancel to
    #     carry on with deprecated configuration.
    advise_on_internal_userdata_dirs(labgym_dir, detectors_dir, models_dir)

    if enable_userdata_survey_exit:
        sys.exit(f'Exiting early.'
            f'  enable_userdata_survey_exit: {enable_userdata_survey_exit}')
