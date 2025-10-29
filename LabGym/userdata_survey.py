"""
Provide functions for surveying the locations of user data.

Public functions:
    survey
    verify_userdata_dir_separation

    is_path_under(path1: str|Path, path2: str|Path) -> bool
    is_path_equivalent(path1: str|Path, path2: str|Path) -> bool
    resolve(path1: str|Path) -> str
    dict2str(arg: dict, hanging_indent: str=' '*16) -> str
(consider making some public functions private?)

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

    # if neither exists, are the strings the same
    if not Path(path1).exists() and not Path(path2).exists():
        # return str(Path(path1).resolve()) == str(Path(path2).resolve())
        return resolve(path1) == resolve(path2)

    # At this point, one exists and the other doesn't, therefore False
    return False


def resolve(path1: str|Path) -> str:
    """Return a string representation of the resolved string or Path obj."""
    return str(Path(path1).resolve())


def survey(
    labgym_dir: str,
    detectors_dir: str,
    models_dir: str,
    ) -> None:
    """Display guidance if userdata dirs are within the LabGym tree.

    1.  verify_userdata_dir_separation(detectors_dir, models_dir)
        Verify the separation of configuration's userdata dirs.
        If bad (not separate), 
        then display an error message, then sys.exit().
    """

    # Get all of the values needed from config.get_config().
    enable_userdata_survey_exit: bool = config.get_config(
        )['enable'].get('userdata_survey_exit', False)

    logger.debug('%s: %r', 'labgym_dir', labgym_dir)
    logger.debug('%s: %r', 'detectors_dir', detectors_dir)
    logger.debug('%s: %r', 'models_dir', models_dir)

    # 1.  verify_userdata_dir_separation(detectors_dir, models_dir)
    #     Verify the separation of configuration's userdata dirs.
    #     If bad (not separate), 
    #     then display an error message, then sys.exit().
    verify_userdata_dir_separation(detectors_dir, models_dir)

    # At this point, the configured detectors_dir and models_dir are not
    # in fundamental conflict, at least.

    if enable_userdata_survey_exit:
        sys.exit(f'Exiting early.'
            f'  enable_userdata_survey_exit: {enable_userdata_survey_exit}')
