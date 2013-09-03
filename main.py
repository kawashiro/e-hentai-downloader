#!/usr/bin/env python3
# -*- coding: UTF-8

__author__ = 'kz'

from EHentaiDownloader import Environment

if __name__ == '__main__':
    try:
        app = Environment.Application()
        app.init()
        app.run()
    except KeyboardInterrupt:
        Environment.Log('Terminated', Environment.LOG_LEVEL_WARN)
        pass
    except BaseException as e:
        Environment.Log(str(e), Environment.LOG_LEVEL_ERR)
        exit(1)
