# -*- coding: UTF-8

__author__ = 'kz'

import sys
import queue
import argparse
from EHentaiDownloader import EHThread, Http

LOG_LEVEL_NONE = 0
LOG_LEVEL_ERR = 1
LOG_LEVEL_WARN = 2
LOG_LEVEL_INTERACTIVE = 3
LOG_LEVEL_INFO = 4
LOG_LEVEL_DEBUG = 5


def singleton(cls):
    """
    Singleton decorator
    @param cls
    """
    instances = {}

    def getInstance():
        """
        Get singleton's instance
        """
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]
    return getInstance


@singleton
class Application:
    """
    Global environment
    """
    def __init__(self):
        """
        Init environment variables
        Should be called from main thread only!
        """
        self._version = '0.01'
        self._storage = {}
        self._completed = False
        self._errorQueue = queue.Queue()

    def init(self):
        """
        Filling environment
        """
        parser = argparse.ArgumentParser(description='E-Hentai gallery downloader', version=self.version)
        parser.add_argument('url',
                            metavar='link',
                            help='Link to gallery main page'),
        parser.add_argument('destination',
                            metavar='path',
                            help='Path to save downloaded gallery to'),
        parser.add_argument('-a', '--user-agent',
                            metavar='User agent',
                            help='Specify new fake user agent',
                            default=Http.USER_AGENT),
        parser.add_argument('-t', '--threads', type=int,
                            metavar='count',
                            help='Images download worker threads count, default 5',
                            default=EHThread.IMAGE_WORKER_THREADS_COUNT)
        parser.add_argument('-r', '--retries', type=int,
                            metavar='count',
                            help='Retries count on download fail, default 3',
                            default=EHThread.FETCH_RETRY_COUNT)
        parser.add_argument('-l', '--log-level', type=int,
                            metavar='0..4',
                            help='0 - quiet, 1 - fatal errors only,\
                                  2 - warnings, 3 - info messages, 4 - debug',
                            default=LOG_LEVEL_INTERACTIVE)
        args = parser.parse_args()
        self._storage = {
            'user_agent':  args.user_agent,
            'threads':     args.threads,
            'uri':         args.url.replace('http://g.e-hentai.org', ''),  # TODO: Constants
            'destination': args.destination,
            'log_level':   args.log_level,
            'retries':     args.retries
        }

    def run(self):
        """
        Run application
        """
        imagesQueue = queue.Queue()
        for i in range(self['threads']):
            downloader = EHThread.ImageDownloader(imagesQueue, i)
            downloader.daemon = True
            downloader.start()
        navigatorThread = EHThread.PageNavigator(imagesQueue, self['uri'], self['destination'])
        navigatorThread.daemon = True
        navigatorThread.start()
        while not self._completed:
            try:
                error = self.error
            except queue.Empty:
                pass
            else:
                navigatorThread.stop()
                navigatorThread.join()
                raise EHThread.CommonException('Error in thread %s: %s' % (error.thread, str(error.exception)))

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

    @property
    def version(self):
        """
        Get application version
        """
        return self._version

    def complete(self):
        """
        Mark a thread as completed
        """
        self._completed = True


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
    if (level <= 0) or (Application()['log_level'] < level):
        return
    if (level == LOG_LEVEL_INTERACTIVE) and (Application()['log_level'] != level):
        return
    out = sys.stderr if level == LOG_LEVEL_ERR else sys.stdout
    print(message, file=out)
