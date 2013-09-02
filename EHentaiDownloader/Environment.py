# -*- coding: UTF-8

__author__ = 'kz'

__all__ = ['Environment']

import sys
import queue
import argparse
from EHentaiDownloader import singleton

LOG_LEVEL_NONE = 0
LOG_LEVEL_ERR = 1
LOG_LEVEL_WARN = 2
LOG_LEVEL_INFO = 3
LOG_LEVEL_DEBUG = 4


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
        self._errorQueue = queue.Queue()

    def init(self):
        """
        Filling environment
        """
        from EHentaiDownloader import Http, EHThread
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
        # parser.add_argument('-s', '--sleep', type=int,
        #                     metavar='seconds',
        #                     help='Sleep between each request to e-hentai gallery, default 1 sec.',
        #                     default=EHThread.FETCH_SLEEP_INTERVAL)
        # parser.add_argument('-b', '--ban-sleep', type=int,
        #                     help='Sleep interval if temporary ban detected, default 5 sec.',
        #                     metavar='seconds',
        #                     default=EHThread.FETCH_SLEEP_INTERVAL_LONG)
        parser.add_argument('-t', '--threads', type=int,
                            metavar='count',
                            help='Images download worker threads count, default 5',
                            default=EHThread.IMAGE_WORKER_THREADS_COUNT)
        parser.add_argument('-l', '--log-level', type=int,
                            metavar='0..4',
                            help='0 - quiet, 1 - fatal errors only,\
                                  2 - warnings, 3 - info messages, 4 - debug',
                            default=LOG_LEVEL_INFO)
        args = parser.parse_args()
        self._storage = {
            'user_agent':  args.user_agent,
            # 'short_sleep': args.sleep,
            # 'long_sleep':  args.ban_sleep,
            'threads':     args.threads,
            'uri':         args.url.replace('http://g.e-hentai.org', ''),  # TODO: Constants
            'destination': args.destination,
            'log_level':   args.log_level
        }

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
    if (level <= 0) or (Application()['log_level'] > level):
        return
    out = sys.stderr if level == LOG_LEVEL_ERR else sys.stdout
    print(message, file=out)
