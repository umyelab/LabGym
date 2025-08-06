# pylint: disable=line-too-long
"""Provide functions for configuring the logging system.

Functions
    configure -- Configure logging based on configfile, then handle list
        of logrecords.

Strengths
  * The configure function is guarded, to log exceptions as warnings, and
    discard them instead of propagate/re-raise them.
    Why?  Because for this sw, the logging is considered not-essential,
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
    from LabGym.mylogging import mylogging
    mylogging.config()

Example 2, Log the loading of this module, and configure the logging system.
    # Standard library imports.
    import inspect
    import logging
    ...

    # Log the loading of this module (by the module loader, on first import).
    # Configure the logging system.
    #
    # These statements are intentionally positioned before this module's
    # other imports (against the guidance of PEP 8), to log the load of this
    # module before other import statements are executed and potentially
    # produce their own log messages.
    logrecords = [logging.LogRecord(lineno=inspect.stack()[0].lineno,
        level=logging.DEBUG, exc_info=None, name=__name__, pathname=__file__,
        msg='%s', args=(f'loading {__file__}',),
        )]
    from LabGym import mylogging
    # Configure logging based on configfile, then handle list of logrecords.
    mylogging.configure(logrecords)

    # Related third party imports.
    ...

    # Local application/library specific imports.
    ...

    logger = logging.getLogger(__name__)

    logger.debug('Milestone')
    logger.info('Milestone')
    logger.warning('Milestone')
    logger.error('Milestone')

The output depends on the configuration of the logging system.
For Example 2 outputs,

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
import functools
import inspect
import logging.config, logging.handlers
import os
from pathlib import Path
# import pprint
import queue
try:
    # tomllib is included in the Python Standard Library since version 3.11
    import tomllib  # type: ignore
except ModuleNotFoundError:
    import tomli as tomllib  # A lil' TOML parser
from typing import Dict, List

# Related third party imports.
import yaml  # PyYAML, YAML parser and emitter for Python

# Local application/library specific imports.
from LabGym import config


logger = logging.getLogger(__name__)

# In general or production use, module attributes raiseExceptions and
# prehandle_logrecords should be False.
#
# During development or maintenance of this module,
# To assist debugging during development or maintenance, defeat the
# suppression of exceptions by setting raiseExceptions to True.
raiseExceptions = False
prehandle_logrecords = False

development_mode = False
if development_mode:
    # Defeat the suppression of exceptions.
    raiseExceptions = True  # for development only
    # Handle manually-created logrecords early (and again normally).
    prehandle_logrecords = True  # for development only


# _mywarning -- Return a WARNING LogRecord for a string or exception.
# _mydebug -- Return a DEBUG LogRecord for a string or exception.
#
# Example
#     logrecords = []
#     ...
#     logrecords.append(_mydebug('Milepost'))
#     try:
#         logrecords.append(_mydebug('Trying...'))
#         ...
#         logrecords.append(_mydebug('Succeeded'))
#     except Exception as e:
#         # log the exception as a warning and continue
#         logrecords.append(_mywarning(
#             f'Continuing after non-fatal exception: {e}'))

def _myLogRecord(myobj: str | Exception, level: int) -> logging.LogRecord:
    """Return a LogRecord for a string or exception."""

    lineno = inspect.stack()[2].lineno  # type: ignore

    logrecord = logging.LogRecord(
        level=level,
        msg="%s", args=(f'{myobj}',),
        lineno=lineno,
        exc_info=None, name=__name__, pathname=__file__,
        )

    if prehandle_logrecords and level >= logger.getEffectiveLevel():
        # for development only
        #
        # In general or production use, handling of this logrecord
        # should be performed only later, after configuring logging.
        #
        # To assist debugging during development or maintenance of this
        # module, handle this logrecord now also (producing redundant
        # output).
        logger.handle(logrecord)  # for development only

    return logrecord


def _mywarning(myobj: str | Exception) -> logging.LogRecord:
    """Return a WARNING LogRecord for a string or exception."""
    return _myLogRecord(myobj, level=logging.WARNING)


def _mydebug(myobj: str | Exception) -> logging.LogRecord:
    """Return a DEBUG LogRecord for a string or exception."""
    return _myLogRecord(myobj, level=logging.DEBUG)


def get_configdict_from_configfile(configfile: Path) -> Dict:
    """Read the configfile and return the config dictionary."""
    if configfile.name.endswith('.toml'):
        with open(configfile, 'rb') as f:
            result = tomllib.load(f)
    elif configfile.name.endswith('.yaml'):
        with open(configfile, 'r', encoding='utf-8') as f:
            result = yaml.safe_load(f)
    else:
        raise Exception(f'bad extension.  configfile: {configfile}')

    return result


def catch_exceptions_and_warn(wrappee):
    """Guard from exceptions.

    Wrap a function to catch an exception and log a warning.

    In general use, raiseExceptions should be False.

    During development or maintenance of this module, for debugging
    purposes, set raiseExceptions to True.
    When this module's raiseExceptions module attribute is True, an
    exception caught by this wrapper will be re-raised, with the
    original traceback preserved, to identify the location where the
    error originated.
    """
    @functools.wraps(wrappee)
    def wrapper(*args, **kwargs):
        assert isinstance(raiseExceptions, bool)
        try:
            return wrappee(*args, **kwargs)
        except Exception as e:
            logger.warning(
                'Continuing after non-fatal exception'
                f" in '{wrappee.__name__}'.  ({e})")
            if raiseExceptions:
                # during development/maintenance, re-raise to id location
                raise
    return wrapper


@catch_exceptions_and_warn  # Guard from exceptions.
def configure() -> None:
    """
    Configure logging based on configfile, then handle list of logrecords.

    (1) Initialize with logging module's basicConfig(), raiseExceptions,
        and captureWarnings().
    (2) Configure the logging system based on settings from a configfile.
    (3) Honor command-line args that override the root logger level.
    (4) After configuring, handle each logrecord in the list of
        accumulated logrecords.


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

    # (1) Initialize ...

    # initialize the logging system.
    # Remove pre-existing handlers from root logger, then basicConfig().
    logging.getLogger().handlers = []
    logging.basicConfig(level=logging.DEBUG)
    defer()


    # Set logging.raiseExceptions to False.
    # (Why?  Because we want to ignore handler emit exceptions.)
    logging.raiseExceptions = False

    # Redirect warnings issued by the warning module to the logging system.
    logging.captureWarnings(True)

    # (2) Configure the logging system based on settings from a configfile.
    try:
        # logrecords is a list of not-yet-handled log records

        # Get all of the values needed from config.get_config().
        _config = config.get_config()
        logging_configfiles: List[Path] = _config['logging_configfiles']
        logging_configfile: Path|None = _config.get('logging_configfile')
        logging_levelname: str|None = _config.get('logging_levelname')

        # if the config defines a specific logging_configfile, only
        # attempt to use it.  Otherwise, step through the list of
        # logging_configfiles and try them until success.

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
                    f'  ({e})'))

        else:
            # none of the logging_configfiles were suitable
            logrecords.append(_mywarning(
                'No suitable logging configfile found.'))

    except Exception as e:
        # log the exception as a warning
        logrecords.append(_mywarning(
            f'Trouble configuring the logging system.  ({e})'))

    # (3) Honor command-line args that override the root logger level.
    try:
        if logging_levelname is not None:
            logrecords.append(_mydebug(
                f'logging_levelname: {logging_levelname}'))
            logging.getLogger().setLevel(getattr(logging, logging_levelname))

    except Exception as e:
        # log the exception as a warning
        logrecords.append(_mywarning(
            f'Trouble overriding root logger level.  ({e})'))

    # (4) After configuring, handle each logrecord in the list of
    #     accumulated logrecords.
    _handle(logrecords)  # Process the manually created logrecords


@catch_exceptions_and_warn  # Guard from exceptions.
def _handle(logrecords: List[logging.LogRecord]) -> None:
    """For each logrecord, have its named logger handle it.

    Arg logrecords is a list of log records that were created manually
    (instead of by a logger method) without handling, before the logging
    system was configured.
    Now, presumably logging has been configured, so for each log record,
    have its named logger handle it based on the current logging
    configuration.
    """

    for logrecord in logrecords:
        logger = logging.getLogger(logrecord.name)
        if logrecord.levelno >= logger.getEffectiveLevel():
            logger.handle(logrecord)


@catch_exceptions_and_warn  # Guard from exceptions.
def defer():
    """Ensure logrecords are being queued.

- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    Collect logrecords in a queue for handling after configuration.

    Collect logrecords in a queue for handling after the logging system
    has been been configured.

    The intention is, for the time being,
    collect logrecords in a queue without filtering,
    and defer handling, with the intention of handling them after the
    logging system is configured.

    If handlers is an empty list, or contains only a nullhandler, then
        add a queuehandler
    elif handlers contains a queuehandler (and optionally others, like
    else
         unexpected
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    """

    rootlogger = logging.getLogger()

    # Check if any of rootlogger's handlers is a QueueHandler.
    contains_queuehandler = any(
        isinstance(handler, logging.handlers.QueueHandler)
        for handler in rootlogger.handlers
        )

    if not contains_queuehandler:
        rootlogger.setLevel(logging.NOTSET)

        logrecord_queue = queue.Queue(-1)  # -1 for an unbounded queue
        queue_handler = logging.handlers.QueueHandler(logrecord_queue)
        rootlogger.addHandler(queue_handler)

        # During dev, handle logrecords immediately also (producing
        # redundant output).
        dev_handler = logging.StreamHandler()
        dev_handler.setFormatter(
            logging.Formatter(f'DEV {logging.BASIC_FORMAT}'))
        rootlogger.addHandler(dev_handler)

        logger.debug('Added a QueueHandler to root logger.')

    logger.debug('%s: %r', 'rootlogger.handlers', rootlogger.handlers)
    logger.debug('%s: %r', 'rootlogger.level', rootlogger.level)
