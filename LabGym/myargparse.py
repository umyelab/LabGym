"""Provide function parse_args for parsing sys.argv (custom implementation).

Example
    import logging
    import myargparse

    vals = myargparse.parse_args()
    if vals.logginglevelname is not None:
        # set root logger level to vals.logginglevelname
        logging.getLogger().setLevel(getattr(logging, vals.logginglevelname))
"""

# standard library imports
# import logging
import os
import sys
import textwrap
from typing import List

# local application/library specific imports
import LabGym


class Values:
    """A Values object is packed with values as object attributes."""

    def __init__(self) -> None:
        self.loggingconfig: str | None = None
        self.logginglevelname: str | None = None
        # self.logginglevel: int | None = None

        self.cmd: str | None = None
        self.args: List[str] = []


def parse_args() -> Values:
    """Parse command-line args and return a Values object packed with results.

    If the help option is encountered, print the help message and
    exit 0.
    If the version option is encountered, print the version message and
    exit 0.

    If a usage error is recognized, then print the error message and the
    help message to stderr, and exit 1.

    Notes
    *   This function operates on a copy of sys.argv and leaves sys.argv
        unchanged.

    *   Command-line args are processed left-to-right.
        If an option is specified more than once, then the rightmost
        specification overrides those to its left.

    *   As an arg is going through the pattern matching... if it doesn't
        begin with '-', it is considered the first positional command-
        line arg and ends the option processing.  The list of positional
        args remaining after option processing is stored in valobj.args.

    *   A '--' arg is recognized as separating options from positional
        command-line args.  It's necessary if the first positional
        command-line arg starts with '-', to prevent processing it as an
        option.
    """

    valobj = Values()

    args = sys.argv[:]  # operate on a copy of sys.argv

    valobj.cmd = args[0]
    basename = os.path.basename(args[0])  # basename used for help msg
    args = args[1:]  # shift 1

    helpmsg = textwrap.dedent(f"""\
        Usage: {basename} [options]

        Options:
          --loggingconfig FILE  Use the toml- or yaml- file FILE to configure
                                the logging system.
          --logginglevel LEVEL  Set the root logger's level to logging.LEVEL,
                                where LEVEL is a level recognized by the
                                logging system, like ERROR, WARNING, INFO,
                                or DEBUG.
          --debug               Equivalent to --logginglevel DEBUG.
          -v, --verbose         Equivalent to --logginglevel DEBUG.
          --version             Show the LabGym version and exit.
          -h, --help            Show this help message and exit.
        """)

    while len(args) > 0:
        arg = args[0]

        # For arg value match expressions below, prefer value-in-list
        # instead of value-in-tuple.
        #
        # Why?  A value-in-tuple expression works fine.  But if an
        # intended 1-tuple of strings is erroneously constructed without
        # the trailing comma, it is syntactically legitimate but is a
        # naked string instead of a 1-tuple and matches not only the
        # full string, but also substrings.
        # The expression
        #     arg in ('--foo')
        # is True for '--foo', but also for the substrings like
        # '--', '--f', '-f', and 'foo', which is bad.

        # custom options
        if arg in ['--loggingconfig']:
            valobj.loggingconfig = args[1]
            args = args[2:]  # shift 2

        elif arg in ['--logginglevel']:
            valobj.logginglevelname = args[1]
            # valobj.logginglevel = getattr(logging, args[1])
            args = args[2:]  # shift 2

        elif arg in ['--debug', '-v', '--verbose']:
            valobj.logginglevelname = 'DEBUG'
            # valobj.logginglevel = logging.DEBUG
            args = args[1:]  # shift 1

        # standard options
        elif arg in ['-h', '--help']:
            # Print help msg to stdout and exit 0.
            print(helpmsg)
            sys.exit()

        elif arg in ['--version']:
            # Print version msg to stdout and exit 0.
            print(f'LabGym.__version__: {LabGym.__version__}')
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

    valobj.args = args  # store any args remaining after options processing

    nargs = len(valobj.args)

    if nargs != 0:
        # unexpected args.  Print msgs to stderr and exit 1.
        sys.exit(
            f'{basename}: bad usage -- '
            f'takes 0 args after options, but {nargs} were found.'
            f'\n{helpmsg}')

    return valobj
