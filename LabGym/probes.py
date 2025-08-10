"""Provide a set of probes to support pre-op sanity checks.

Provide a set of probes to support pre-op sanity checks of the LabGym
sw and its configuration, and outside resources.
"""

# Allow use of newer syntax Python 3.10 type hints in Python 3.9.
from __future__ import annotations

# Standard library imports.
# import inspect
import getpass
# import json
import logging
# import os
# from pathlib import Path
import platform
# import sys


# Log the load of this module (by the module loader, on first import).
#
# These statements are intentionally positioned before this module's
# other imports (against the guidance of PEP 8), to log the load of this
# module before other import statements are executed and potentially
# produce their own log messages.
# pylint: disable=wrong-import-position
logger = logging.getLogger(__name__)
logger.debug('%s', f'loading {__file__}')
logger.debug('%s: %r', '(__name__, __package__)', (__name__, __package__))
# pylint: enable=wrong-import-position


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

    # Check for cacert trouble which might be a fouled installation.
    probe_url_to_verify_cacert()

    # central logger, for reporting usage to the central receiver
    central_logger = central_logging.get_central_logger()

    assert isinstance(central_logger.disabled, bool)
    if central_logger.disabled is True:
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
        #
        # Either
        # 1.  sw is registered.
        #     is_registered() returns True.
        # 2.  registration was skipped (with unchecked "Don't ask again").
        #     is_registered() returns False.
        # 3.  registration was skipped (with checked "Don't ask again").
        #     Now user is running the same version of LabGym as when
        #     registration was skipped.
        #     is_registered() returns True.
        #     Inspect reginfo['name'] and reginfo['version']
        # 4.  registration was skipped (with checked "Don't ask again").
        #     Now user is running a different version of LabGym as when
        #     registration was skipped.
        #     is_registered() returns True.
        #     Inspect reginfo['name'] and reginfo['version']
        #
        # Note that is_registered() depends on
        # <configdir>/registration.yaml.  If the setting for <configdir>
        # is changed to a dir that doesn't have a registration.yaml,
        # then is_registered() will return False.

        reginfo = registration.get_reginfo_from_file()

        # if user has skipped registration (with checked "Don't ask again")
        # but that was selected in some different (earlier?) installation,
        # then expire or void the "skip-henceforth" behavior.
        skip_pass_void = (reginfo is not None
            and reginfo.get('name') == 'skip'
            and packaging.version.parse(version)
                != packaging.version.parse(reginfo.get('version'))
            )

        # if not registration.is_registered():
        if not registration.is_registered() or skip_pass_void:
            # Get reg info from user, store reginfo locally.  Also, send
            # reginfo to central receiver via central_logger (unless
            # central_logger's disabled attribute is True).
            registration.register()

    # Report sw start and context to the central receiver.
    # if central_logger.disabled is True, no logrecord is created/sent.
    central_logger.info(get_context(anonymous))


def probe_url_to_verify_cacert() -> None:
    """Check for cacert trouble which might be a fouled installation.

    Send an HTTP GET to https://dl.fbaipublic.com.  If it fails due to
    cacert trouble, then output an error message and carry on.
    (Or should this be fatal?)

    On 2025-05-19 Google AI says,
        Detectron2 relies on dl.fbaipublicfiles.com for distributing
        pre-built binaries and model weights.
        If you're using the pre-built versions of Detectron2 or 
        downloading pre-trained models, your system will likely be
        downloading files from dl.fbaipublicfiles.com.
    """

    url = 'https://dl.fbaipublicfiles.com/detectron2'

    # With good cacerts.pem & cert chain, requests.get(url) responds with
    #     <Response [403]>
    #
    # With a deficient cacerts.pem, or defective cert chain,
    # requests.get(url) raises an exception, like
    #     requests.exceptions.SSLError: HTTPSConnectionPool(host='dl.fbaipublicfiles.com', port=443): Max retries exceeded with url: /detectron2 (Caused by SSLError(SSLCertVerificationError(1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1007)')))

    try:
        # requests.get(url) returns <Response [403]>
        response = requests.get(url, timeout=8)
    except requests.exceptions.SSLError as e:
        logger.debug('%s: %r', 'certifi.where()', certifi.where())

        # sys.exit(f'(fatal) Trouble in SSL cert chain... ({e})')
        logger.error(f'(non-fatal) Trouble in SSL cert chain... ({e})')


def get_context(anonymous: bool=False) -> dict:
    """Survey and return a dict of context info."""

    try:
        reginfo_uuid = registration.get_reginfo_from_file()['uuid']
    except Exception:
        reginfo_uuid = None

    result = {
        'schema': 'context 2025-08-10',

        # computer name & os, and python version
        # 'node': platform.node(),  # the computer's network name
        # 'platform': platform.platform(aliased=True),
        'python_version': platform.python_version(),

        # LabGym sw
        'version': version,  # LabGym version

        # User info
        # 'username': getpass.getuser(),
        # 'reginfo_uuid': reginfo_uuid,
        }

    # # If anonymous-flag is True, then anonymize the context data.
    # if anonymous:
    #     result.update({
    #         'node': 'anonymous',
    #         'username': 'anonymous',
    #         'reginfo_uuid': 'anonymous',
    #         })

    return result
