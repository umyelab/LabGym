"""Provide functions to the intended configuration values.

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
    or an environment variable before running LabGym, like
        export LABGYM_CONFIGFILE=~/alt_config.toml
"""

"""
------------------------------------------------------------------------
clipboard
Redefinition of models and detectors dirs is not yet implemented.
Notes
    MODELS and DETECTORS dirs are easy for the user to override, by 
    several ways, including but not limited to, and ordered 
    from easier and stronger and less persistent,
    to harder (file-editing?), weaker (easier to override), and more persistent.

    1.  command-line key/value pair option like --models ~/tangerine-study/models
    2.  environment variable LABGYM_MODELS
    3.  models dir defined in ~/.labgym/config.toml
------------------------------------------------------------------------
"""

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
import yaml

# Local application/library specific imports.
from LabGym import myargparse

# regarding naming... 'enable' vs. 'enabled'.
# The argument in favor of 'enabled' is that it's a noun, the state that the
# user has specified.  But that's weak, it's not actually applied yet.  At
# this point it's not the state.
# The argument in favor of 'enable' is that it's a verb, it's the action that's
# been commanded.
# central_logger_disabled is so named because it follows the ...
# never mind... not worth it.  use --enable 'central_logger' to
# produce setting that drives central_logging.get_central_logger.disabled
#    

# Instead of merging defaults with explicit settings,
# Why not send them separately, to support different behavior at the point
# of use?  Or not separately, but rolled in as _defaults.
#     default_value = config.get_config().get('_defaults').get('mykey')
#     value = config.get_config().get('mykey')
#     if value is not None:
#         
# for path values, if a path is a relative path, then the using code should
# expand at time of use?  Or shall we do that here before returning, in an
# interpolation step?
# for a list of path values, usage might be, use first found, or use first 
# found that's not fouled, or use all existing...

defaults = {
    'configdir': Path.home().joinpath('.labgym'),  # ~/.labgym
    'configfile': Path('config.toml'),  # relative path

    'logging_configfiles': [  # list of paths
        Path('logging.toml'),  # relative path
        Path('logging.yaml'),  # relative path
        Path(__file__).parent.joinpath('logging.yaml'),  # LabGym/logging.yaml
        ],
    # intentionally, no default specified here for logging_configfile
    # intentionally, no default specified here for logging_levelname

    # for now, user must opt-in for central logging and registration
    'enable': {
        'central_logger': False,
        'registration': False,
        },

    'anonymous': False,
}

logger = logging.getLogger(__name__)


def get_config_from_argv() -> dict:
    """Get config values from command-line args."""

    # result = myargparse.parse_args().__dict__
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
        if configfile.endswith('.ini'):
            parser = configparser.ConfigParser()
            result = parser.read(configfile)
        elif configfile.endswith('.toml'):
            with open(configfile, 'rb') as f:
                result = tomllib.load(f)
        elif configfile.endswith('.yaml'):
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
    """Return a config dict.

    Weaknesses
    *   Some config values should accumulate, instead of override.
        If get_config_from_configfile()['enable'] returns
            {'newfeature1': True}
        and get_config_from_argv()['enable'] returns
            {'newfeature2': True}
        then get_config()['enable'] should return
            {'newfeature1': True, 'newfeature2': True}

        This is not yet implemented.  It could be implemented by
        employing something other than the dict update method for
        aggregation.  Or it could be implemented as a second op (after
        the existing naive aggregation) to replace certain values with 
        better ones.
        
    *   As presently implemented, the config dict is reconstructed each
        time this function is called.  A better approach would be to
        construct it once, with subsequent calls getting the original
        result returned.  Fortunately, this is a fairly fast function, 
        so improvement is not urgently needed.

    *   Each override could be logged.  
        The cost of implementation including unit test and complexity 
        and maintainability may exceed benefit.

    *   Provenances for all settings could be kept in a provenance 
        dictionary, and be logged before the function returns.
        The cost of implementation including unit test and complexity 
        and maintainability may exceed benefit.
    """

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
