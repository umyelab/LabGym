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
from typing import List


# class LabGymError(Exception): pass


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

    If the help option is encountered, print the help message and exit 0.

    If a usage error is recognized, then print the error message and the
    help message to stderr, and exit 1.

    Notes
    *   This function operates on a copy of sys.argv and leaves sys.argv
        unchanged.

    *   Command-line args are processed left-to-right.
        If an option is specified more than once, then the rightmost
        specification overrides those to its left.

    *   An arg going through the pattern matching... if it doesn't begin
        with '-', it is considered the first positional command-line arg
        and ends the option processing.  The list of positional args
        remaining after option processing is stored in valobj.args.

    *   A '--' arg is recognized as separating options from positional
        command-line args.  It's used if the first positional command-
        line arg starts with '-', to prevent processing it as an option.
    """

    valobj = Values()

    args = sys.argv[:]  # operate on a copy of sys.argv

    valobj.cmd = args[0]
    basename = os.path.basename(args[0])  # basename used for help msg
    args = args[1:]  # shift 1

    helpmsg = f"""
Usage: {basename} [options]

Options:
  --loggingconfig FILE  Use the toml- or yaml- file FILE to configure
                        the logging system.
  --logginglevel LEVEL  Set the root logger's level to logging.LEVEL,
                        where LEVEL is a level recognized by the logging
                        system, like ERROR, WARNING, INFO, or DEBUG.
  --debug               Equivalent to --logginglevel DEBUG.
  -v, --verbose         Equivalent to --logginglevel DEBUG.
  -h, --help            Show this help message and exit.
        """.strip()

    while len(args) > 0:
        arg = args[0]

        # For arg value match expressions below, prefer value-in-list
        # instead of value-in-tuple.

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
            # print help msg and exit
            print(helpmsg)
            sys.exit()

        elif arg == '--':
            # break out of options processing
            args = args[1:]  # shift 1
            break

        elif arg.startswith('-'):
            # unrecognized option.  Print msgs to stderr and exit 1.
            sys.exit(
                f'{basename}: bad usage -- unrecognized option {arg}'
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


# def error(msg: str) -> None:
#     print(f'ERROR: {msg}', file=sys.stderr)
#     sys.exit(1)
