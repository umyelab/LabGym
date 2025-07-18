"""Provide a set of probes to support pre-op sanity checks.

Provide a set of probes to support pre-op sanity checks of the LabGym 
sw and its configuration, and outside resources.
"""

# Standard library imports.
# import inspect
import getpass
import json
import logging
import os
from pathlib import Path
import platform
import sys


# Log the load of this module (by the module loader, on first import).
#
# These statements are intentionally positioned before this module's
# other imports (against the guidance of PEP 8), to log the load of this
# module before other import statements are executed and potentially
# produce their own log messages.
logger = logging.getLogger(__name__)
logger.debug('%s', f'loading {__file__}')
logger.debug('%s: %r', '(__name__, __package__)', (__name__, __package__))


# Related third party imports.
import certifi  # Python package for providing Mozilla's CA Bundle.
import requests  # Python HTTP for Humans.
import packaging  # Core utilities for Python packages

# Local application/library specific imports.
from LabGym import __version__ as version
from LabGym import central_logging, registration
from LabGym import config


def probes() -> None:
    """Perform some pre-op checks and probes of outside resources.

    It's generally preferable to expose any inevitable problems sooner
    rather than later.
    Some checks can be suppressed by command line options.
    """

    # Get all of the values needed from config.get_config().
    _config = config.get_config()
    anonymous: bool = _config['anonymous']
    registration_enable: bool = _config['enable']['registration']

    # central logger, for reporting usage to the central receiver
    central_logger = central_logging.get_central_logger()

    assert isinstance(central_logger.disabled, bool)
    if central_logger.disabled == True:
        logger.info('Central Logging is disabled.')
    else:
        logger.info('Central Logging is enabled.')

    if anonymous:
        # skip registration check
        logger.info('Skipping Registration Check'
             f' because anonymous: {anonymous}')
    elif central_logger.disabled:
        # skip registration check
        logger.info('Skipping Registration Check'
             f' because central_logger.disabled: {central_logger.disabled}')
    elif not registration_enable:
        # skip registration check
        logger.info('Skipping Registration Check'
             f' because registration_enable: {registration_enable}')
    else:
        # proceed with registration check
        if not registration.is_registered():
            # Get reg info from user, store reginfo locally.  Also, send 
            # reginfo to central receiver via central_logger.
            registration.register()

    # Report sw start and context to the central receiver.
    # if central_logger.disabled is True, no logrecord is created/sent.
    central_logger.info(get_context(anonymous))


def get_context(anonymous: bool=False) -> dict:
    """Survey and return a dict of context info."""

    try:
        reginfo_uuid = registration.get_reginfo_from_file()['uuid']
    except:
        reginfo_uuid = None

    result = {
        'schema': 'context 2025-07-10',

        # computer name & os, and python version
        'node': platform.node(),  # the computer's network name
        'platform': platform.platform(aliased=True),
        'python_version': platform.python_version(),

        # LabGym sw
        'version': version,  # LabGym version

        # User info
        'username': getpass.getuser(),
        'reginfo_uuid': reginfo_uuid,
        }

    # If anonymous-flag is True, then anonymize the context data.
    if anonymous:
        result.update({
            'node': 'anonymous',
            'username': 'anonymous',
            'reginfo_uuid': 'anonymous',
            })

    return result
