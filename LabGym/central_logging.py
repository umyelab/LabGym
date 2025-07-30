"""Provide ...

Functions
    get_central_logger -- Return logger 'Central Logger', configured to
        send log records to an HTTP server.
"""

# Allow use of newer syntax Python 3.10 type hints in Python 3.9.
from __future__ import annotations

# Standard library imports.
import atexit
import logging
import logging.handlers
import queue

# Related third party imports.
# None

# Local application/library specific imports.
from LabGym import config


# cleanup should be registered with atexit if queueing is used.
def cleanup(queue_listener):
    try:
        # print('logging.shutdown(): Calling')
        logging.shutdown()  # ensure all buffered log records are processed.
        # print('queue_listener.stop(): Calling...')
        queue_listener.stop()  # shut down the listener thread.
        # print('queue_listener.stop(): Returned')
    except Exception as e:
        print(f'Ignoring Exception: {e}')


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
    
    Strength:  This implementation uses asynchronous handling of log 
        records.  It uses QueueHandler/QueueListener and queue.Queue to
        let the HTTPHandler do its work on a separate thread.

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

    # Typically, this is connects the logger to the handler.
    #     # Add the handler to the logger
    #     central_logger.addHandler(http_handler)
    #     # Milestone -- logrecord handling is configured.
    #
    # But for this logger, we want non-blocking logging, where log 
    # records are queued and processed asynchronously.
    # So configure the logger to handle logrecords by putting them into
    # a queue and moving on.  Use a QueueListener running in a separate
    # thread to monitor the queue, retrieve LogRecord objects, and hand
    # them off to the downstream handler (http_handler).

    # Create a Queue obj.  This queue will store the LogRecord objects.
    logrecord_queue = queue.Queue(-1)  # -1 for an unbounded queue

    # Create a QueueHandler obj.  Its sole purpose is to place LogRecord 
    # objects onto the Queue obj (logrecord_queue).
    queue_handler = logging.handlers.QueueHandler(logrecord_queue)

    # Attach the QueueHandler obj to the intended Logger obj.
    central_logger.addHandler(queue_handler)

    # Create and Start a QueueListener obj.  This listener runs in a 
    # separate thread, continuously monitors the logrecord_queue, and 
    # dispatches the retrieved LogRecord objects to the configured 
    # downstream handlers (http_handler).
    queue_listener = logging.handlers.QueueListener(logrecord_queue, 
        http_handler)
    queue_listener.start()  # Start the listener thread

    atexit.register(cleanup, queue_listener)

    # Milestone -- logrecord handling is configured.

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
