"""Provide functions for configuring the logging system.

Functions
    config -- Configure logging based on a configfile, or fall back and
        call logging.basicConfig.
    handle -- Use the root logger's handle method to handle each of the
        log records that were "manually" created and queued/stacked,
        prior to and during the configuration of the logging system.

Strengths
  * The config function is guarded, to log exceptions as warnings, and
    discard them instead of propagate/re-raise them.
    Why?  Because for this sw, the logging is considered not essential,
    so logging config trouble is intentionally not fatal.

Example 1
    # Configure the logging system.
    import LabGym.mylogging as mylogging
    mylogging.config()

Example 2, handle logrecords created during the call to config
    # Configure the logging system.
    import LabGym.mylogging as mylogging
    logrecords = []
    mylogging.config(logrecords)  # (appends some log records)
    mylogging.handle(logrecords)  # handle each log record

Example 3, handle logrecords created before and during the call to config
    # Configure the logging system.
    # Log the load of this module (by the module loader, on first import).
    #
    # These statements are intentionally positioned before this module's
    # other imports (against the guidance of PEP 8), to log the load of this
    # module before other import statements are executed and produce their
    # own log messages.
    import inspect
    import logging
    logrecords = [logging.LogRecord(lineno=inspect.stack()[0].lineno,
        level=logging.DEBUG, msg='%s', args=(f'loading {__file__}',),
        exc_info=None, name=__name__, pathname=__file__,
        )]
    import LabGym.mylogging as mylogging
    mylogging.config(logrecords)  # (appends some log records)
    mylogging.handle(logrecords)  # handle each log record

    # other imports...

    logger = logging.getLogger(__name__)
    logger.debug('milepost')

The output depends on the configuration of the logging system.
For Example 3,

(a) If the default config file LabGym/logging.yaml is used, with root
    logger level=INFO, then there is no console output of the DEBUG
    messages.

(b) If a modified config file is used (for example
    ~/.LabGym/logging.yaml) with root logger level=DEBUG, or if command-
    line arg --verbose is specified, then console output shows messages
    like

    2025-05-14 09:21:02     DEBUG   [4467582464:LabGym.__main__:__main__:28]        loading /Users/john/Public/LabGym/LabGym/__main__.py
    2025-05-14 09:21:02     DEBUG   [4467582464:LabGym.mylogging:mylogging:291]     configfile: '/Users/john/.LabGym/logging.yaml'
    2025-05-14 09:21:02     DEBUG   [4467582464:LabGym.mylogging:mylogging:295]     function get_configdict returned a result
    2025-05-14 09:21:02     DEBUG   [4467582464:LabGym.__main__:__main__:38]        __name__: 'LabGym.__main__'

(c) If no config file is found or the config file is fouled, then
    console output shows messages like

    DEBUG:LabGym.__main__:loading /Users/john/Public/LabGym/LabGym/__main__.py
    DEBUG:LabGym.mylogging:configfile: '/Users/john/.LabGym/logging.toml'
    WARNING:LabGym.mylogging:Expected '=' after a key in a key/value pair (at line 4, column 8)
    WARNING:LabGym.mylogging:Trouble configuring logging.  Calling logging.basicConfig(level=logging.DEBUG)
    DEBUG:LabGym.__main__:__name__: 'LabGym.__main__'
"""  # noqa: E501

from __future__ import annotations  # 3.9 needs this for some type annotations

# standard library imports
import inspect
import logging.config
import os
# import pprint
# import sys
try:
    # tomllib is included in the Python Standard Library since version 3.11
    import tomllib  # type: ignore
except ModuleNotFoundError:
    import tomli as tomllib
from typing import Dict, List

# related third party imports
import yaml

# local application/library specific imports
import LabGym.myargparse as myargparse
# from LabGym import myargparse  # pylint suggests this instead


# _mywarning -- Return a WARNING LogRecord for a string or exception.
# _mydebug -- Return a DEBUG LogRecord for a string or exception.
#
# Example
#     logrecords = []
#     ...
#     logrecords.append(_mydebug('Milepost'))
#     try:
#         logrecords.append(_mydebug('Trying...')
#         ...
#         logrecords.append(_mydebug('Succeeded')
#     except Exception as e:
#         # log the exception as a warning
#         # log another message as a warning
#         logrecords.append(_mywarning(e))
#         logrecords.append(_mywarning('Trouble...'))
#
def _myLogRecord(myobj: str | Exception, level: int) -> logging.LogRecord:
    """Return a LogRecord for a string or exception."""
    lineno = inspect.stack()[2].lineno  # type: ignore

    return logging.LogRecord(
        level=level,
        msg="%s", args=(f'{myobj}',),
        lineno=lineno,
        exc_info=None, name=__name__, pathname=__file__,
        )


def _mywarning(myobj: str | Exception) -> logging.LogRecord:
    """Return a WARNING LogRecord for a string or exception."""
    # print(f'W: {myobj}')
    return _myLogRecord(myobj, level=logging.WARNING)


def _mydebug(myobj: str | Exception) -> logging.LogRecord:
    """Return a DEBUG LogRecord for a string or exception."""
    # print(f'D: {myobj}')
    return _myLogRecord(myobj, level=logging.DEBUG)


def get_configfile() -> str:
    """Return the path to a toml or yaml logging configfile.

    If no configfile exists among the standard paths, then raise an
    Exception.

    In decreasing precedence:
        1.  in the current dir of the process, that is, in os.getcwd(),
            like
                *cwd*/logging.yaml
        2.  in a package config dir in the user's home dir, that is, in
            $HOME/.__package__, like
                /Users/Andrew/.labgym/logging.yaml
        3.  in this module file's dir, that is, dirname(__file__), like
                .../LabGym/logging.yaml
    """

    # Prepare a list of configfile paths to iterate through.
    configfiles = [
        os.path.join(os.getcwd(), 'logging.toml'),
        os.path.join(os.getcwd(), 'logging.yaml'),
        ]

    home = os.environ.get('HOME')
    if home is not None:
        configfiles.extend([
            os.path.join(home, f'.{__package__}', 'logging.toml'),
            os.path.join(home, f'.{__package__}', 'logging.yaml'),
            os.path.join(home, f'.{__package__.lower()}', 'logging.toml'),
            os.path.join(home, f'.{__package__.lower()}', 'logging.yaml'),
            ])

    configfiles.extend([
        os.path.join(os.path.dirname(__file__), 'logging.toml'),
        os.path.join(os.path.dirname(__file__), 'logging.yaml'),
        ])

    # Step through the list of configfiles and return the first that exists.
    for configfile in configfiles:
        if os.path.exists(configfile):
            return configfile

    # No configfile has been found, so raise an exception.
    # (? another way to signal this would be to return None ?)
    raise Exception('logging configfile not found')


def get_configdict(configfile: str) -> Dict:
    """Read the configfile and return the config dictionary."""
    if configfile.endswith('.toml'):
        with open(configfile, 'rb') as f:
            configdict = tomllib.load(f)
    elif configfile.endswith('.yaml'):
        # with open(configfile, 'r') as f:
        with open(configfile, 'r', encoding='utf-8') as f:
            configdict = yaml.safe_load(f)
    else:
        raise Exception('bad extension -- configfile: {configfile!r}')

    return configdict


def _config(
        opts: myargparse.Values,
        logrecords: List[logging.LogRecord],
        ) -> None:
    """Configure the logging system based on a configfile.

    Args
      opts -- a mylogging.Values object of parsed command-line values.
      logrecords -- a list of not-yet-handled log records

    If a logging congfigfile was specified by command-line args, then
    try to configure logging with it.

    Otherwise, a logging configfile was not specified by command-line
    args, so iterate through a list of standard locations, and try to
    configure logging with the first found to exist.
    The list of standard locations ends with mypkg/logging.yaml.

    Append any new log records to logrecords, for later handling.
    """

    if opts.loggingconfig is not None:
        configfile = opts.loggingconfig
    else:
        configfile = get_configfile()

    logrecords.append(_mydebug(f'configfile: {configfile!r}'))

    # Get the config dictionary from the configfile.
    configdict = get_configdict(configfile)
    logrecords.append(_mydebug(
        'function get_configdict returned a result'))
    # logrecords.append(_mydebug(
    #     f'configdict:\n{pprint.pformat(configdict, indent=2)}'))

    # Apply the config dictionary.
    logging.config.dictConfig(configdict)


def config(logrecords: List[logging.LogRecord] = []) -> None:
    """Configure logging based on configfile, or fall back to basicConfig().

    Args
      logrecords -- a list of not-yet-handled log records

    (1) Configure logging based on configfile, or fall back to
        calling logging.basicConfig(level=logging.DEBUG).

    (2) Redirect all warnings issued by the warnings module to the
        logging system.

    (3) After configuring the logging system per configfile, honor
        command-line args that override the root logger level (-v,
        --verbose, --logginglevel DEBUG).

    While executing this function, append any new log records to
    logrecords (for later handling).

    This function guards against propagating/re-raising exceptions.
    """

    try:
        # logrecords is a list of not-yet-handled log records

        # parse command line args
        opts = myargparse.parse_args()
        logrecords.append(_mydebug(f'opts.__dict__: {opts.__dict__}'))

        # (1) Configure logging based on configfile, or fall back to
        #     calling logging.basicConfig(level=logging.DEBUG).
        try:
            _config(opts, logrecords)
        except Exception as e:
            # log the exception as a warning
            # log another message as a warning
            # call logging.basicConfig
            logrecords.append(_mywarning(e))
            logrecords.append(_mywarning(
                'Trouble configuring logging...  '
                'Calling logging.basicConfig(level=logging.DEBUG)'))
            logging.basicConfig(level=logging.DEBUG)

        # (2) Redirect all warnings ... to the logging system.
        logging.captureWarnings(True)

        # (3) Honor command-line args that override the root logger level.
        try:
            levelname = opts.logginglevelname
            if levelname is not None:
                logrecords.append(_mydebug(f'levelname: {levelname!r}'))
                logging.getLogger().setLevel(getattr(logging, levelname))

        except Exception as e:
            # log the exception as a warning
            # log another message as a warning
            logrecords.append(_mywarning(e))
            logrecords.append(_mywarning(
                'Trouble overriding root logger level.'))

    except Exception as e:
        # log the exception as a warning
        # log another message as a warning
        logrecords.append(_mywarning(e))
        logrecords.append(_mywarning('Trouble configuring logging.'))


def handle(logrecords: List[logging.LogRecord]) -> None:
    """Use the root logger's handle method to handle each logrecord.

    Args
      logrecords -- a list of log records

    This function expects that the logging system has been configured
    already.

    This function guards against propagating/re-raising exceptions.
    """

    try:
        rootlogger = logging.getLogger()
        for rec in logrecords:
            # the logger to which the logrecord was attributed
            rec_logger = logging.getLogger(rec.name)
            if rec.levelno >= rec_logger.getEffectiveLevel():
                rootlogger.handle(rec)

    except Exception as e:
        # log the exception as a warning
        # log another message as a warning
        logging.warning(e)
        logging.warning('Trouble handling logrecords')
