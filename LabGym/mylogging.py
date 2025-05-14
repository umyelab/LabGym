"""Provide functions for configuring the logging system.

Functions
    config -- Configure logging based on configfile, or fall back to
        basicConfig().
    handle -- Use the root logger's handle method to handle each logrecord.

Example 1
    # Configure the logging system.
    import LabGym.mylogging as mylogging
    mylogging.config()

Example 2, handle logrecords created during the call to config
    # Configure the logging system.
    import LabGym.mylogging as mylogging
    logrecords = []
    mylogging.config(logrecords)
    mylogging.handle(logrecords)

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
        level=logging.DEBUG, exc_info=None, name=__name__, pathname=__file__,
        msg='%s', args=(f'loading {__file__}',),
        )]
    import LabGym.mylogging as mylogging
    mylogging.config(logrecords)
    mylogging.handle(logrecords)
    logger = logging.getLogger(__name__)
    logger.debug('milestone')

The output depends on the configuration.
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

Strengths & Weaknesses
This module is written to log exceptions and discard them instead of propagate/re-raise them.  Why?  Because the logging is not strictly necessary, so logging trouble should not be fatal.

How can this module produce an exception?  The exposed function, config, is
wrapped in try/expect to avoid producting an exception.  But importing this module could produce an exception if its imports (tomllib or tomli, and yaml),
"""

# standard library imports
import inspect
import logging.config
import os
import pprint
import sys
try:
    # tomllib is included in the Python Standard Library since version 3.11
    import tomllib  # type: ignore
except ModuleNotFoundError:
    import tomli as tomllib
# from typing import Union

# related third party imports
import yaml


# _mywarning -- Return a WARNING LogRecord for a string or exception.
# _mydebug -- Return a DEBUG LogRecord for a string or exception.
#
# Example
#     logrecords = [_mydebug('Milepost')]
#     try:
#         logrecords.append(_mydebug('Trying...')
#         ...
#     except Exception as e:
#         # log the exception as a warning
#         # log another message as a warning
#         logrecords.append(_mywarning(e))
#         logrecords.append(_mywarning('Trouble...'))
#
def _myLogRecord(myobj: str|Exception, level: int) -> logging.LogRecord:
    """Return a LogRecord for a string or exception."""
    lineno = inspect.stack()[2].lineno  # type: ignore

    return logging.LogRecord(
        level=level,
        msg="%s", args=(f'{myobj}',),
        lineno=lineno,
        exc_info=None, name=__name__, pathname=__file__,
        )


def _mywarning(myobj: str|Exception) -> logging.LogRecord:
    """Return a WARNING LogRecord for a string or exception."""
    # print(f'W: {myobj}')
    return _myLogRecord(myobj, level=logging.WARNING)


def _mydebug(myobj: str|Exception) -> logging.LogRecord:
    """Return a DEBUG LogRecord for a string or exception."""
    # print(f'D: {myobj}')
    return _myLogRecord(myobj, level=logging.DEBUG)


def get_val_from_sysargv(key: str) -> str|None:
    """Return option value if specified in sys.argv, or return None.

    *   Args following a '--' arg are not processed as options.
        A '--' is recognized as separating options from required
        positional command-line args.
    *   If key/value pair is specified more than once, return the last
        value.
    *   Operate on a copy of sys.argv, leave sys.argv intact.

    Weaknesses
    *   This function can mishandle the args, because it treats all
        unrecognized args as single-arg options, despite the general
        case that there may be double-arg options present.
    """

    val = None
    myargs = sys.argv[1:]  # my copy of command-line args

    while len(myargs) > 0:
        myarg = myargs[0]
        if myarg == f'--{key}':
            val = myargs[1]
            myargs = myargs[2:]  # shift 2
        elif myarg.startswith(f'--{key}='):
            val = myarg[len(f'--{key}='):]
            myargs =  myargs[1:]  # shift 1
        elif myarg == '--':
            myargs = myargs[1:]  # shift 1
            break
        else:
            myargs = myargs[1:]  # shift 1

    return val


def get_logginglevel_from_sysargv():
    """Return logginglevel if specified by sys.argv, or return None."""

    key = 'logginglevel'
    val = None
    myargs = sys.argv[1:]  # my copy of command-line args

    while len(myargs) > 0:
        myarg = myargs[0]
        if myarg == f'--{key}':
            val = myargs[1]
            myargs = myargs[2:]  # shift 2
        elif myarg.startswith(f'--{key}='):
            val = myarg[len(f'--{key}='):]
            myargs =  myargs[1:]  # shift 1
        elif myarg == '--debug' or myarg == '--verbose' or myarg == '-v':
            val = 'DEBUG'
            myargs =  myargs[1:]  # shift 1
        elif myarg == '--':
            myargs = myargs[1:]  # shift 1
            break
        else:
            myargs = myargs[1:]  # shift 1

    return val


def get_configfile(logrecords):
    """Return the path to a logging configfile.

    In decreasing precedence:
        1.  specified by command-line arg (--loggingconfig path)
        2.  in the current dir of the process, that is, getcwd()
        3.  in a config dir in the user's home dir, that is, $HOME/.__package__
        4.  in this module file's dir, that is, dirname(__file__)
    """

    try:
        configfile = get_val_from_sysargv('loggingconfig')
        if configfile is not None:
            return configfile
    except Exception as e:
        # log the exception and a string as warnings, then continue
        logrecords.append(_mywarning(e))
        logrecords.append(_mywarning(
            'Trouble parsing command-line for --loggingconfig path.'))

    # Milepost: No configfile was specified on command-line.

    # Prepare a list of configfile paths to iterate through, in these dirs
    #     (a) cwd
    #     (b) $HOME/.mypkg
    #     (c) in this module file's dir
    configfiles = [
        os.path.join(os.getcwd(), 'logging.toml'),
        os.path.join(os.getcwd(), 'logging.yaml'),
        ]

    try:
        home = os.environ.get('HOME')
        configfiles.extend([
            os.path.join(home, f'.{__package__}', 'logging.toml'),
            os.path.join(home, f'.{__package__}', 'logging.yaml'),
            os.path.join(home, f'.{__package__.lower()}', 'logging.toml'),
            os.path.join(home, f'.{__package__.lower()}', 'logging.yaml'),
            ])
    except:
        # HOME isn't set, so skip $HOME/.labgym and
        pass

    configfiles.extend([
        os.path.join(os.path.dirname(__file__), 'logging.toml'),
        os.path.join(os.path.dirname(__file__), 'logging.yaml'),
        ])

    # Step through the list and return the first that exists.
    for configfile in configfiles:
        if os.path.exists(configfile):
            return configfile

    # Milepost: No configfile has been found, so raise an exception.
    try:
        raise Exception('no configfile found')
    except Exception as e:
        # log the exception and re-raise
        logrecords.append(_mywarning(e))
        raise


def get_configdict(configfile, logrecords):
    """Read the configfile and return the config dictionary."""
    if configfile.endswith('.toml'):
        with open(configfile, 'rb') as f:
            configdict = tomllib.load(f)
    elif configfile.endswith('.yaml'):
        with open(configfile, 'r') as f:
            configdict = yaml.safe_load(f)
    else:
        raise Exception('bad extension -- configfile: {configfile!r}')

    return configdict


def _config(logrecords):
    """Configure logging based on configfile.

    # Get the path to a configfile.
    # Get the config dictionary from the configfile.
    # Apply the configdict.

    Append any new log records to logrecords, for later handling.

    Args
      logrecords -- a list of not-yet-handled log records
    """

    # Get the path to a configfile.
    configfile = get_configfile(logrecords)
    logrecords.append(_mydebug(f'configfile: {configfile!r}'))

    # Get the config dictionary from the configfile.
    configdict = get_configdict(configfile, logrecords)
    logrecords.append(_mydebug(
        'function get_configdict returned a result'))
    # logrecords.append(_mydebug(
    #     f'configdict:\n{pprint.pformat(configdict, indent=2)}'))

    # Apply the configdict.
    logging.config.dictConfig(configdict)


def config(*args):
    """Configure logging based on configfile, or fall back to basicConfig().

    Args
      logrecords -- a list of not-yet-handled log records

    (1) If a logging congfigfile was specified by command-line args, then
        try to configure logging with it.

        Otherwise, a logging configfile was not specified by command-line
        args, so iterate through a list of standard locations, and try to
        configure logging with the first found to exist.
        The list of standard locations ends with mypkg/logging.yaml.

        If an exception is raised, then call logging.basicConfig(level=
        logging.DEBUG) to configure logging.

    (2) After configuring per (1), honor command-line args that
        override the root logger level (-v, --verbose, --logginglevel DEBUG).

    While performing this work, append any new log records to
    logrecords (for later handling).
    ---

    This function guards against raising an exception.
    """
    try:
        if len(args) == 1:
            logrecords = args[0]
        elif len(args) == 0:
            logrecords = []
        else:
            raise Exception('bad usage')


        # (1) Configure logging based on configfile, or fall back to basicConfig().
        try:
            _config(logrecords)
        except Exception as e:
            # log the exception as a warning
            # log another message as a warning
            # call basicConfig
            logrecords.append(_mywarning(e))
            logrecords.append(_mywarning(
                'Trouble configuring logging.  '
                'Calling logging.basicConfig(level=logging.DEBUG)'))

            logging.basicConfig(level=logging.DEBUG)

        # (2) Honor command-line args that override the root logger level.
        try:
            levelname = get_logginglevel_from_sysargv()
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
        # Ignore unexpected exceptions
        logging.basicConfig()
        logging.error('Ignoring unexpected but benign exception while '
            'configuring logging, ' f'e: {e!r}')


def handle(logrecords):
    """Use the root logger's handle method to handle each logrecord.

    This function guards against raising an exception.
    """

    try:
        rootlogger = logging.getLogger()
        for logrecord in logrecords:
            # effectivelevel of the logger to which the logrecord was attributed
            effectivelevel = logging.getLogger(logrecord.name).getEffectiveLevel()
            if logrecord.levelno >= effectivelevel:
                rootlogger.handle(logrecord)
    except Exception as e:
        logging.error('Ignoring unexpected but benign exception while '
            'handling logrecords, ' f'e: {e!r}')
