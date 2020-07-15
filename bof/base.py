"""Set of global and useful classes and functions used within the module.

:Exceptions: BOF-specific exceptions raised by the module.
:Logging:    Functions to enable or disable logging for the module.
:JSON:       JSON files handling (JSON is used for protocols specification).
"""

import logging
from datetime import datetime
from re import sub

###############################################################################
# BOF EXCEPTIONS                                                              #
###############################################################################

class BOFError(Exception):
    """Base class for all BOF exceptions.

    .. warning:: Should not be used directly, please raise or catch subclasses
                 instead.
    """

class BOFLibraryError(BOFError):
    """Library, files and import-related exceptions.

    Usually raised when the library cannot find what it needs to work correctly
    (such as an external module or a file).
    """ 
    pass

class BOFNetworkError(BOFError):
    """Network-related exceptions.

    Occurs when the network connection fails or is interrupted.
    """
    pass

class BOFProgrammingError(BOFError):
    """Script and module programming-related errors.

    This occurs when a function or an argument is not used as expected.

    .. note:: As a module user, this exception is the one that you may
              encounter the most.
    """ 
    pass

###############################################################################
# BOF LOGGING                                                                 #
###############################################################################

__DEFAULT_FILENAME = "bof"
__LOG_SUFFIX = "log"
__LOG_FORMAT = "%(asctime)s:%(levelname)s:%(message)s:%(filename)s:%(lineno)s"

_LOGGING_ENABLED = False

def enable_logging(filename:str="", error_only:bool=False) -> None:
    """Turn on logging features to store BOF-autogenerated events and user-
    generated events (call to ``bof.log()`` function). Relies on Python's
    ``logging`` module.

    :param filename: Optional name of the file in which events will be saved.
                     Default is ``bof.log``.
    :param error_only: All types of events are logged (info, warning, error)
                       are saved unless this parameter is set to ``True``.    
    """
    level = logging.WARNING if error_only else logging.INFO
    filename = "{0}.{1}".format(filename if filename else __DEFAULT_FILENAME,
                                __LOG_SUFFIX)
    logging.basicConfig(filename=filename, level=level,
                        format=__LOG_FORMAT)
    now = datetime.now().strftime("%y%m%d-%H%M%S")
    logging.info("Starting BOF session {0}".format(now))
    global _LOGGING_ENABLED
    _LOGGING_ENABLED = True

def disable_logging() -> None:
    """Turn off logging features,"""
    global _LOGGING_ENABLED
    _LOGGING_ENABLED = False

def log(message:str, level:str="INFO") -> bool:
    """Logs an event (``message``) to a file, if BOF logging is enabled
    (requires previous call to `bof.`enable_logging()``). A ``message`` is
    recorded along with event-related information:

    - date and time
    - level (can be changed with parameter ``level``)
    - event location in the code (file name, line number)

    :param message: Event definition.
    :param level: Type of event to record: ``ERROR``, ``WARNING``, ``DEBUG``.
                  `INFO`` (default). Levels from Python's ``logging`` are used.
    :returns: Current state of logging (enabled/``True``, disabled/``False``).
    """
    if _LOGGING_ENABLED:
        level = getattr(logging, level.upper())
        if not isinstance(level, int):
            raise BOFProgrammingError("Invalid logging level")
        logging.log(level, message)
    return _LOGGING_ENABLED

###############################################################################
# STRING MANIPULATION                                                         #
###############################################################################

def to_property(value:str) -> str:
    """Replace all non alphanumeric characters in a string with ``_``"""
    return sub('[^0-9a-zA-Z]+', '_', value)
