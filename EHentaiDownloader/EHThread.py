__author__ = 'kz'

__all__ = ['ImageDownloader', 'PageNavigator', 'ThreadTerminatedException']

import time
import threading
from EHentaiDownloader import Html, Http, Environment


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


class PageNavigator(threading.Thread):
    """
    Class which represents collecting direct links to images
    """
    FETCH_SLEEP_INTERVAL = 1
    FETCH_SLEEP_INTERVAL_LONG = 5
    FETCH_RETRY_COUNT = 3

    def __init__(self, queue, baseUri, destination):
        """
        Initialize thread
        """
        super().__init__(name='PageNavigator')
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
        firstIteration = True
        pageNumber = 1
        try:
            while self._subpages:
                subpage = self._subpages.pop(0)
                fetchFields = ('pages', 'subpages') if firstIteration else ('pages',)
                result = self._fetchContent(subpage, fetchFields)
                if firstIteration:
                    self._subpages = result['subpages']
                self._pages += result['pages']
                while self._pages:
                    page = self._pages.pop(0)
                    image = self._fetchContent(page, ('image',))['image']
                    image['number'] = pageNumber
                    image['destination'] = self._destination
                    self._queue.put(image)
                    pageNumber += 1
                    print('Parsed page {0}'.format(pageNumber - 1))
                firstIteration = False
            self._queue.join()
        except ThreadTerminatedException:
            pass
        except BaseException as e:
            error = Environment.ErrorInfo(self._name, e)
            Environment.Environment().setError(error)

    def stop(self):
        """
        Set flag to stop thread as soon as possible
        """
        self._stopped = True

    def _fetchContent(self, uri, fields):
        """
        Download a page and parse out all needed content
        """
        if self._stopped:
            raise ThreadTerminatedException
        try:
            if not self._slept:
                time.sleep(self.FETCH_SLEEP_INTERVAL)
            result = {}
            self._parser.content = self._httpClient.get(uri)
            for field in fields:
                result[field] = self._parser[field]
            self._slept = False
            self._retried = 0
            return result
        except Html.TemporaryBanException as e:
            print(str(e))
            time.sleep(self.FETCH_SLEEP_INTERVAL_LONG)
            self._slept = True
        except Html.EHTMLParserException as e:
            # TODO: Logging class ore something like that
            self._retried += 1
            print('%s, retry #%d' % (str(e), self._retried))
            if self._retried == self.FETCH_RETRY_COUNT:
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
        self._number = number  # Debug only
        super().__init__(name='ImageDownloader-%s' % number)
        self._queue = queue

    def run(self):
        """
        Download images from queue
        """
        while True:
            try:
                imageInfo = self._queue.get()
                print('Thread {0} downloads page #{1}'.format(self._name, imageInfo['number']))
                print(imageInfo['uri'])
                httpClient = Http.Client(imageInfo['host'], imageInfo['port'])
                file = open(imageInfo['destination'] + str(imageInfo['number']), 'wb')
                # image = httpClient.getRaw(imageInfo['uri'])
                try:
                    httpClient.sendRequest(imageInfo['uri'])
                    while True:
                        file.write(httpClient.getChunk())
                except Http.ReadResponseException:
                    pass
                # file.write(image)
                httpClient.close()
                file.close()
                self._queue.task_done()
            except BaseException as e:
                error = Environment.ErrorInfo(self._name, e)
                Environment.Environment().setError(error)
                break
