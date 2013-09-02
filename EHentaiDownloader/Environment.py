__author__ = 'kz'

__all__ = ['Environment']

import sys
import queue
from EHentaiDownloader import singleton


LOG_LEVEL_NONE = 0
LOG_LEVEL_ERR = 1
LOG_LEVEL_WARN = 2
LOG_LEVEL_INFO = 3
LOG_LEVEL_DEBUG = 4


@singleton
class Environment:
    """
    Global environment
    """
    def __init__(self):
        """
        Init environment variables
        Should be called from main thread only!
        """
        self._storage = {}
        self._errorQueue = queue.Queue()

    def __setitem__(self, key, value):
        """
        Set a value to the storage
        """
        self._storage[key] = value

    def __getitem__(self, item):
        """
        Get a value from the storage
        """
        return self._storage[item]

    def setError(self, errorInfo):
        """
        Set thread error to environment
        @param errorInfo
        """
        if type(errorInfo) != ErrorInfo:
            raise TypeError('Error info must be type of Environment.ErrorInfo')
        self._errorQueue.put(errorInfo)

    @property
    def error(self):
        """
        Get error queue instance
        """
        return self._errorQueue.get(timeout=0.1)


class ErrorInfo:
    """
    Simple error info structure
    """
    def __init__(self, thread, exception):
        self.thread = thread
        self.exception = exception


def Log(message, level):
    """
    Print message on stdout
    @param message Message to print
    @param level Logging level [1..4]
    """
    if (level <= 0) or (Environment()['log_level'] > level):
        return
    out = sys.stderr if level == LOG_LEVEL_ERR else sys.stdout
    print(message, file=out)
