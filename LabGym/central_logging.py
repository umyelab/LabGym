"""Provide ...

Functions
    get_central_logger -- Return logger 'Central Logger', configured to
        send log records to an HTTP server.
"""

# Allow use of newer syntax Python 3.10 type hints in Python 3.9.
from __future__ import annotations

# Standard library imports.
import logging
import logging.handlers

# Related third party imports.
# None

# Local application/library specific imports.
from LabGym import config


http_handler_config = {
    # Host and optional port
    # 'host': 'localhost:8080',
    'host': 'solid-skill-463519-e0.appspot.com',  
    }

http_handler_config.update({
    'url': '/',  # URL path on the server
    'secure': True,  # Use HTTPS if needed
    'method': 'POST',  # Specify POST method

    # Optional basic authentication
    # 'credentials': ('username', 'password'),  
    })


def reset_central_logger(logger):
    """Reset the Central Logger.  (Useful during interactive dev.)"""
    assert logger.name == 'Central Logger'

    if hasattr(logger, 'configured'):
         delattr(logger, 'configured')

    logger.setLevel(logging.NOTSET)

    for h in logger.handlers:
        logger.removeHandler(h)

    logger.disabled = False
    logger.propagate = True


def get_central_logger(http_handler_config=http_handler_config, reset=False):
    """Return logger 'Central Logger', configured to send to an HTTP server.

    Return logger 'Central Logger', configured to send log records to an 
    HTTP server.
    
    Weakness:  This implementation uses an HTTPHandler, which waits 
        for the send to complete (or timeout).
        Consider using QueueHandler/QueueListener and
        multiprocessing.Queue to let handlers do their work on a 
        separate thread. 

    References 
    [1] search: python logging send to url http post
        https://www.google.com/search?q=python+logging+send+to+url+http+post

        "Python's built-in logging module can send log records to an HTTP
        server using the HTTPHandler class. This allows for centralized 
        log management by sending logs to a remote endpoint."

    Dev, with this file named sandbox.py
        >>> import importlib
        >>> import logging
        >>> logging.basicConfig()
        >>> import sandbox

        (edit/save sandbox.py)
        >>> importlib.reload(sandbox)
        >>> central_logger = sandbox.get_central_logger(reset=True)
        >>> central_logger.info({'name': 'Lyndon Baines Johnson', 'id': 36})
    """

    # Get all of the values needed from config.get_config().
    _config = config.get_config()
    central_logger_disabled: bool = not _config['enable']['central_logger']

    central_logger = logging.getLogger('Central Logger')

    if reset:
        reset_central_logger(central_logger)

    if getattr(central_logger, 'configured', False):
        return central_logger

    # Milepost: central_logger has not been configured yet.
    central_logger.setLevel(logging.INFO)

    # Prepare a handler.
    # An HTTPHandler doesn't use a Formatter, so using setFormatter() to 
    # specify a Formatter for an HTTPHandler has no effect.
    http_handler = logging.handlers.HTTPHandler(**http_handler_config)

    # Add the handler to the logger
    central_logger.addHandler(http_handler)

    central_logger.disabled = central_logger_disabled

    central_logger.configured = True

    return central_logger


if __name__ == '__main__':  # pragma: no cover
    logging.basicConfig(level=logging.INFO)

    central_logger = get_central_logger()

    reginfo = {
        'name': 'James Stewart', 
        'rank': 'Brigadier General',
        'serial number': 'O-433210',
        }

    logging.info(reginfo)
    central_logger.info(reginfo)
