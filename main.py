#!/usr/bin/env python3
__author__ = 'kz'

import sys
import queue
from EHentaiDownloader import EHThread, Environment


def main():
    """
    Main routine

    """
    try:
        Environment.Environment()  # Initialize environment
        imagesQueue = queue.Queue()
        for i in range(5):
            downloader = EHThread.ImageDownloader(imagesQueue, i)
            downloader.daemon = True
            downloader.start()
            #NavigatorThread = PageNavigator.PageNavigator(imagesQueue, '/g/623156/fea2d2ec61/', '/home/kz/pyeghd_test/img_')
        NavigatorThread = EHThread.PageNavigator(imagesQueue, '/g/594711/bb126bd78a/', '/home/kz/pyeghd_test/img_')
        NavigatorThread.start()
        while True:
            try:
                error = Environment.Environment().error
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
