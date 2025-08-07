"""Provide functions to obtain the configuration values.

Configuration evaluation involves (ordered in increasing precedence)
    1.  hardcoded defaults
    2.  configuration file settings
    3.  environment variables
    4.  command-line options

Notes
*   Environment variables and command-line options can be used to 
    override the location of the configuration file, so determine the 
    configuration file location before reading it.

*   Typical LabGym configdir organization is
        ~/.labgym/config.toml  (optional)
                  logging.yaml  (optional)
                  registration.done  (created at registration)

    To use a different configfile only (without changing the references
    to other configdir files),
    use command-line args like
        LabGym --configfile ~/alt_config.toml
    or assign an environment variable before running LabGym, like
        export LABGYM_CONFIGFILE=~/alt_config.toml
"""

# Allow use of newer syntax Python 3.10 type hints in Python 3.9.
from __future__ import annotations

# Standard library imports.
import configparser
import copy
import logging
import os
from pathlib import Path
import pprint
import sys
try:
    # tomllib is included in the Python Standard Library since version 3.11
    import tomllib  # type: ignore
except ModuleNotFoundError:
    import tomli as tomllib  # A lil' TOML parser

# Related third party imports.
import yaml  # PyYAML, YAML parser and emitter for Python

# Local application/library specific imports.
from LabGym import myargparse


defaults = {
    'configdir': Path.home().joinpath('.labgym'),  # ~/.labgym
    'configfile': Path('config.toml'),  # relative path

    'logging_configfiles': [  # list of paths
        Path('logging.toml'),  # relative path
        Path('logging.yaml'),  # relative path
        Path(__file__).parent.joinpath('logging.yaml'),  # LabGym/logging.yaml
        ],
    # intentionally, no default specified here for logging_configfile
    # intentionally, no default specified here for logging_level

    'enable': {
        'central_logger': True,  # to disable central logger, user must opt out
        'registration': True,  # to disable registration, user must opt out
        },

    'anonymous': False,
}

logger = logging.getLogger(__name__)

_cached_config = None


def get_config_from_argv() -> dict:
    """Get config values from command-line args."""

    result = myargparse.parse_args()

    return result


def get_config_from_environ() -> dict:
    """Get config values from os.environ.

    Weaknesses
    *   Environment variables are case-sensitive.  
        There could be a collision when mapping names to lowercase, 
        which should generate a warning or an exception, but that is not 
        implemented.
        As implemented, the retained value is the value of the 
        environment variable whose name sorts higher.
    """
    prefix = 'LABGYM_'
    result = {name.removeprefix(prefix).lower(): value 
        for name, value in sorted(os.environ.items()) if name.startswith(prefix)}
    return result


def get_config_from_configfile(configfile: Path) -> dict:
    """Get config values from a configfile."""

    assert os.path.isabs(configfile)

    if not configfile.is_file():
        logger.debug('%s: %s', configfile, 'file not found')
        return {}

    # An existing but unreadable or defective configfile is fatal.
    try:
        if configfile.name.endswith('.ini'):
            parser = configparser.ConfigParser()
            result = parser.read(configfile)
        elif configfile.name.endswith('.toml'):
            with open(configfile, 'rb') as f:
                result = tomllib.load(f)
        elif configfile.name.endswith('.yaml'):
            # with open(configfile, 'r') as f:
            with open(configfile, 'r', encoding='utf-8') as f:
                result = yaml.safe_load(f)
        else:
            raise Exception('unsupported file extension')
    except Exception as e:
        logger.error(e)
        msg = f'Trouble reading configfile ({configfile})'
        sys.exit(msg)

    return result


def get_config():
    """Return a cached config dict. Construct it if necessary.

    Strengths
    *   Instead of reconstructing the config dict each time this 
        function is called, the config dict is determined the first time 
        this function is run and then the function always returns the 
        same value without reconstructing it.
        This implementation uses the common approach of using a module-
        level variable to store the value after its initial creation.
        This pattern is often referred to as memoization or lazy 
        initialization.

    Weaknesses
    *   Each override could be logged.  
        The cost of implementation including unit test and complexity 
        and maintainability may exceed benefit.

    *   Provenances for all settings could be kept in a provenance 
        dictionary, and be logged before the function returns.
        The cost of implementation including unit test and complexity 
        and maintainability may exceed benefit.
    """

    global _cached_config

    if _cached_config is not None:
        return _cached_config

    # Milestone -- This must be the first time running this function.
    # Construct the config dict, cache it, and return it.

    config_from_argv = get_config_from_argv()

    config_from_environ = get_config_from_environ()

    provenance = {}  # some provenances of some vals
    # determine the configuration file location
    if config_from_argv.get('configdir'):
        configdir = Path(config_from_argv.get('configdir'))
    elif config_from_environ.get('configdir'):
        configdir = Path(config_from_environ.get('configdir'))
    else:
        provenance.update({'configdir': 'defaults'})
        configdir = defaults['configdir']
    assert isinstance(configdir, Path)

    if config_from_argv.get('configfile'):
        configfile = Path(config_from_argv.get('configfile'))
    elif config_from_environ.get('configfile'):
        configfile = Path(config_from_environ.get('configfile'))
    else:
        provenance.update({'configfile': 'defaults'})
        configfile = defaults['configfile']
    assert isinstance(configfile, Path)

    # # buffer some key/value pairs for late merge, to override.
    # buf = {'configdir': configdir, 'configfile': configfile} 

    if not os.path.isabs(configfile):
        configfile = configdir.joinpath(configfile)

    # A missing explicitly specified configfile is fatal.
    if not configfile.is_file() and provenance.get('configfile') != 'defaults':
        msg = f'Trouble reading user-specified configfile ({configfile})'
        sys.exit(msg)
            
    config_from_configfile = get_config_from_configfile(configfile)

    # Aggregate 4 dicts.  Use myupdate instead of dict update method.
    result = copy.deepcopy(defaults)  # this preserves the defaults dict
    myupdate(result, config_from_configfile)
    myupdate(result, config_from_environ)
    myupdate(result, config_from_argv)
    mypathexpand(result)  # replace relative paths with absolute paths

    # logger.debug('%s: %s', 'provenance', provenance)
    logger.debug('%s:\n%s', 'result', pprint.pformat(result))
    _cached_config = result
    return result


def myupdate(target: dict, addendum: dict) -> None:
    """..."""

    # if the addendum has 'enable' dict, then merge the existing 
    # target['enable'] into addendum['enable'] before target.update()

    if target.get('enable') is not None and addendum.get('enable') is not None:
        buf = {}
        buf.update(target['enable'])
        buf.update(addendum['enable'])
        addendum['enable'] = buf
    
    target.update(addendum)


def mypathexpand(target: dict) -> None:
    """
    For all items in the target that should be Path objects, ensure
    they are absolute paths.  
    Overrides from environment variables need to be converted from str 
    to Path, and, relative paths need to be anchored to configdir.
    """
    if not isinstance(target['configdir'], Path):
        target['configdir'] = Path(target['configdir'])
    configdir = target['configdir']
    assert configdir.is_absolute()

    if not isinstance(target['configfile'], Path):
        target['configfile'] = Path(target['configfile'])
    if not target['configfile'].is_absolute():
        target['configfile'] = configdir.joinpath(Path(target['configfile']))

    files = target['logging_configfiles']
    for i, item in enumerate(files):
        if not isinstance(files[i], Path):
            files[i] = Path(files[i])
        if not files[i].is_absolute():
            files[i] = configdir.joinpath(files[i])

    return
