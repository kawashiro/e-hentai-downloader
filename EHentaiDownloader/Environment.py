# -*- coding: UTF-8

__author__ = 'kz'

import sys
import subprocess
import queue
import argparse
from EHentaiDownloader import EHThread, Http

LOG_LEVEL_NONE = 0
LOG_LEVEL_ERR = 1
LOG_LEVEL_WARN = 2
LOG_LEVEL_INFO = 3
LOG_LEVEL_DEBUG = 4


def singleton(cls):
    """
    Singleton decorator
    :param cls: class - class to decorate
    """
    instances = {}

    def getInstance():
        """
        Get singleton's instance
        :return: object - instance of decorated class
        """
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]
    return getInstance


class InvalidArgumentException(Exception):
    """
    Exception on wrong input parameters
    """
    pass


@singleton
class Application:
    """
    Main application instance
    """
    def __init__(self):
        """
        Init environment variables
        Should be called from main thread only!
        """
        self._version = '0.1'
        self._storage = {}
        self._completed = False
        self._errorQueue = queue.Queue()

    def init(self):
        """
        Filling environment variables, parsing command line arguments
        """
        # FIXME: Fails on shindoshs
        parser = argparse.ArgumentParser(description='E-Hentai gallery downloader', version=self.version)
        parser.add_argument('url',
                            metavar='link',
                            help='Link to gallery main page'),
        parser.add_argument('destination',
                            metavar='save_path',
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
        parser.add_argument('-l', '--log-level',
                            metavar='level',
                            help='none, err, warn, info, debug',
                            default='info')
        args = parser.parse_args()
        try:
            self._storage = {
                'user_agent':  args.user_agent,
                'threads':     args.threads,
                'uri':         self._defineUri(args.url),
                'destination': args.destination,
                'log_level':   self._defineLogLevel(args.log_level),
                'retries':     args.retries,
                'full_uri':    args.url
            }
        except ValueError:
            parser.print_usage()
            raise InvalidArgumentException

    def _defineLogLevel(self, val):
        """
        Get log level from input string
        :return: int - log level
        """
        return ['none', 'err', 'warn', 'info', 'debug'].index(val.lower())

    def _defineUri(self, uri):
        """
        Cut host from uri
        :param uri: string - input uri
        :return: string - uri without host name and scheme
        """
        host = Http.HTTP_SCHEME + Http.E_HENTAI_GALLERY_HOST
        if uri.find(host) == -1:
            raise ValueError
        return uri.replace(host, '')

    def run(self):
        """
        Run application
        """
        Log('Source:      %s' % self['full_uri'], LOG_LEVEL_INFO)
        Log('Destination: %s' % self['destination'], LOG_LEVEL_INFO)
        Log('Fetching gallery info...', LOG_LEVEL_INFO)
        imagesQueue = queue.Queue()
        for i in range(self['threads']):
            downloader = EHThread.ImageDownloader(imagesQueue, i)
            downloader.daemon = True
            downloader.start()
        navigatorThread = EHThread.PageNavigator(imagesQueue)
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
        # TODO: Make zipping optional or even allow user to select a custom archiver
        # FIXME: Zip "archives" whole directory ierarchy if absolute destination path is specified
        self._zip()
        Log('Completed successfully', LOG_LEVEL_INFO)

    def _zip(self):
        """
        Create zip archive
        """
        zipfile = '%s.zip' % self['destination']
        cmds = [
            ['zip', '-r', zipfile, self['destination']],
            ['rm',  '-r', self['destination']]
        ]
        Log('Creating ZIP-archive: %s' % zipfile, LOG_LEVEL_INFO)
        for cmd in cmds:
            try:
                Log('Eecuting: %s' % ' '.join(cmd), LOG_LEVEL_DEBUG)
                ret = subprocess.check_output(cmd)
            except subprocess.CalledProcessError as e:
                ret = e.output
                raise e
            finally:
                Log('Command returned: %s' % (ret.decode() if ret else '<empty result>'), LOG_LEVEL_DEBUG)

    def __setitem__(self, key, value):
        """
        Set a value to the storage
        :param key:
        :param value:
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
        :param errorInfo: ErrorInfo
        """
        if type(errorInfo) != ErrorInfo:
            raise TypeError('Error info must be type of Environment.ErrorInfo')
        self._errorQueue.put(errorInfo)

    @property
    def error(self):
        """
        Get error queue instance
        :return: ErrorInfo
        """
        return self._errorQueue.get(timeout=0.1)

    @property
    def version(self):
        """
        Get application version
        :return: string - application version
        """
        return self._version

    def complete(self):
        """
        Say application to complete threads management
        """
        self._completed = True


class ErrorInfo:
    """
    Simple error info structure
    """
    def __init__(self, thread, exception):
        """
        Create ErrorInfo object
        :param thread:    string        - thread name
        :param exception: BaseException - raised exception
        """
        self.thread = thread
        self.exception = exception


def Log(message, level, cr=False):
    """
    Print message on stdout
    :param message: string - Message to print
    :param level:   int    - logging level [0..4]
    :param cr:      bool   - use CR instead of LF at the end of line
    """
    try:
        lastEol = Application()['log_last_eol']
    except KeyError:
        lastEol = None
    if (level <= 0) or (Application()['log_level'] < level):
        return
    out = sys.stderr if level == LOG_LEVEL_ERR else sys.stdout
    end = '\r' if cr and Application()['log_level'] == LOG_LEVEL_INFO else '\n'
    if lastEol == '\r' and not cr:
        message = '\n' + message
    print(message, file=out, end=end)
    Application()['log_last_eol'] = end
