# -*- coding: UTF-8

__author__ = 'kz'

FETCH_SLEEP_INTERVAL = 1
FETCH_SLEEP_INTERVAL_LONG = 5
FETCH_RETRY_COUNT = 3
IMAGE_WORKER_THREADS_COUNT = 5

import time
import threading
import os
from EHentaiDownloader import Html, Http


class CommonException(Exception):
    """
    Common EHThread exception
    """
    pass


class ThreadTerminatedException(CommonException):
    """
    Tread is terminated simultaneously
    """
    pass


class AbstractEHThread(threading.Thread):
    """
    Abstract class with some common crap
    """
    def __init__(self, queue, name):
        """
        Initialize thread
        :param queue: queue.Queue - images queue
        :param name:  string      - thread unique name
        """
        from EHentaiDownloader import Environment
        self._app = Environment.Application()
        verbose = (self._app['log_level'] == Environment.LOG_LEVEL_DEBUG)
        super().__init__(name=name, verbose=verbose)
        self._queue = queue
        self._slept = True
        self._stopped = False
        self._retried = 0


class PageNavigator(AbstractEHThread):
    """
    Class which represents collecting direct links to images
    """
    def __init__(self, queue):
        """
        Initialize thread
        :param queue: queue.Queue - images queue
        """
        super().__init__(queue, 'PageNavigator')
        self._destination = self._app['destination']
        self._subpages = [self._app['uri']]
        self._parser = Html.EHTMLParser(self._app['uri'])
        self._httpClient = Http.Client()
        self._pages = []

    def run(self):
        """
        Run thread
        """
        from EHentaiDownloader import Environment
        firstIteration = True
        pageNumber = 1
        try:
            while self._subpages:
                subpage = self._subpages.pop(0)
                Environment.Log('Fetching subpage %s' % subpage, Environment.LOG_LEVEL_DEBUG)
                fetchFields = ('pages', 'subpages', 'meta') if firstIteration else ('pages',)
                result = self._fetchContent(subpage, fetchFields)
                if firstIteration:
                    meta = result['meta']
                    Environment.Log('Title: {0[main]} / {0[jap]}'.format(meta['title']), Environment.LOG_LEVEL_INFO)
                    for k in meta['additional'].keys():
                        Environment.Log('{0:.<20}...{1}'.format(k, meta['additional'][k]), Environment.LOG_LEVEL_INFO)
                    self._subpages = result['subpages']
                    self._destination = '/'.join((self._destination.rstrip('/'), meta['title']['main']))
                    os.mkdir(self._destination)
                    self._app['destination'] = self._destination
                    self._app['total_images'] = meta['count']
                    Environment.Log('Found subpages: %s' % repr(self._subpages), Environment.LOG_LEVEL_DEBUG)
                Environment.Log('Found pages: %s' % repr(result['pages']), Environment.LOG_LEVEL_DEBUG)
                self._pages += result['pages']
                while self._pages:
                    page = self._pages.pop(0)
                    Environment.Log('Fetching page # %d; URI %s' % (pageNumber, page), Environment.LOG_LEVEL_DEBUG)
                    image = self._fetchContent(page, ('image',))['image']
                    Environment.Log('Found image %s, adding to queue' % image, Environment.LOG_LEVEL_DEBUG)
                    image['number'] = pageNumber
                    image['destination'] = self._destination
                    self._queue.put(image)
                    pageNumber += 1
                firstIteration = False
            self._queue.join()
        except ThreadTerminatedException:
            pass
        except BaseException as e:
            error = Environment.ErrorInfo(self._name, e)
            self._app.setError(error)
        finally:
            self._app.complete()

    def stop(self):
        """
        Set flag to stop thread as soon as possible
        """
        self._stopped = True

    def _fetchContent(self, uri, fields):
        """
        Download a page and parse out all needed content
        :param uri:    string - uri to fetch content from
        :param fields: tuple  - tuple of fields to fetch labels
        :return:       dict   - dictionary with parsed values
        """
        from EHentaiDownloader import Environment
        if self._stopped:
            raise ThreadTerminatedException
        try:
            if not self._slept:
                Environment.Log('Sleeping %f seconds before the next request' % FETCH_SLEEP_INTERVAL,
                                Environment.LOG_LEVEL_DEBUG)
                time.sleep(FETCH_SLEEP_INTERVAL)
            result = {}
            self._parser.content = self._httpClient.get(uri)
            for field in fields:
                result[field] = self._parser[field]
            self._slept = False
            self._retried = 0
            return result
        except Html.TemporaryBanException:
            Environment.Log(
                'Temporary ban ocured, sleeping %f seconds before the next request' % FETCH_SLEEP_INTERVAL_LONG,
                Environment.LOG_LEVEL_WARN
            )
            time.sleep(FETCH_SLEEP_INTERVAL_LONG)
            self._slept = True
        except Html.EHTMLParserException as e:
            self._retried += 1
            self._slept = False
            Environment.Log('%s, retry # %d' % (str(e), self._retried), Environment.LOG_LEVEL_WARN)
            if self._retried == self._app['retries']:
                raise e
        return self._fetchContent(uri, fields)


class ImageDownloader(AbstractEHThread):
    """
    Image downloader thread
    """
    def __init__(self, queue, number=0):
        """
        Initialize image download worker thread
        :param queue:  queue.Queue - images queue
        :param number: int         - worker thread unique id
        """
        super().__init__(queue, 'ImageDownloader-%s' % number)

    def run(self):
        """
        Download images from queue
        """
        from EHentaiDownloader.Environment import ErrorInfo
        while True:
            try:
                self._performTask()
            except BaseException as e:
                self._retried += 1
                if self._retried == self._app['retries']:
                    error = ErrorInfo(self._name, e)
                    self._app.setError(error)
                    break
                self._performTask()

    def _performTask(self):
        """
        Get and perform a single task
        """
        from EHentaiDownloader import Environment
        imageInfo = self._queue.get()
        totalImages = self._app['total_images']
        Environment.Log('Downloading image #%d/%d' % (imageInfo['number'], totalImages),
                        Environment.LOG_LEVEL_INFO, True)
        Environment.Log('from: %s; to: %s' % (imageInfo['full_uri'], imageInfo['destination']),
                        Environment.LOG_LEVEL_DEBUG)
        httpClient = Http.Client(imageInfo['host'], imageInfo['port'])
        httpClient.sendRequest(imageInfo['uri'])
        contentType = httpClient.getHeader('Content-type')
        extension = self._getExtensionFromContentType(contentType)
        fileName = '{image[destination]}/{image[number]:0={padding}}.{ext}'.format(
            image=imageInfo, ext=extension, padding=str(totalImages).__len__())
        file = open(fileName, 'wb')
        try:
            while True:
                file.write(httpClient.getChunk())
        except Http.ReadResponseException:
            pass
        file.close()
        httpClient.close()
        self._retried = 0
        self._queue.task_done()

    def _getExtensionFromContentType(self, contentType):
        """
        Try to get file extension according to content-type
        This crap is some kind of suitable for images only,
        but we don't need anything more
        :return: string - corresponding file extension
        """
        return contentType.split('/')[1].lower().replace('jpeg', 'jpg')
