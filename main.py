#!/usr/bin/env python3
# -*- coding: UTF-8

__author__ = 'kz'

import sys
import queue
from EHentaiDownloader import Environment, EHThread


def main():
    """
    Main routine

    """
    try:
        app = Environment.Application()  # Initialize environment
        app.init()
        imagesQueue = queue.Queue()
        # TODO: Move threads initialization in some Environment.Application() method
        for i in range(app['threads']):
            downloader = EHThread.ImageDownloader(imagesQueue, i)
            downloader.daemon = True
            downloader.start()
        NavigatorThread = EHThread.PageNavigator(imagesQueue, app['uri'], app['destination'])
        NavigatorThread.start()
        while True:
            try:
                error = Environment.Application().error
            except queue.Empty:
                pass
            else:
                NavigatorThread.stop()
                NavigatorThread.join()
                raise EHThread.CommonException('Error in thread %s: %s' % (error.thread, str(error.exception)))
    except KeyboardInterrupt:
        print('Terminated')
        pass
    except BaseException as e:
        print(str(e), file=sys.stderr)
        exit(1)


if __name__ == '__main__':
    main()
