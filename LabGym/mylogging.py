# pylint: disable=line-too-long
"""Provide functions for configuring the logging system.

Functions
    defer -- Ensure logrecords are being queued for later handling.
    configure -- Configure logging based on configfile, then handle
        deferred logrecords.

Strengths
  * The public functions (defer, configure) are guarded, to log
    exceptions as warnings, and discard them instead of propagate/
    re-raise them.
    Why?  Because for this sw, the logging is considered not-essential,
    so logging config trouble is intentionally not fatal.

Notes
  * The Python logging system allows the output of lower-level (like
    INFO) messages, despite the root logger set to higher-level (like
    WARNING).

    If the user supplies command line args which set logging_level to
    WARNING (like '--logging_level WARNING'), the root logger level is
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
    import logging

    # Configure the logging system.
    from LabGym.mylogging import mylogging
    mylogging.config()

    logger = logging.getLogger(__name__)
    logger.debug('Milestone')
    logger.info('Milestone')
    logger.warning('Milestone')
    logger.error('Milestone')

Example 2, Log the loading of this module, and configure the logging system.
    # Standard library imports.
    import logging
    ...

    # These statements are intentionally positioned before this module's
    # other imports (against the guidance of PEP 8), to log the loading of
    # this module before other import statements are executed and
    # potentially produce their own log messages.

    from LabGym import mylogging
    # Collect logrecords and defer handling until logging is configured.
    mylogging.defer()

    # Log the loading of this module (by the module loader, on first import).
    logger = logging.getLogger(__name__)
    logger.debug('loading %s', __file__)

    # Configure logging based on configfile, then handle collected logrecords.
    mylogging.configure()

    # Related third party imports.
    ...

    # Local application/library specific imports.
    ...

    logger.debug'%s: %r', '(__name__, __package__', (__name__, __package__))
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
    """Return a LogRecord for a string or for an exception."""

    lineno = inspect.stack()[2].lineno  # type: ignore

    logrecord = logging.LogRecord(
        level=level,
        msg="%s", args=(f'{myobj}',),
        lineno=lineno,
        exc_info=None, name=__name__, pathname=__file__,
        )

    return logrecord


def _mywarning(myobj: str | Exception) -> logging.LogRecord:
    """Return a WARNING LogRecord for a string or for an exception."""
    return _myLogRecord(myobj, level=logging.WARNING)


def _mydebug(myobj: str | Exception) -> logging.LogRecord:
    """Return a DEBUG LogRecord for a string or for an exception."""
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
    Configure logging based on configfile, then handle deferred logrecords.

    (1) Configure the logging system based on settings from a configfile.
    (2) Honor command-line args that override the root logger level.
    (3) Handle the collected/deferred logrecords
    """

    rootlogger = logging.getLogger()

    # Set logging.raiseExceptions to False.
    # (Why?  Because we want to ignore handler emit exceptions.)
    logging.raiseExceptions = False

    # Redirect warnings issued by the warning module to the logging system.
    logging.captureWarnings(True)

    # (1) Configure the logging system based on settings from a configfile.
    try:
        defer()  # Ensure logrecords are being queued.

        # (1) Get all of the values needed from config.get_config().
        _config = config.get_config()
        logging_configfiles: List[Path] = _config['logging_configfiles']
        logging_configfile: Path|None = _config.get('logging_configfile')
        logging_level: str|None = _config.get('logging_level')

        # Copy the queued logrecords to a list, and switch over to
        # manual logrecord creation until configuring is completed.
        logrecords = _get_logrecords_from_queue()

        # if the config defines a specific logging_configfile, then only
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
        # initialize the logging system.
        logrecords.append(_mywarning(
            f'Trouble configuring the logging system.  ({e})'))
        rootlogger.handlers = []
        logging.basicConfig(level=logging.DEBUG)

    # (2) Honor command-line args that override the root logger level.
    try:
        if logging_level is not None:
            logrecords.append(_mydebug(
                f'logging_level: {logging_level}'))
            rootlogger.setLevel(logging_level)

    except Exception as e:
        # log the exception as a warning
        logrecords.append(_mywarning(
            f'Trouble overriding root logger level.  ({e})'))

    # Milestone -- The logging system is configured.

    # (3) Handle the collected/deferred logrecords
    _handle(logrecords)


def _handle(logrecords: List[logging.LogRecord]) -> None:
    """For each collected/deferred logrecord, have its named logger handle it.

    Now, presumably the python logging system has been configured, so
    for each log record that was collected (with handling deferred),
    have its named logger handle it based on the current logging
    configuration.
    """

    for logrecord in logrecords:
        logger = logging.getLogger(logrecord.name)
        if logrecord.levelno >= logger.getEffectiveLevel():
            logger.handle(logrecord)


@catch_exceptions_and_warn  # Guard from exceptions.
def defer():
    """Ensure logrecords are being queued for later handling.

    After the specified logging configuration has been applied to the
    logging system, function _handle will be called to handle logrecords.
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

        # # During dev, handle logrecords immediately also (producing
        # # redundant output).
        # dev_handler = logging.StreamHandler()
        # dev_handler.setFormatter(
        #     logging.Formatter(f'DEV {logging.BASIC_FORMAT}'))
        # rootlogger.addHandler(dev_handler)

        logger.debug('Added a QueueHandler to root logger.')

    logger.debug('%s: %r', 'rootlogger.handlers', rootlogger.handlers)
    logger.debug('%s: %r', 'rootlogger.level', rootlogger.level)


def _get_logrecords_from_queue():
    """Return a list of logrecords that were queued by the rootlogger.

    Weaknesses:
    1.  The expected usage is that the rootlogger has exactly one
        QueueHandler.  This function could be more defensive regarding
        confirming that expectation.
    2.  The queue should be deleted and the handler removed from the
        rootlogger... but this will happen automatically, right?   When
        the logging system is configured, the handler will be unused and
        garbage collected along with its queue. (?)
    """

    rootlogger = logging.getLogger()

    for handler in rootlogger.handlers:
        if isinstance(handler, logging.handlers.QueueHandler):
            return list(handler.queue.queue)
    else:
        return []
