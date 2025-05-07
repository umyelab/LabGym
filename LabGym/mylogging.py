"""

Example, in the __init__.py for package "mypkg", this
  1 # standard library imports
  2 import logging
  3 
  4 # Log the load of this module (by the module loader, on first import).
  5 # Create the log record manually, because logging isn't configured yet.
  6 # print(f'DEBUG\tloading {__file__}')
  7 logrecords = [logging.LogRecord(
  8     level=logging.DEBUG, msg='loading %s', args=(__file__),
  9     lineno=7, exc_info=None, name=__name__, pathname=__file__,
 10     )]
 11 # print(f'DEBUG\t__name__: {repr(__name__)}')
 12 # logrecords.append(logging.LogRecord(
 13 #     level=logging.DEBUG, msg='%s: %r', args=('__name__', __name__),
 14 #     lineno=12, exc_info=None, name=__name__, pathname=__file__,
 15 #     ))
 16 
 17 # local application/library specific imports
 18 import mypkg.mylogging as mylogging
 19      
 20 # Configure logging, and append any new log records to logrecords.
 21 try:
 22     mylogging.config(logrecords, myname=__name__)
 23 except:
 24     # raise  # for debugging mylogging.config()
 25     # print(f'WARNING\ttrouble configuring logging')
 26     logrecords.append(logging.LogRecord(
 27         level=logging.WARNING,
 28         msg='trouble configuring logging', args=None,
 29         lineno=26, exc_info=None, name=__name__, pathname=__file__,
 30         ))  
 31      
 32     logging.basicConfig(level=logging.DEBUG)
 33  
 34 # Now that logging is configured, handle the manually created log records.
 35 handle = logging.getLogger().handle  # the root logger's handle method
 36 for logrecord in logrecords:
 37     # get the effectivelevel of the logger to which the record was attributed
 38     effectivelevel = logging.getLogger(logrecord.name).getEffectiveLevel()
 39     if logrecord.levelno >= effectivelevel:
 40         handle(logrecord)
 41      
 42 # raise Exception('intentional abend')

outputs (after logging is configured):
(1) if mypkg/logging.yaml specifies root logger level=INFO, then
    (no logrecords output)

(2) if mypkg/logging.yaml specifies root logger level=DEBUG, then
    2025-05-06 14:06:19       DEBUG   [4544087552:mypkg:__init__:7] loading /Users/john/work/mypkg/__init__.py
    2025-05-06 14:06:19       DEBUG   [4544087552:mypkg:mylogging:23]        configfile: '/Users/john/work/mypkg/logging.yaml'
    2025-05-06 14:06:19       DEBUG   [4544087552:mypkg:mylogging:32]        configdict: {'version': 1, 'formatters': {'myformat': {'datefmt': '%Y-%m-%d %H:%M:%S', 'format': '%(asctime)s\t%(levelname)s\t[%(thread)d:%(name)s:%(module)s:%(lineno)d]\t%(message)s'}}, 'handlers': {'console': {'class': 'logging.StreamHandler', 'formatter': 'myformat'}}, 'root': {'handlers': ['console'], 'level': 'DEBUG'}, 'loggers': {'h5py': {'level': 'INFO'}, 'matplotlib.font_manager': {'level': 'INFO'}, 'urllib3.connectionpool': {'level': 'INFO'}}, 'disable_existing_loggers': False}

(3) if mypkg/logging.yaml is missing, then
    DEBUG:mypkg:loading /Users/john/work/mypkg/__init__.py
    DEBUG:mypkg:configfile: '/Users/john/work/mypkg/logging.yaml'
    WARNING:mypkg:trouble configuring logging
"""

# standard library imports
import logging.config
import os

# related third party imports
import yaml


def config(logrecords, myname=None):
    """Configure logging, and append any new log records to logrecords.

    logrecords -- a list of log records, which can be appended with new
        log records, for later handling
    myname -- the name of the logger in new log records
    """

    # Configure logging per logging.yaml
    configfile = os.path.join(os.path.dirname(__file__), 'logging.yaml')
    # print(f'configfile: {configfile!r}')
    logrecords.append(logging.LogRecord(
        level=logging.DEBUG,
        msg='%s: %r', args=('configfile', configfile),
        lineno=23, exc_info=None, name=myname, pathname=__file__,
        ))

    with open(configfile) as f:
        configdict = yaml.safe_load(f)
    # print(f'configdict: {configdict!r}')
    logrecords.append(logging.LogRecord(
        level=logging.DEBUG,
        msg='%s: %r', args=('configdict', configdict),
        lineno=32, exc_info=None, name=myname, pathname=__file__,
        ))

    logging.config.dictConfig(configdict)
