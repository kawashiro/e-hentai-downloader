# -*- coding: UTF-8

__author__ = 'kz'

FETCH_SLEEP_INTERVAL = 1
FETCH_SLEEP_INTERVAL_LONG = 5
FETCH_RETRY_COUNT = 3
IMAGE_WORKER_THREADS_COUNT = 5

import time
import threading
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


# TODO: Too much duplicate code in each thread class. Refactor it moving duplicated parts in abstract class
class PageNavigator(threading.Thread):
    """
    Class which represents collecting direct links to images
    """
    def __init__(self, queue, baseUri, destination):
        """
        Initialize thread
        """
        from EHentaiDownloader import Environment
        verbose = (Environment.Application()['log_level'] == Environment.LOG_LEVEL_DEBUG)
        super().__init__(name='PageNavigator', verbose=verbose)
        self._queue = queue
        self._destination = destination
        self._parser = Html.EHTMLParser(baseUri)
        self._httpClient = Http.Client()
        self._subpages = [baseUri]
        self._pages = []
        self._slept = True
        self._stopped = False
        self._retried = 0

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
                fetchFields = ('pages', 'subpages') if firstIteration else ('pages',)
                result = self._fetchContent(subpage, fetchFields)
                if firstIteration:
                    # TODO: Total pages, can be parsed from main page, write other meta info
                    self._subpages = result['subpages']
                    Environment.Log('Found subpages: %s' % repr(self._subpages), Environment.LOG_LEVEL_DEBUG)
                Environment.Log('Found pages: %s' % repr(result['pages']), Environment.LOG_LEVEL_DEBUG)
                self._pages += result['pages']
                while self._pages:
                    page = self._pages.pop(0)
                    Environment.Log('Fetching page #%d; URI %s' % (pageNumber, page), Environment.LOG_LEVEL_DEBUG)
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
            Environment.Application().setError(error)
        finally:
            Environment.Application().complete()

    def stop(self):
        """
        Set flag to stop thread as soon as possible
        """
        self._stopped = True

    def _fetchContent(self, uri, fields):
        """
        Download a page and parse out all needed content
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
        except Html.TemporaryBanException as e:
            print(str(e))
            Environment.Log(
                'Temporary ban ocured, sleeping %f seconds before the next request' % FETCH_SLEEP_INTERVAL_LONG,
                Environment.LOG_LEVEL_WARN
            )
            time.sleep(FETCH_SLEEP_INTERVAL_LONG)
            self._slept = True
        except Html.EHTMLParserException as e:
            self._retried += 1
            self._slept = False
            Environment.Log('%s, retry #%d' % (str(e), self._retried), Environment.LOG_LEVEL_WARN)
            if self._retried == Environment.Application()['retries']:
                raise e
        return self._fetchContent(uri, fields)


class ImageDownloader(threading.Thread):
    """
    Image downloader thread
    """
    def __init__(self, queue, number=0):
        """
        Initialize image download worker thread
        """
        from EHentaiDownloader import Environment
        verbose = (Environment.Application()['log_level'] == Environment.LOG_LEVEL_DEBUG)
        super().__init__(name='ImageDownloader-%s' % number, verbose=verbose)
        self._queue = queue

    def run(self):
        """
        Download images from queue
        """
        from EHentaiDownloader import Environment
        while True:
            try:
                imageInfo = self._queue.get()
                Environment.Log('Downloading image #%d' % imageInfo['number'], Environment.LOG_LEVEL_INFO)
                Environment.Log('from: %s; to: %s' % (imageInfo['full_uri'], imageInfo['destination']),
                                Environment.LOG_LEVEL_DEBUG)
                httpClient = Http.Client(imageInfo['host'], imageInfo['port'])
                file = open(imageInfo['destination'] + str(imageInfo['number']), 'wb')
                try:
                    httpClient.sendRequest(imageInfo['uri'])
                    while True:
                        file.write(httpClient.getChunk())
                except Http.ReadResponseException:
                    pass
                httpClient.close()
                file.close()
                self._queue.task_done()
            except BaseException as e:
                # TODO: Retries as in PageNavigator()
                error = Environment.ErrorInfo(self._name, e)
                Environment.Application().setError(error)
                break
