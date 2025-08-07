"""Provide function parse_args for parsing sys.argv (custom implementation).

What about repeated settings within command-line args?
*   Processed left to right.

*   In this implementation, rightmost overrides those to the left,
    except --enable and --disable, which for different featurenames
    accumulates in the enable dict
    For example,
        --enable F1 --enable F2 --disable F1
    accumulates to enable dict {'F1': False, 'F2': True}
    Two -v args does not select more verbosity.
"""

# Allow use of newer syntax Python 3.10 type hints in Python 3.9.
from __future__ import annotations

# Standard library imports.
import os
import sys
import textwrap
from typing import List, Union, Dict, Any

# Local application/library specific imports.
# import LabGym.__version__ as version
from LabGym import __version__ as version


# result is a dict with keys that are string, and vals that are
# string or bool or a dict of str,bool items.
ResultType = Dict[str, Union[
    # Path,  # configdir, configfile, logging_configfile (specific)
    str,  # configdir, configfile, logging_configfile (specific)
    # List[Path], # logging_configfiles (potentials)
    List[str], # logging_configfiles (potentials)
    str,  # logging_level
    bool,  # anonymous
    Dict[str, bool],  # enable
    ]]

def parse_args() -> ResultType:
    """Parse command-line args and return a dict.

    If the help option is encountered, print the help message and
    exit 0.
    If the version option is encountered, print the version message and
    exit 0.

    If a usage error is recognized, then print the error message and the
    help message to stderr, and exit 1.

    The --enable FEATURE and --disable FEATURE provide a risk-mitigated
    approach to the introduction of new features or behaviors.
    Introduce the feature defaulting to disabled, and support user
    opt-in.
    After achieving confidence in the feature, change the default to
    enabled, and support user opt-out.

    Notes
    *   This function operates on a copy of sys.argv and leaves sys.argv
        unchanged.

    *   Command-line args are processed left-to-right.
        If an option is specified more than once, then the rightmost
        specification overrides those to its left.

    *   As an arg is going through the pattern matching... if it doesn't
        begin with '-', it is considered the first positional command-
        line arg, and ends the option processing.

    *   A '--' arg is recognized as separating options from positional
        command-line args.  The '--' arg is necessary if the first
        positional command-line arg starts with '-', to prevent
        processing it as an option.
    """

    args = sys.argv[:]  # operate on a copy of sys.argv

    cmd = args[0]
    basename = os.path.basename(cmd)  # basename is used for help msg
    args = args[1:]  # shift 1

    helpmsg = textwrap.dedent(f"""\
        Usage: {basename} [options]

        Options:
          --anonymous           Send only anonymized stats to the
                                central receiver.
          --configdir DIR       Find LabGym config files in the config
                                dir (default '~/.labgym')
          --configfile FILE     LabGym config file (default 'config.toml')
          --enable FEATURE      Enable FEATURE.
          --debug               Equivalent to --logging_level DEBUG.
          --disable FEATURE     Disable FEATURE.
          -h, --help            Show this help message and exit.
          --logging_configfile FILE    Use FILE to configure the logging
                                system instead of trying the defaults.
          --logging_level LEVEL    Set the root logger's level to LEVEL,
                                where LEVEL is a term recognized by the
                                logging system, like DEBUG, INFO,
                                WARNING, or ERROR.
          -v, --verbose         Equivalent to --logging_level DEBUG.
          --version             Show the LabGym version and exit.
        """)

    result: ResultType = {}

    while len(args) > 0:
        arg = args[0]

        # For arg value match expressions below, prefer value-in-list
        # instead of value-in-tuple.
        #
        # Why?  A value-in-tuple expression works fine.  But if an
        # intended 1-tuple of strings is erroneously constructed without
        # the trailing comma, it is syntactically legitimate but is a
        # naked string instead of a 1-tuple, and matches not only the
        # full string, but also substrings.
        # The expression
        #     arg in ('--foo')
        # is True for '--foo', but also for the substrings like
        # '--', '--f', '-f', and 'foo', which is bad.

        # custom options
        if arg in ['--anonymous']:
            result['anonymous'] = True
            args = args[1:]  # shift 1

        elif arg in ['--configdir']:
            result['configdir'] = args[1]
            args = args[2:]  # shift 2

        elif arg in ['--configfile']:
            result['configfile'] = args[1]
            args = args[2:]  # shift 2

        elif arg in ['--enable']:
            if result.get('enable') is None:
                 result['enable'] = {}
            result.get('enable').update({args[1]: True})
            args = args[2:]  # shift 2

        elif arg in ['--disable']:
            if result.get('enable') is None:
                 result['enable'] = {}
            result.get('enable').update({args[1]: False})
            args = args[2:]  # shift 2

        elif arg in ['--logging_configfile']:
            result['logging_configfile'] = args[1]
            args = args[2:]  # shift 2

        elif arg in ['--logging_level']:
            result['logging_level'] = args[1]
            args = args[2:]  # shift 2

        elif arg in ['--debug', '-v', '--verbose']:
            result['logging_level'] = 'DEBUG'
            args = args[1:]  # shift 1

        # standard options
        elif arg in ['-h', '--help']:
            # Print help msg to stdout and exit 0.
            print(helpmsg)
            sys.exit()

        elif arg in ['--version']:
            # Print version msg to stdout and exit 0.
            print(f'version: {version}')
            sys.exit()

        elif arg == '--':
            # break out of options processing
            args = args[1:]  # shift 1
            break

        elif arg.startswith('-'):
            # unrecognized option.  Print msgs to stderr and exit 1.
            sys.exit(
                f'{basename}: bad usage -- unrecognized option {arg!r}'
                f'\n{helpmsg}')

        else:
            # milepost -- reached the end of options
            break

    # At this point,
    #   result is a dict of settings obtained from command-line options
    #   args is a list of command-line args remaining after options processing
    #   cmd is the original command (sys.argv[0])
    #   basename is basename(cmd)

    # Sanity check remaining args before returning.
    nargs = len(args)
    if nargs != 0:
        # unexpected args.  Print msgs to stderr and exit 1.
        sys.exit(
            f'{basename}: bad usage -- '
            f'takes 0 args after options, but {nargs} were found.'
            f'\n{helpmsg}')

    return result
