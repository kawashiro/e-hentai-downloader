__author__ = 'kz'

__all__ = ['Environment']

import queue
from EHentaiDownloader import singleton


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