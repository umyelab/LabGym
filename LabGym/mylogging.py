# pylint: disable=line-too-long
"""Provide functions for configuring the logging system.

--------
Notes to self... (move this elsewhere)
The naming of functions and variables as "config" leads to confusion, because
the verb configure and noun configuration both get shortened to config.
Better not to shorten unless clear from context like 
Function *configure, and variable configuration.
Modulename is  config.
configfile
configdir
--------


Functions
    configure -- Configure logging based on a logging configfile, or 
        fall back and call logging.basicConfig.
    handle -- Use the root logger's handle method to handle each of the
        log records that were "manually" created and queued/stacked,
        prior to and during the configuration of the logging system.

Strengths
  * The config function is guarded, to log exceptions as warnings, and
    discard them instead of propagate/re-raise them.
    Why?  Because for this sw, the logging is considered not essential,
    so logging config trouble is intentionally not fatal.

Notes
  * The Python logging system allows the output of lower-level (like
    INFO) messages, despite the root logger set to higher-level (like
    WARNING).

    If the user supplies command line args which set logginglevelname to
    WARNING (like '--logginglevel WARNING'), the root logger level is
    set to logging.WARNING.
    The user might expect that setting root logger level to WARNING
    would suppress all INFO-level log messages from the console output,
    but it doesn't.

    When logging via a child logger, it is the child logger's effective
    level (not the root logger's level) which determines whether a log
    record is created.  As that log record is propagated up to other
    loggers in the hierarchy, it's passed to the handlers of those
    superior loggers (if any exist), and so the log record is passed to
    the handlers on the root logger.
    If a root logger handler doesn't reject log record, then that
    handler will emit the log record.

    For example, if
        root logger level is set to WARNING
        child logger 'urllib3.connectionpool' level is set to INFO
    then
        an INFO-level logrecord created by the child logger
        'urllib3.connectionpool' will be handled/emitted by the root
        logger's handler(s)
    unless propagation is disabled, or the root logger handler is given
    a handler-level-value or a handler-filter-function which rejects the
    log record.

    See
        "Logging Flow"
        https://docs.python.org/3/howto/logging.html#logging-flow

References
    https://docs.python.org/3/library/logging.html
    https://docs.python.org/3/howto/logging.html#logging-basic-tutorial
    https://docs.python.org/3/howto/logging.html#logging-advanced-tutorial
    https://docs.python.org/3/howto/logging-cookbook.html#logging-cookbook

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
# pylint: enable=line-too-long

# Allow use of newer syntax Python 3.10 type hints in Python 3.9.
from __future__ import annotations

# Standard library imports.
import inspect
import logging.config
import os
from pathlib import Path
# import pprint
try:
    # tomllib is included in the Python Standard Library since version 3.11
    import tomllib  # type: ignore
except ModuleNotFoundError:
    import tomli as tomllib  # A lil' TOML parser
from typing import Dict, List

# Related third party imports.
import yaml

# Local application/library specific imports.
from LabGym import config


logger = logging.getLogger(__name__)
# For production use, this module's logger should be disabled.
logger.disabled = True


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
    """Return a LogRecord for a string or exception.

    Also, for development, shadow this logrecord creation by sending
    myobj to this module's logger.
    For production use, this module's logger should be disabled.
    """
    lineno = inspect.stack()[2].lineno  # type: ignore

    logrecord = logging.LogRecord(
        level=level,
        msg="%s", args=(f'{myobj}',),
        lineno=lineno,
        exc_info=None, name=__name__, pathname=__file__,
        )

    if level >= logger.getEffectiveLevel():
        logger.handle(logrecord)  # for development only

    return logrecord


def _mywarning(myobj: str | Exception) -> logging.LogRecord:
    """Return a WARNING LogRecord for a string or exception."""
    return _myLogRecord(myobj, level=logging.WARNING)


def _mydebug(myobj: str | Exception) -> logging.LogRecord:
    """Return a DEBUG LogRecord for a string or exception."""
    return _myLogRecord(myobj, level=logging.DEBUG)


# def get_logging_configfile() -> Path:
#     """Return the path to a toml or yaml configfile for logging.
# 
#     If no configfile exists among the standard paths, then raise an
#     Exception.
# 
#     In decreasing precedence:
#         1.  in the current dir of the process, that is, in os.getcwd(),
#             like
#                 *cwd*/logging.yaml
#         2.  in a package config dir in the user's home dir, that is, in
#             $HOME/.__package__, like
#                 /Users/Andrew/.labgym/logging.yaml
#         3.  in this module file's dir, that is, dirname(__file__), like
#                 .../LabGym/logging.yaml
#     """
# 
#     logger.debug('Milepost')
#     myconfig = config.get_config()
#     logger.debug('Milepost')
#     configdir = Path(myconfig.get('configdir'))
#     logger.debug('Milepost')
# 
#     # Prepare a list of configfile path objs to iterate through.
#     configfiles = []
# 
#     if myconfig.get('logging_configfile'):
#         _ = Path(myconfig.get('logging_configfile'))
#         if os.path.is_abs(_):
#             configfile = _
#         else:
#             # if configfile is relative, fix it relative to configdir.
#             configfile = configdir.joinpath(_)
# 
#         configfiles.append(configfile)
# 
#     configfiles.extend([
#         configdir.joinpath('logging.toml'),
#         configdir.joinpath('logging.yaml'),
# 
#         Path(os.path.dirname(__file__)).joinpath('logging.yaml'),
#         ])
# 
#     # Step through the list of path objs and return the first that exists.
#     for configfile in configfiles:
#         if configfile.is_file():
#             return configfile
# 
#     # No configfile has been found, so raise an exception.
#     # (? another way to signal this would be to return None ?)
#     raise Exception('logging configfile not found')


def get_configdict_from_configfile(configfile: Path) -> Dict:
    """Read the configfile and return the config dictionary."""
    if configfile.name.endswith('.toml'):
        with open(configfile, 'rb') as f:
            result = tomllib.load(f)
    elif configfile.name.endswith('.yaml'):
        # with open(configfile, 'r') as f:
        with open(configfile, 'r', encoding='utf-8') as f:
            result = yaml.safe_load(f)
    else:
        raise Exception('bad extension.  configfile: {configfile!r}')

    return result



# def _config(
#         logging_configfilepath: Path,
#         # opts: myargparse.Values,
#         logrecords: List[logging.LogRecord],
#         ) -> None:
#     """Configure the logging system based on a configfile.
# 
#     Args
#       opts -- a mylogging.Values object of parsed command-line values.
#       logrecords -- a list of not-yet-handled log records
# 
#     If a logging congfigfile was specified by command-line args, then
#     try to configure logging with it.
# 
#     Otherwise, a logging configfile was not specified by command-line
#     args, so iterate through a list of standard locations, and try to
#     configure logging with the first found to exist.
#     The list of standard locations ends with mypkg/logging.yaml.
# 
#     Append any new log records to logrecords, for later handling.
#     """
# 
#     if opts.loggingconfig is not None:
#         configfile = opts.loggingconfig
#     else:
#         configfile = get_configfile()
# 
#     logrecords.append(_mydebug(f'configfile: {configfile!r}'))
# 
#     # Get the config dictionary from the configfile.
#     configdict = get_configdict(configfile)
#     logrecords.append(_mydebug(
#         'function get_configdict returned a result'))
#     # logrecords.append(_mydebug(
#     #     f'configdict:\n{pprint.pformat(configdict, indent=2)}'))
# 
#     # Apply the config dictionary.
#     logging.config.dictConfig(configdict)
# 
# 
# def get_dict_from_file(filepath):
#     if filepath.endswith('.toml'):
#     elif filepath.endswith('.yaml'):
#     else:
#         raise Exception(f'Bad extension. filepath: {filepath}')


def configure(logrecords: List[logging.LogRecord] = []) -> None:
    """Configure logging based on configfile, or fall back to basicConfig().

    Args
      logrecords -- a list of not-yet-handled log records

    (1) Configure logging based on configfile, or fall back to
        calling logging.basicConfig(level=logging.DEBUG).
        Set logging.raiseExceptions to False.  (Why?  Because We want to 
        ignore handler-emit exceptions.)

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

        # Get all of the values needed from config.get_config().
        _config = config.get_config()
        logging_configfiles: List[Path] = _config['logging_configfiles']
        logging_configfile: Path|None = _config.get('logging_configfile')
        logging_levelname: str|None = _config.get('logging_levelname')

        # if the config defines a specific logging_configfile, only
        # attempt to use it.  Otherwise, step through the list of
        # logging_configfile and try them until success.

        if logging_configfile:
            logging_configfiles = [logging_configfile]

        for logging_configfile in logging_configfiles:
            try:
                configdict = get_configdict_from_configfile(logging_configfile)
                logging.config.dictConfig(configdict)

                logrecords.append(_mydebug(
                    f'Applied logging config from {logging_configfile}'))

                break
            except Exception as e:
                # this logging_configfile was unsuitable, go to next
                logrecords.append(_mydebug(
                    f'Unsuitable logging configfile {logging_configfile}.'
                    f'  ...  {e}'))

        else:
            # none of the logging_configfiles was suitable
            logrecords.append(_mywarning(
                'Trouble configuring logging...  '
                'Calling logging.basicConfig(level=logging.DEBUG)'))

            logging.basicConfig(level=logging.DEBUG)
                

#         logger.debug('Milepost')
#         logging_configfile = Path(
#             config.get_config().get('logging_configfile'))
#         logger.debug('Milepost')
# 
#         if os.path.isabs(logging_configfile):
#             logging_configfilepath = logging_configfile
#         else:
#             configdir = config.get_config.get('configdir')
#             logging_configfilepath = configdir.joinpath(logging_configfile)
#         logger.debug('Milepost')
# 
#         logrecords.append(_mydebug(
#             f'logging_configfilepath: {logging_configfilepath}'))
#         logger.debug('Milepost')

#         # (1) Configure logging based on configfile, or fall back to
#         #     calling logging.basicConfig(level=logging.DEBUG).
# 
#         # A missing logging-configfile produces a warning.
#         # 
#         # An existing but unreadable or defective logging-configfile 
#         # produces a warning.  
#         # Why not raise an exception?  Because the logging system is 
#         # non-essential; trouble configuring or using the # logging 
#         # system should not be fatal.
#         try:
#             _config(logging_configfilepath, logrecords)
#         except Exception as e:
#             # log the exception as a warning
#             # log another message as a warning
#             # call logging.basicConfig
#             logrecords.append(_mywarning(e))
#             logrecords.append(_mywarning(
#                 'Trouble configuring logging...  '
#                 'Calling logging.basicConfig(level=logging.DEBUG)'))
#             logging.basicConfig(level=logging.DEBUG)

        # Set logging.raiseExceptions to False.  (Why?  Because We want to 
        # ignore handler-emit exceptions.)
        logging.raiseExceptions = False

        # (2) Redirect all warnings ... to the logging system.
        logging.captureWarnings(True)

        # (3) Honor command-line args that override the root logger level.
        try:
            if logging_levelname is not None:
                logrecords.append(_mydebug(
                    f'logging_levelname: {logging_levelname!r}'))
                logging.getLogger().setLevel(getattr(logging, logging_levelname))

        except Exception as e:
            logger.exception(e)
            # log the exception as a warning
            logrecords.append(_mywarning(
                f'Trouble overriding root logger level.  ... {e}'))

    except Exception as e:
        logger.exception(e)
        # log the exception as a warning
        logrecords.append(_mywarning(
            f'Trouble configuring logging.  ... {e}'))


def handle(logrecords: List[logging.LogRecord]) -> None:
    """Use the root logger's handle method to handle each logrecord.

    Args
      logrecords -- a list of log records

    This function expects that the logging system has been configured
    already.

    This function guards against propagating/re-raising exceptions.
    """

    try:
        # rootlogger = logging.getLogger()
        # for rec in logrecords:
        #     # rec_logger is the name given at LogRecord creation.  For
        #     # logger-generated LogRecords, this rec_logger is  the name 
        #     # of the logger.
        #     rec_logger = logging.getLogger(rec.name)
        #     if rec.levelno >= rec_logger.getEffectiveLevel():
        #         rootlogger.handle(rec)
        
        for logrecord in logrecords:
            logger = logging.getLogger(logrecord.name)
            if logrecord.levelno >= logger.getEffectiveLevel():
                logger.handle(logrecord)
            

    except Exception as e:
        # log the exception as a warning
        logger.warning(f'Trouble handling logrecords.  {e}')
